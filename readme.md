 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index 6ac64a9126f0528c9b04ccefd4fcd2b6918e6eb8..bc0e02e40279983fcf8fb74aad1e30b5e0e51bff 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,57 @@
-# Ccidd
\ No newline at end of file
+# LLM Bulk Analyzer – anti-bot resilient DOM/Markdown extraction
+
+This repository now contains a practical extraction pipeline for pages that block simple HTTP clients.
+
+## What this solves
+
+If your URLs are being blocked by bot protection, the fix is usually:
+
+1. **Use a real browser context** (Playwright) for pages with JS/bot checks.
+2. **Fallback fetchers** (requests/cloudscraper) for simple pages.
+3. **Normalize output** into:
+   - raw HTML
+   - cleaned DOM text
+   - markdown for LLM ingestion
+
+## Quick start
+
+```bash
+python -m venv .venv
+source .venv/bin/activate
+pip install requests beautifulsoup4 markdownify readability-lxml trafilatura playwright cloudscraper
+playwright install chromium
+python llm_bulk_analyzer/fetch_pipeline.py https://example.com
+```
+
+## Notes on site protection
+
+- Respect robots, Terms of Service, and legal constraints.
+- Use rate limiting and retries.
+- Some enterprise anti-bot systems may require authenticated sessions and cannot be bypassed reliably without owner authorization.
+
+## Output shape
+
+The script prints JSON with:
+
+- `status`: `ok` or `error`
+- `url`
+- `method_used`: `requests`, `cloudscraper`, or `playwright`
+- `title`
+- `raw_html`
+- `clean_text`
+- `markdown`
+
+This is suitable for downstream LLM-readiness scoring.
+
+## Chrome extension mode (for protected pages)
+
+Yes — you can now load this as an unpacked Chrome extension and extract the **already-rendered DOM** from the current tab.
+
+1. Open `chrome://extensions`
+2. Enable **Developer mode**
+3. Click **Load unpacked**
+4. Select the `chrome-extension/` folder from this repo
+5. Open any page, click the extension icon, and click **Extract Current Tab**
+6. Optionally click **Download JSON**
+
+This avoids many server-side bot protections because extraction runs inside your active browser tab after page render.
 
EOF
)
