"""
JSON Bridge: Node.js Express → Python Grievance AI Pipeline.

Receives JSON via stdin, writes ONE JSON object to stdout,
keeps all diagnostic/progress output strictly on stderr.
Never exposes stack traces in the JSON output.
"""

import sys
import json
import traceback

# Redirect all progress prints from pipeline modules to stderr
# so they do not contaminate the JSON stdout channel.
import io

if hasattr(sys.stdin, "reconfigure"):
    try:
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

_original_stdout = sys.stdout
_stderr_only     = sys.stderr


def _force_stderr_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def main():
    # ── Read stdin ───────────────────────────────────────────
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        raw = sys.stdin.read()

    if not raw or not raw.strip():
        json.dump({"error": "Empty input received by bridge."}, _original_stdout, ensure_ascii=False)
        return

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        json.dump({"error": f"Invalid JSON input: {exc}"}, _original_stdout, ensure_ascii=False)
        return

    text      = payload.get("text", "")
    area      = payload.get("area", "Unknown")
    days_open = int(payload.get("days_open", 0))

    if not text or not text.strip():
        json.dump({"error": "Empty grievance text."}, _original_stdout, ensure_ascii=False)
        return

    # ── Redirect module-level print() to stderr ──────────────
    sys.stdout = sys.stderr  # while loading pipeline, capture progress
    try:
        from pipeline import pipeline_instance
        pipeline_instance.initialize()
        result = pipeline_instance.process_grievance(text, area=area, days_open=days_open)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        sys.stdout = _original_stdout
        json.dump({"error": str(exc)}, _original_stdout, ensure_ascii=False)
        _original_stdout.flush()
        return
    finally:
        sys.stdout = _original_stdout      # restore stdout before writing result

    # ── Write result to stdout ───────────────────────────────
    json.dump(result, _original_stdout, ensure_ascii=False)
    _original_stdout.flush()


if __name__ == "__main__":
    main()
