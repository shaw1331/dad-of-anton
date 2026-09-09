from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from pydantic import BaseModel

from app.ai.factory import AgentFactory
from app.stock_jury.models import CandidateVerdict, JuryBallot, JuryChallenge, JuryVerdict
from app.stock_jury.prompts import ballot_prompt, challenge_prompt, chair_prompt
from app.stock_jury.validation import validate_verdict

logger = logging.getLogger(__name__)


class StockJury:
    """Bounded parallel jury with an injectable agent runner for tests."""

    ROLES = ("swing_momentum", "catalyst_news", "downside_risk", "comparative_portfolio")

    def __init__(self, runner: Callable[[type[BaseModel], str, str], Any] | None = None) -> None:
        self.runner = runner or self._default_runner

    @staticmethod
    def _default_runner(model: type[BaseModel], system: str, human: str) -> Any:
        graph = AgentFactory.get("stock_analysis", output_model=model)
        result = graph.run({"stock_data": {}, "system_prompt": system, "analysis_prompt": human})
        if not result.success or result.data is None:
            raise RuntimeError(result.error or "Agent returned no structured output")
        return model.model_validate(result.data)

    @staticmethod
    def _evidence(candidate_reports: list[dict]) -> list[dict]:
        packets: list[dict] = []
        for report in candidate_reports:
            ticker = str(report.get("ticker", "UNKNOWN")).upper()
            packet = {"ticker": ticker, "name": report.get("name", ""), "evidence": []}
            for key, value in report.items():
                if key in {"ticker", "name", "error"} or value in (None, "", [], {}):
                    continue
                packet["evidence"].append({"id": f"REPORT.{key.upper()}", "field": key, "value": value})
            if report.get("error"):
                packet["error"] = report["error"]
            packets.append(packet)
        return packets

    def _run_with_retry(self, model: type[BaseModel], system: str, human: str) -> Any:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                return self.runner(model, system, human)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("Jury agent attempt %d failed: %s", attempt + 1, exc)
        raise RuntimeError(str(last_error))

    def evaluate(self, candidate_reports: list[dict], max_holdings: int = 3, max_allocation_pct: float = 50) -> dict:
        evidence = self._evidence(candidate_reports)
        valid = [packet for packet in evidence if "error" not in packet]
        tickers = {packet["ticker"] for packet in evidence}
        ballots: list[JuryBallot] = []
        failures: list[dict] = []

        def run_ballot(role: str) -> JuryBallot:
            system, human = ballot_prompt(role, valid)
            return self._run_with_retry(JuryBallot, system, human)

        with ThreadPoolExecutor(max_workers=len(self.ROLES)) as pool:
            futures = {pool.submit(run_ballot, role): role for role in self.ROLES}
            for future in as_completed(futures):
                role = futures[future]
                try:
                    ballots.append(future.result())
                except Exception as exc:  # noqa: BLE001
                    failures.append({"agent": role, "error": str(exc)})

        if len(ballots) < 3:
            raise RuntimeError(f"Jury quorum unavailable: {len(ballots)} successful ballots")

        ballot_dicts = [ballot.model_dump(mode="json") for ballot in ballots]
        challenges: list[JuryChallenge] = []

        def run_challenge(kind: str) -> JuryChallenge:
            system, human = challenge_prompt(kind, valid, ballot_dicts)
            return self._run_with_retry(JuryChallenge, system, human)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(run_challenge, kind): kind for kind in ("BULL", "BEAR")}
            for future in as_completed(futures):
                try:
                    challenges.append(future.result())
                except Exception as exc:  # noqa: BLE001
                    failures.append({"agent": futures[future], "error": str(exc)})

        system, human = chair_prompt(valid, ballot_dicts, [item.model_dump(mode="json") for item in challenges])
        verdict = self._run_with_retry(JuryVerdict, system, human)
        rows = {row.ticker.upper(): row for row in verdict.candidates}
        for report in candidate_reports:
            ticker = str(report.get("ticker", "UNKNOWN")).upper()
            if report.get("error") and ticker not in rows:
                rows[ticker] = CandidateVerdict(
                    ticker=ticker,
                    name=str(report.get("name", "")),
                    rating="WATCH",
                    portfolio_status="INSUFFICIENT_DATA",
                    conviction=0,
                    outlook="NEUTRAL",
                    summary="No investment rating was issued because the stock workflow failed.",
                    data_quality_warnings=[str(report["error"])],
                )
        verdict.candidates = list(rows.values())
        verdict.selected = [row for row in verdict.candidates if row.portfolio_status == "SELECTED"]
        verdict.rejected = [row for row in verdict.candidates if row.portfolio_status != "SELECTED"]
        verdict.decision = "ACTIONABLE" if verdict.selected else "NO_ACTION"
        evidence_ids = {item["id"] for packet in valid for item in packet["evidence"]}
        validate_verdict(verdict, tickers, evidence_ids=evidence_ids, max_holdings=max_holdings, max_allocation_pct=max_allocation_pct)
        verdict.jury_audit = {
            "successful_ballots": [ballot.juror for ballot in ballots],
            "challenges": [challenge.challenger for challenge in challenges],
            "failures": failures,
        }
        return verdict.model_dump(mode="json")
