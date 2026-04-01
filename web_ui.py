"""
Simple web UI for Downloads organizer.

Run:
    python3 web_ui.py

Open:
    http://127.0.0.1:8080
"""

from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

import organize_downloadsv3 as organizer

HOST = "127.0.0.1"
PORT = 8080
DEFAULT_TARGET = organizer.DEFAULT_DOWNLOADS_PATH


def _safe_target(raw_path: str | None) -> Path:
    """Resolve user-provided path safely."""
    if raw_path and raw_path.strip():
        return Path(raw_path).expanduser().resolve()
    return DEFAULT_TARGET


def _recent_runs(limit: int = 8) -> list[dict]:
    """Return recent runs from project history file."""
    paths = organizer._paths(DEFAULT_TARGET)
    organizer._ensure_runtime_dirs(paths)
    runs = organizer._load_runs(paths["runs_file"])
    return list(reversed(runs[-limit:]))


def _counts(records: list[dict]) -> tuple[int, int, int, int]:
    moved = sum(1 for record in records if record.get("status") == "moved")
    preview = sum(1 for record in records if record.get("status") == "would_move")
    skipped = sum(1 for record in records if str(record.get("status", "")).startswith("skipped"))
    errors = sum(1 for record in records if str(record.get("status", "")).startswith("error"))
    return moved, preview, skipped, errors


def _render_page(message: str = "", message_type: str = "info", selected_path: Path | None = None) -> str:
    """Render dashboard HTML."""
    target = selected_path or DEFAULT_TARGET
    runs = _recent_runs()
    latest = runs[0] if runs else None

    latest_rows = ""
    if latest:
        for record in latest.get("records", [])[:25]:
            latest_rows += (
                "<tr>"
                f"<td>{html.escape(record.get('file_name', ''))}</td>"
                f"<td>{html.escape(record.get('category', ''))}</td>"
                f"<td>{html.escape(record.get('status', ''))}</td>"
                f"<td><code>{html.escape(record.get('moved_path', ''))}</code></td>"
                "</tr>"
            )

    run_rows = ""
    for run in runs:
        moved, preview, skipped, errors = _counts(run.get("records", []))
        run_rows += (
            "<tr>"
            f"<td>{html.escape(run.get('run_id', ''))}</td>"
            f"<td>{html.escape(run.get('started_at', ''))}</td>"
            f"<td>{html.escape(run.get('downloads_path', ''))}</td>"
            f"<td>{moved}</td>"
            f"<td>{preview}</td>"
            f"<td>{skipped}</td>"
            f"<td>{errors}</td>"
            "</tr>"
        )

    color = "#2563eb" if message_type == "info" else "#b45309"
    if message_type == "error":
        color = "#b91c1c"

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Downloads Organizer Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #111827; }}
    .card {{ background: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; margin-bottom: 16px; }}
    h1 {{ margin: 0 0 12px 0; }}
    input[type="text"] {{ width: 600px; max-width: 95%; padding: 8px; }}
    button {{ padding: 8px 12px; margin-right: 8px; margin-top: 8px; cursor: pointer; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 8px; font-size: 13px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    .msg {{ color: {color}; font-weight: 600; margin-top: 8px; }}
    code {{ font-size: 12px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Downloads Organizer</h1>
    <form method="post" action="/action">
      <label><strong>Target folder</strong></label><br />
      <input type="text" name="target_path" value="{html.escape(str(target))}" />
      <br />
      <button type="submit" name="action" value="run">Run (with backup)</button>
      <button type="submit" name="action" value="dry_run">Dry Run Preview</button>
      <button type="submit" name="action" value="run_no_backup">Run (no backup)</button>
      <button type="submit" name="action" value="undo">Undo Last Run</button>
    </form>
    <div class="msg">{html.escape(message)}</div>
    <div style="margin-top:8px;">History file: <code>{html.escape(str(organizer.PROJECT_DATA_DIR / "runs_history.json"))}</code></div>
  </div>

  <div class="card">
    <h2>Recent Runs</h2>
    <table>
      <thead>
        <tr><th>Run ID</th><th>Started</th><th>Target Path</th><th>Moved</th><th>Preview</th><th>Skipped</th><th>Errors</th></tr>
      </thead>
      <tbody>
        {run_rows or '<tr><td colspan="7">No runs yet.</td></tr>'}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Latest Run Details (first 25 files)</h2>
    <table>
      <thead>
        <tr><th>File</th><th>Category</th><th>Status</th><th>Destination</th></tr>
      </thead>
      <tbody>
        {latest_rows or '<tr><td colspan="4">No run details available.</td></tr>'}
      </tbody>
    </table>
  </div>
</body>
</html>"""


class OrganizerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        message = query.get("msg", [""])[0]
        message_type = query.get("type", ["info"])[0]
        selected = query.get("target", [""])[0]
        page = _render_page(message=message, message_type=message_type, selected_path=_safe_target(selected))
        self._send_html(page)

    def do_POST(self) -> None:
        if self.path != "/action":
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(content_length).decode("utf-8")
        form = parse_qs(payload)
        action = form.get("action", [""])[0]
        target = _safe_target(form.get("target_path", [""])[0])

        try:
            if action == "run":
                result = organizer.organize_downloads(base_dir=target, create_backup=True, dry_run=False)
                moved = sum(1 for record in result["records"] if record["status"] == "moved")
                msg = f"Run {result['run_id']} completed. Moved {moved} file(s)."
            elif action == "dry_run":
                result = organizer.organize_downloads(base_dir=target, create_backup=True, dry_run=True)
                preview = sum(1 for record in result["records"] if record["status"] == "would_move")
                msg = f"Dry run {result['run_id']} complete. Would move {preview} file(s)."
            elif action == "run_no_backup":
                result = organizer.organize_downloads(base_dir=target, create_backup=False, dry_run=False)
                moved = sum(1 for record in result["records"] if record["status"] == "moved")
                msg = f"Run {result['run_id']} completed (no backup). Moved {moved} file(s)."
            elif action == "undo":
                ok = organizer.undo_last_move(base_dir=target)
                msg = "Undo completed." if ok else "No run history found for undo."
            else:
                msg = "Unsupported action."
        except Exception as error:  # pragma: no cover
            self._redirect(
                f"/?msg={quote_plus(str(error))}&type=error&target={quote_plus(str(target))}"
            )
            return

        self._redirect(f"/?msg={quote_plus(msg)}&type=info&target={quote_plus(str(target))}")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_html(self, body: str) -> None:
        content = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), OrganizerHandler)
    print(f"Web UI running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
