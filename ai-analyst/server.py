# siemnest AI analyst - stdlib only.
# Polls the shared OpenSearch data plane for security events (Wazuh alerts)
# and Graylog log streams, asks an OpenAI-compatible LLM to correlate and
# summarize them, stores verdicts, and serves them to the portal.
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("AI_PORT", "8090"))
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama3.1:8b")
OS_URL = os.environ.get("OPENSEARCH_URL", "").rstrip("/")
OS_USER = os.environ.get("OPENSEARCH_USER", "admin")
OS_PASSWORD = os.environ.get("OPENSEARCH_PASSWORD", "")
GRAYLOG_API = os.environ.get("GRAYLOG_API", "").rstrip("/")
GRAYLOG_TOKEN = os.environ.get("GRAYLOG_TOKEN", "")
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "60"))

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE  # self-signed indexer certs inside the stack

FINDINGS = []          # latest AI verdicts (newest first)
STATE = {"last_poll": 0, "last_error": "", "llm_calls": 0}


def http_json(url, method="GET", body=None, headers=None, timeout=15):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    ctx = SSL_CTX if url.startswith("https") else None
    with urllib.request.urlopen(req, data=data, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode())


def fetch_recent_events():
    """Pull recent events from the shared OpenSearch plane (Wazuh alert indices
    + Graylog default streams) and normalize them for the LLM."""
    events = []
    if OS_URL:
        try:
            res = http_json(
                f"{OS_URL}/wazuh-alerts-*/_search",
                body={"size": 25, "sort": [{"timestamp": {"order": "desc"}}],
                      "_source": ["timestamp", "rule.description", "rule.level",
                                  "agent.name", "data.srcip", "rule.groups"]},
                headers=_basic(OS_USER, OS_PASSWORD))
            for hit in res.get("hits", {}).get("hits", []):
                src = hit.get("_source", {})
                rule = src.get("rule", {})
                events.append({
                    "source": "wazuh",
                    "description": rule.get("description", ""),
                    "level": rule.get("level"),
                    "agent": src.get("agent", {}).get("name", ""),
                    "src_ip": src.get("data", {}).get("srcip", ""),
                    "groups": rule.get("groups", [])[:4],
                })
        except Exception as e:  # noqa: BLE001
            STATE["last_error"] = f"opensearch: {e}"
    if GRAYLOG_API and GRAYLOG_TOKEN:
        try:
            res = http_json(
                f"{GRAYLOG_API}/search/universal/relative?query=*&range=900&limit=15",
                headers={"Authorization": f"Basic {GRAYLOG_TOKEN}", "Accept": "application/json"})
            for msg in res.get("messages", [])[:15]:
                f = msg.get("message", {})
                events.append({
                    "source": "graylog",
                    "description": str(f.get("message", ""))[:200],
                    "level": f.get("level"),
                    "agent": f.get("source", ""),
                    "src_ip": f.get("gl2_remote_ip", ""),
                    "groups": [],
                })
        except Exception as e:  # noqa: BLE001
            STATE["last_error"] = f"graylog: {e}"
    return events


def _basic(user, pw):
    import base64
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()}


def llm_analyze(events):
    """Ask the LLM to correlate the event batch into a verdict. Falls back to a
    deterministic heuristic digest when no LLM endpoint is configured."""
    if not events:
        return {"verdict": "quiet", "summary": "No recent events from either source.", "priority": "info"}
    if not LLM_BASE_URL:
        wazuh_n = sum(1 for e in events if e["source"] == "wazuh")
        graylog_n = len(events) - wazuh_n
        hi = [e for e in events if isinstance(e.get("level"), int) and e["level"] >= 10]
        verdict = "attention" if hi else "normal"
        return {
            "verdict": verdict,
            "priority": "high" if hi else "info",
            "summary": (f"{len(events)} events: {wazuh_n} security (Wazuh), {graylog_n} log "
                        f"(Graylog). {len(hi)} high-severity rule hits." if hi else
                        f"{len(events)} events: {wazuh_n} security (Wazuh), {graylog_n} log (Graylog). Nothing high-severity."),
            "model": "heuristic",
        }
    prompt = (
        "You are a SOC analyst. Correlate these events from two SIEM sources "
        "(Wazuh security alerts + Graylog log streams) and reply with STRICT JSON: "
        '{"verdict":"quiet|normal|attention|critical","priority":"info|medium|high",'
        '"summary":"<max 3 sentences>", "notable":["..."]}. Events: '
        + json.dumps(events[:40])
    )
    try:
        res = http_json(
            f"{LLM_BASE_URL}/chat/completions",
            body={"model": LLM_MODEL, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.2},
            headers={"Authorization": f"Bearer {LLM_API_KEY}"} if LLM_API_KEY else {},
            timeout=60)
        STATE["llm_calls"] += 1
        content = res["choices"][0]["message"]["content"]
        start, end = content.find("{"), content.rfind("}")
        return json.loads(content[start:end + 1]) if start != -1 else {"verdict": "normal", "summary": content[:400]}
    except Exception as e:  # noqa: BLE001
        STATE["last_error"] = f"llm: {e}"
        return {"verdict": "normal", "summary": f"LLM unavailable ({e})", "model": "fallback"}


def poll_loop():
    while True:
        try:
            events = fetch_recent_events()
            verdict = llm_analyze(events)
            verdict["event_count"] = len(events)
            verdict["ts"] = int(time.time())
            FINDINGS.insert(0, verdict)
            del FINDINGS[20:]
            STATE["last_poll"] = int(time.time())
        except Exception as e:  # noqa: BLE001
            STATE["last_error"] = str(e)
        time.sleep(POLL_SECONDS)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/healthz":
            return self._send(200, "text/plain", b"ok")
        if path == "/api/findings":
            return self._send(200, "application/json", json.dumps({"findings": FINDINGS, "state": STATE}).encode())
        return self._send(404, "text/plain", b"not found")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    import threading
    threading.Thread(target=poll_loop, daemon=True).start()
    print(f"[siemnest-ai] on :{PORT} | llm={LLM_BASE_URL or 'heuristic'} model={LLM_MODEL}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
