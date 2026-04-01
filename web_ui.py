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


def _run_by_id(run_id: str) -> dict | None:
    """Return a single run by id."""
    if not run_id:
        return None
    for run in _recent_runs(limit=200):
        if run.get("run_id") == run_id:
            return run
    return None


CATEGORY_COLORS: dict[str, str] = {
    "Images": "#8b5cf6",
    "Documents": "#2563eb",
    "Videos": "#db2777",
    "Music": "#059669",
    "Archives": "#d97706",
    "Programs": "#6366f1",
    "Others": "#6b7280",
}

STATUS_COLORS: dict[str, str] = {
    "moved": "#059669",
    "would_move": "#2563eb",
    "undone": "#7c3aed",
    "skipped_destination_exists": "#d97706",
}


def _counts(records: list[dict]) -> tuple[int, int, int, int]:
    moved = sum(1 for r in records if r.get("status") == "moved")
    preview = sum(1 for r in records if r.get("status") == "would_move")
    skipped = sum(1 for r in records if str(r.get("status", "")).startswith("skipped"))
    errors = sum(1 for r in records if str(r.get("status", "")).startswith("error"))
    return moved, preview, skipped, errors


def _badge(text: str, bg: str) -> str:
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;'
        f'font-size:11px;font-weight:600;color:#fff;background:{bg}">'
        f'{html.escape(text)}</span>'
    )


def _status_badge(status: str) -> str:
    bg = STATUS_COLORS.get(status, "#b91c1c" if status.startswith("error") else "#6b7280")
    return _badge(status, bg)


def _category_badge(category: str) -> str:
    bg = CATEGORY_COLORS.get(category, "#6b7280")
    return _badge(category, bg)


def _render_page(
    message: str = "",
    message_type: str = "info",
    selected_path: Path | None = None,
    selected_run_id: str = "",
) -> str:
    """Render dashboard HTML."""
    target = selected_path or DEFAULT_TARGET
    runs = _recent_runs()
    latest = runs[0] if runs else None
    selected_run = _run_by_id(selected_run_id) or latest

    # Summary cards for selected run
    sel_moved, sel_preview, sel_skipped, sel_errors = (0, 0, 0, 0)
    sel_run_label = "No run selected"
    if selected_run:
        sel_moved, sel_preview, sel_skipped, sel_errors = _counts(selected_run.get("records", []))
        sel_run_label = f"Run {selected_run.get('run_id', '')} &mdash; {html.escape(selected_run.get('started_at', ''))}"

    details_rows = ""
    if selected_run:
        for idx, record in enumerate(selected_run.get("records", [])):
            stripe = "background:#f9fafb;" if idx % 2 == 0 else ""
            details_rows += (
                f'<tr style="{stripe}">'
                f"<td style='text-align:center;color:#64748b'>{idx + 1}</td>"
                f"<td style='font-weight:500'>{html.escape(record.get('file_name', ''))}</td>"
                f"<td><code>{html.escape(record.get('original_path', ''))}</code></td>"
                f"<td><code>{html.escape(record.get('moved_path', ''))}</code></td>"
                f"<td>{_category_badge(record.get('category', ''))}</td>"
                f"<td>{_status_badge(record.get('status', ''))}</td>"
                f"<td><code>{html.escape(record.get('backup_path', '') or '-')}</code></td>"
                "</tr>"
            )

    run_rows = ""
    run_options = '<option value="">Latest run</option>'
    for run in runs:
        moved, preview, skipped, errors = _counts(run.get("records", []))
        rid = run.get("run_id", "")
        sel_attr = " selected" if rid == selected_run_id else ""
        run_options += (
            f'<option value="{html.escape(rid)}"{sel_attr}>'
            f'{html.escape(rid)} | {html.escape(run.get("started_at", ""))}'
            f' | {moved} moved'
            "</option>"
        )
        active_class = " style='background:#eff6ff;'" if rid == (selected_run or {}).get("run_id") else ""
        run_rows += (
            f"<tr{active_class}>"
            f"<td><a class='run-link' href='/?run_id={quote_plus(rid)}&target={quote_plus(str(target))}'>{html.escape(rid)}</a></td>"
            f"<td>{html.escape(run.get('started_at', ''))}</td>"
            f"<td style='max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{html.escape(run.get('downloads_path', ''))}</td>"
            f"<td><strong>{moved}</strong></td>"
            f"<td>{preview}</td>"
            f"<td>{skipped}</td>"
            f"<td>{_badge(str(errors), '#b91c1c') if errors else '0'}</td>"
            "</tr>"
        )

    msg_bg = {"info": "#eff6ff", "error": "#fef2f2"}.get(message_type, "#fffbeb")
    msg_border = {"info": "#bfdbfe", "error": "#fecaca"}.get(message_type, "#fde68a")
    msg_color = {"info": "#1e40af", "error": "#991b1b"}.get(message_type, "#92400e")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Downloads Organizer Dashboard</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: #f1f5f9; color: #1e293b; }}

    .header {{ background: linear-gradient(135deg, #1e3a5f 0%, #0f766e 100%); color: #fff; padding: 20px 32px; }}
    .header h1 {{ margin: 0; font-size: 26px; letter-spacing: -0.5px; }}
    .header p {{ margin: 4px 0 0; opacity: 0.85; font-size: 14px; }}

    .container {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}

    .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
    .card h2 {{ margin: 0 0 14px; font-size: 17px; color: #334155; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}

    .msg-bar {{ padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 600;
                background: {msg_bg}; border: 1px solid {msg_border}; color: {msg_color};
                margin-bottom: 16px; display: {"block" if message else "none"}; }}

    .stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }}
    .stat {{ flex: 1; min-width: 120px; text-align: center; padding: 14px 8px; border-radius: 10px; }}
    .stat .num {{ font-size: 28px; font-weight: 700; }}
    .stat .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; opacity: 0.8; }}

    .form-row {{ margin-bottom: 12px; }}
    .form-row label {{ display: block; font-weight: 600; font-size: 13px; color: #475569; margin-bottom: 4px; }}
    .form-row input[type="text"], .form-row select {{
      width: 100%; max-width: 640px; padding: 9px 12px; border: 1px solid #cbd5e1; border-radius: 8px;
      font-size: 14px; background: #f8fafc; transition: border 0.15s;
    }}
    .form-row input:focus, .form-row select:focus {{ outline: none; border-color: #0f766e; box-shadow: 0 0 0 3px rgba(15,118,110,0.12); }}

    .btn-group {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }}
    .btn {{ padding: 9px 16px; border: none; border-radius: 8px; font-size: 13px; font-weight: 600;
            cursor: pointer; transition: transform 0.1s, box-shadow 0.15s; }}
    .btn:hover {{ transform: translateY(-1px); box-shadow: 0 2px 6px rgba(0,0,0,0.12); }}
    .btn:active {{ transform: translateY(0); }}
    .btn-primary {{ background: #0f766e; color: #fff; }}
    .btn-blue {{ background: #2563eb; color: #fff; }}
    .btn-amber {{ background: #d97706; color: #fff; }}
    .btn-red {{ background: #b91c1c; color: #fff; }}
    .btn-gray {{ background: #475569; color: #fff; }}

    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #f1f5f9; font-size: 12px; text-transform: uppercase; letter-spacing: 0.4px; color: #64748b; padding: 10px 8px; text-align: left; border-bottom: 2px solid #e2e8f0; }}
    td {{ padding: 8px; font-size: 13px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }}
    td code {{ font-size: 11px; color: #475569; word-break: break-all; }}

    .run-link {{ color: #0f766e; font-weight: 600; text-decoration: none; }}
    .run-link:hover {{ text-decoration: underline; }}

    .meta {{ font-size: 12px; color: #94a3b8; margin-top: 8px; }}
    .meta code {{ font-size: 11px; }}

    .table-wrap {{ overflow-x: auto; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Downloads Organizer</h1>
    <p>Organize, backup, and track every file move in your Downloads folder</p>
  </div>

  <div class="container">
    <div class="msg-bar">{html.escape(message)}</div>

    <div class="card">
      <h2>Actions</h2>
      <form method="post" action="/action">
        <div class="form-row">
          <label>Target Folder</label>
          <input type="text" name="target_path" value="{html.escape(str(target))}" />
        </div>
        <div class="form-row">
          <label>Inspect Run</label>
          <select name="run_id">
            {run_options}
          </select>
        </div>
        <div class="btn-group">
          <button class="btn btn-primary" type="submit" name="action" value="run">Run (with backup)</button>
          <button class="btn btn-blue" type="submit" name="action" value="dry_run">Dry Run Preview</button>
          <button class="btn btn-amber" type="submit" name="action" value="run_no_backup">Run (no backup)</button>
          <button class="btn btn-red" type="submit" name="action" value="undo">Undo Last Run</button>
          <button class="btn btn-gray" type="submit" name="action" value="show_run">Show Selected Run</button>
        </div>
      </form>
      <div class="meta">History: <code>{html.escape(str(organizer.PROJECT_DATA_DIR / "runs_history.json"))}</code></div>
    </div>

    <div class="card">
      <h2>Selected Run: {sel_run_label}</h2>
      <div class="stats">
        <div class="stat" style="background:#ecfdf5;color:#065f46"><div class="num">{sel_moved}</div><div class="label">Moved</div></div>
        <div class="stat" style="background:#eff6ff;color:#1e40af"><div class="num">{sel_preview}</div><div class="label">Preview</div></div>
        <div class="stat" style="background:#fffbeb;color:#92400e"><div class="num">{sel_skipped}</div><div class="label">Skipped</div></div>
        <div class="stat" style="background:#fef2f2;color:#991b1b"><div class="num">{sel_errors}</div><div class="label">Errors</div></div>
      </div>
    </div>

    <div class="card">
      <h2>Recent Runs</h2>
      <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Run ID</th><th>Started</th><th>Target Path</th><th>Moved</th><th>Preview</th><th>Skipped</th><th>Errors</th></tr>
        </thead>
        <tbody>
          {run_rows or '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">No runs yet.</td></tr>'}
        </tbody>
      </table>
      </div>
    </div>

    <div class="card">
      <h2>File Mapping &mdash; Original &rarr; Moved</h2>
      <div class="table-wrap">
      <table>
        <thead>
          <tr><th>#</th><th>File</th><th>Original Path</th><th>Moved Path</th><th>Category</th><th>Status</th><th>Backup Path</th></tr>
        </thead>
        <tbody>
          {details_rows or '<tr><td colspan="7" style="text-align:center;color:#94a3b8;">No run details available.</td></tr>'}
        </tbody>
      </table>
      </div>
    </div>
  </div>
</body>
</html>"""


class OrganizerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        message = query.get("msg", [""])[0]
        message_type = query.get("type", ["info"])[0]
        selected = query.get("target", [""])[0]
        run_id = query.get("run_id", [""])[0]
        page = _render_page(
            message=message,
            message_type=message_type,
            selected_path=_safe_target(selected),
            selected_run_id=run_id,
        )
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
        run_id = form.get("run_id", [""])[0]

        try:
            if action == "run":
                result = organizer.organize_downloads(base_dir=target, create_backup=True, dry_run=False)
                moved = sum(1 for record in result["records"] if record["status"] == "moved")
                msg = f"Run {result['run_id']} completed. Moved {moved} file(s)."
                run_id = result["run_id"]
            elif action == "dry_run":
                result = organizer.organize_downloads(base_dir=target, create_backup=True, dry_run=True)
                preview = sum(1 for record in result["records"] if record["status"] == "would_move")
                msg = f"Dry run {result['run_id']} complete. Would move {preview} file(s)."
                run_id = result["run_id"]
            elif action == "run_no_backup":
                result = organizer.organize_downloads(base_dir=target, create_backup=False, dry_run=False)
                moved = sum(1 for record in result["records"] if record["status"] == "moved")
                msg = f"Run {result['run_id']} completed (no backup). Moved {moved} file(s)."
                run_id = result["run_id"]
            elif action == "undo":
                ok = organizer.undo_last_move(base_dir=target)
                msg = "Undo completed." if ok else "No run history found for undo."
            elif action == "show_run":
                msg = f"Showing run details for: {run_id or 'latest'}"
            else:
                msg = "Unsupported action."
        except Exception as error:  # pragma: no cover
            self._redirect(
                f"/?msg={quote_plus(str(error))}&type=error&target={quote_plus(str(target))}&run_id={quote_plus(run_id)}"
            )
            return

        self._redirect(
            f"/?msg={quote_plus(msg)}&type=info&target={quote_plus(str(target))}&run_id={quote_plus(run_id)}"
        )

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
