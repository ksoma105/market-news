"""Best-effort ElevenLabs narration, independent of article publication."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib import error, parse, request

ISSUE = re.compile(r"\d{4}-\d{2}-\d{2}-(?:0600|1200|2200)")
ERROR_REASONS = {
    "quota_exceeded": "quota_exceeded",
    "insufficient_credits": "quota_exceeded",
    "subscription_required": "subscription_required",
    "subscription_expired": "subscription_required",
    "paid_plan_required": "subscription_required",
    "rate_limit_exceeded": "rate_limited",
    "too_many_concurrent_requests": "rate_limited",
    "invalid_api_key": "authentication_error",
    "voice_not_found": "voice_not_found",
}


class NarrationLink(HTMLParser):
    def __init__(self):
        super().__init__()
        self.issues = set()

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href", "")
        if tag == "a":
            match = re.fullmatch(r"narration/(\d{4}-\d{2}-\d{2}-(?:0600|1200|2200))\.txt", href)
            if match:
                self.issues.add(match.group(1))


def current_issue(root):
    parser = NarrationLink()
    parser.feed((root / "docs/index.html").read_text(encoding="utf-8"))
    if len(parser.issues) != 1:
        raise ValueError("Missing or ambiguous narration link")
    return next(iter(parser.issues))


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def convert(text, key, voice):
    url = "https://api.elevenlabs.io/v1/text-to-speech/" + parse.quote(voice, safe="")
    url += "?output_format=mp3_44100_128"
    body = json.dumps({"text": text, "model_id": "eleven_v4", "language_code": "ja"}).encode("utf-8")
    req = request.Request(url, data=body, headers={
        "xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg",
    }, method="POST")
    with request.build_opener(NoRedirect()).open(req, timeout=120) as response:
        if response.headers.get_content_type() not in ("audio/mpeg", "audio/mp3", "application/octet-stream"):
            raise ValueError("Unexpected audio content type")
        audio = response.read(15 * 1024 * 1024 + 1)
        if not audio or len(audio) > 15 * 1024 * 1024:
            raise ValueError("Invalid audio size")
        return audio


def validate_audio(path):
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name",
        "-of", "json", str(path),
    ], check=True, capture_output=True, text=True, timeout=30)
    info = json.loads(probe.stdout)
    duration = float(info.get("format", {}).get("duration", 0))
    if duration <= 0 or not any(s.get("codec_name") == "mp3" for s in info.get("streams", [])):
        raise ValueError("Invalid MP3")
    return duration


def api_reason(exc):
    # Never expose an API message: it may contain credentials or account details.
    try:
        body = json.loads(exc.read(65536))
        detail = body.get("detail", {})
        code = detail.get("status") if isinstance(detail, dict) else None
    except (ValueError, OSError):
        code = None
    if isinstance(code, str) and code in ERROR_REASONS:
        return ERROR_REASONS[code]
    if exc.code == 429:
        return "rate_limited"
    if exc.code == 401:
        return "authentication_error"
    return "api_error"


def generate(root, issue, env=None, converter=convert, validator=validate_audio):
    env = os.environ if env is None else env
    if not ISSUE.fullmatch(issue):
        raise ValueError("Invalid issue ID")
    audio_dir = root / "docs/audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / (issue + ".mp3")
    status_path = audio_dir / (issue + ".json")
    # One attempt per issue, including skipped issues. A new issue gets a new attempt.
    if status_path.exists():
        return json.loads(status_path.read_text(encoding="utf-8"))
    state = {"issue_id": issue, "model_id": "eleven_v4", "status": "skipped", "checked_at": datetime.now(timezone.utc).isoformat()}
    temporary = audio_dir / (issue + ".mp3.tmp")
    stage = "prepare"
    try:
        text = (root / "docs/narration" / (issue + ".txt")).read_text(encoding="utf-8").strip()
        key = env.get("ELEVENLABS_API_KEY", "").strip()
        voice = env.get("ELEVENLABS_VOICE_ID", "").strip()
        if not key or not voice:
            state["reason"] = "configuration_missing"
        elif not text or len(text) > 9500:
            state["reason"] = "invalid_narration_length"
        else:
            if validator is validate_audio and shutil.which("ffprobe") is None:
                raise FileNotFoundError("MP3 validator unavailable")
            # A validated existing file can be recovered without billing again.
            if audio_path.exists():
                stage = "validation"
                duration = validator(audio_path)
            else:
                stage = "request"
                temporary.write_bytes(converter(text, key, voice))
                stage = "validation"
                duration = validator(temporary)
                stage = "save"
                temporary.replace(audio_path)
            state.update(status="ready", file=issue + ".mp3", duration_seconds=round(duration, 2),
                         narration_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())
    except error.HTTPError as exc:
        state["reason"] = api_reason(exc)
        state["http_status"] = exc.code
    except (TimeoutError, socket.timeout):
        state["reason"] = "timeout"
    except error.URLError:
        state["reason"] = "connection_error"
    except Exception as exc:
        state["reason"] = "audio_processing_error"
        state["failure_stage"] = stage
        state["error_type"] = type(exc).__name__
    finally:
        if temporary.exists():
            # Keep a failed validation response as a private run artifact, not a public asset.
            recovery = root / "audio-work"
            recovery.mkdir(exist_ok=True)
            temporary.replace(recovery / (issue + ".mp3"))
        temporary.unlink(missing_ok=True)
    pending_status = status_path.with_suffix(".json.tmp")
    pending_status.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending_status.replace(status_path)
    return state


def main():
    root = Path(__file__).resolve().parents[1]
    state = generate(root, current_issue(root))
    print(json.dumps(state, ensure_ascii=False))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        message = "音声生成済み" if state["status"] == "ready" else "音声スキップ：" + state.get("reason", "unknown")
        with open(summary, "a", encoding="utf-8") as target:
            target.write("\n## " + state["issue_id"] + "\n記事の公開は独立して継続します。" + message + "\n")


if __name__ == "__main__":
    main()
