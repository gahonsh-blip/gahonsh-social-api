"""Small HTTP helper: JSON, multipart and retries in one place."""
import json
import mimetypes
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def request(method, url, json_body=None, data=None, headers=None, files=None,
            timeout=120, retries=2):
    """Returns (status, parsed_or_text). Never raises for HTTP errors."""
    headers = dict(headers or {})
    body = None

    if files:
        boundary = "----gahonsh" + str(int(time.time() * 1000))
        parts = []
        for name, value in (data or {}).items():
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
            )
        for name, path in files.items():
            path = Path(path)
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{path.name}\"\r\n"
                f"Content-Type: {ctype}\r\n\r\n".encode()
            )
            parts.append(path.read_bytes())
            parts.append(b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif json_body is not None:
        body = json.dumps(json_body).encode()
        headers.setdefault("Content-Type", "application/json")
    elif data:
        body = urllib.parse.urlencode(data).encode()
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8", "ignore")
                return r.status, _maybe_json(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "ignore")
            last = (e.code, _maybe_json(raw))
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            return last
        except Exception as e:  # network
            last = (0, str(e))
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            return last
    return last


def _maybe_json(raw):
    try:
        return json.loads(raw)
    except Exception:
        return raw
