# DOA-012: Scraper — honor `Retry-After`, log terminal failures, don't silently save partial index data

- **Type:** Bug (data quality)
- **Priority:** P2
- **Component:** screener_scraper
- **Affected files:** `screener_scraper/utils.py`, `screener_scraper/scrape_indexes.py`

## Problems

1. **`get_page` gives up silently.** `utils.py:16-34` returns `None` after `MAX_RETRIES` with only per-attempt warnings — there is no terminal `ERROR` line saying the URL was abandoned.

2. **429 handling ignores `Retry-After` and burns attempts at a fixed 30 s.** A 429 consumes one of the 3 attempts with a hardcoded wait; screener.in sends `Retry-After`, which should be honored (capped) before falling back to 30 s.

3. **Partial index results are saved as if complete.** `scrape_indexes.py:95-97`: when a page fetch fails mid-pagination, the loop `break`s and the companies collected so far are written to CSV with a normal success summary. A 2-page index that fails on page 2 produces a half-empty `*_companies.csv` that looks fine. Downstream (`scrape_companies.py`) then permanently misses those companies.

## Steps of completion

1. In `get_page`: parse `Retry-After` (seconds form), cap it (e.g. 120 s), fall back to 30 s; add a final `logger.error` before returning `None`.
2. In `scrape_index`: track a `failed` flag when a page fetch returns `None`; return it alongside the companies.
3. In `main`: mark such indexes as `PARTIAL/FAILED` in the summary and **skip writing the CSV** (or write it with a `.partial` suffix — pick one; diff below skips and reports).
4. Test: point one index at a bogus slug and verify the run ends with a clear failure line and no misleading CSV.

## Changes (diff)

### `screener_scraper/utils.py`

```diff
@@ -16,19 +16,26 @@
 def get_page(url: str) -> BeautifulSoup | None:
     """Fetch a page and return BeautifulSoup object with exponential backoff."""
     for attempt in range(MAX_RETRIES):
         try:
             response = session.get(url, timeout=REQUEST_TIMEOUT)
             # Handle rate limiting (429)
             if response.status_code == 429:
-                wait = 30  # Wait 30s on rate limit
+                retry_after = response.headers.get("Retry-After", "")
+                wait = min(int(retry_after), 120) if retry_after.isdigit() else 30
                 logger.warning("Rate limited (429) — waiting %ds", wait)
                 time.sleep(wait)
                 continue
             response.raise_for_status()
             return BeautifulSoup(response.text, "html.parser")
         except requests.RequestException as e:
             wait = REQUEST_DELAY * (2 ** attempt)  # 1.5, 3, 6, 12...
             logger.warning("Attempt %d failed: %s — retrying in %.1fs", attempt + 1, e, wait)
             if attempt < MAX_RETRIES - 1:
                 time.sleep(wait)
+    logger.error("Giving up on %s after %d attempts", url, MAX_RETRIES)
     return None
```

### `screener_scraper/scrape_indexes.py`

```diff
@@ -75,12 +75,13 @@
-def scrape_index(index_name: str, index_slug: str) -> list[dict]:
+def scrape_index(index_name: str, index_slug: str) -> tuple[list[dict], bool]:
     """Scrape all companies from an index, handling pagination.
+
+    Returns (companies, complete). `complete` is False when any page failed.
     """
     logger.info("=" * 60)
     logger.info("Scraping index: %s", index_name)
     logger.info("=" * 60)

     all_companies = []
     page = 1
     total_pages = None
+    complete = True

     while True:
@@ -93,7 +94,8 @@
         soup = get_page(url)

         if not soup:
             logger.error("  FAILED to fetch page %d", page)
+            complete = False
             break
@@ -114,8 +116,8 @@
         time.sleep(REQUEST_DELAY)

     logger.info("  Total companies scraped: %d", len(all_companies))
-    return all_companies
+    return all_companies, complete
@@ -163,12 +165,17 @@
     results = {}
+    failed = []
     for index_name, index_slug in indexes.items():
-        companies = scrape_index(index_name, index_slug)
-        if companies:
+        companies, complete = scrape_index(index_name, index_slug)
+        if not complete:
+            logger.error("  %s: INCOMPLETE (%d companies fetched) — not saving CSV",
+                         index_name, len(companies))
+            failed.append(index_name)
+        elif companies:
             filepath = save_to_csv(companies, index_name)
             results[index_name] = {
                 "count": len(companies),
                 "file": filepath,
             }

     # Summary
     logger.info("=" * 60)
     logger.info("SCRAPE COMPLETE")
     logger.info("=" * 60)
     for index_name, info in results.items():
         logger.info("  %s: %d companies -> %s", index_name, info["count"], info["file"])
+    for index_name in failed:
+        logger.error("  %s: FAILED — rerun this index", index_name)
+
+    if failed:
+        sys.exit(1)

     return results
```

> `sys` is already imported at `scrape_indexes.py:9`. Exiting non-zero lets `run.sh` / cron detect partial runs.

## Acceptance criteria

- [ ] A failing index produces `FAILED — rerun this index`, no CSV, and exit code 1.
- [ ] A 429 with `Retry-After: 7` waits ~7 s, not 30 s.
- [ ] Successful runs are byte-identical to before (same CSVs, exit 0).
