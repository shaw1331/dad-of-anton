from __future__ import annotations

from app.screener_query.tasks import QueryScreenerTask
from app.workflow.base_workflow_config import BaseWorkflowConfig, InputField
from app.workflow.workflow_orchestrator_v1.workflow_registry import WORKFLOWS

SCREENER_QUERY_WORKFLOW = BaseWorkflowConfig(
    name="screener_query",
    description="Finds stocks matching a screener query or index name",
    input_fields=[
        InputField(
            name="query",
            type="str",
            label="Screener Query",
            description="Index name or query to search for (e.g. NIFTY50, SMALLCAP50)",
            required=True,
        ),
    ],
    tasks=[QueryScreenerTask],
)

WORKFLOWS["screener_query"] = SCREENER_QUERY_WORKFLOW
