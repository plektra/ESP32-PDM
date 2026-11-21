"""Fetch EasyEDA footprints for LCSC codes from the pcbparts MCP server into a JSON file."""
import json, sys, urllib.request

URL = 'https://pcbparts.dev/mcp'
HDR = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}


def post(body, sid=None):
    h = dict(HDR)
    if sid:
        h['Mcp-Session-Id'] = sid
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=h)
    with urllib.request.urlopen(req, timeout=120) as r:
        sid = r.headers.get('Mcp-Session-Id') or sid
        raw = r.read().decode()
    msgs = []
    for line in raw.splitlines():
        if line.startswith('data:'):
            msgs.append(json.loads(line[5:]))
    if not msgs and raw.strip().startswith('{'):
        msgs.append(json.loads(raw))
    return sid, msgs


sid, _ = post({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
               'params': {'protocolVersion': '2025-03-26', 'capabilities': {},
                          'clientInfo': {'name': 'fp-check', 'version': '1'}}})
post({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, sid)
out = {}
for i, code in enumerate(sys.argv[2:]):
    _, msgs = post({'jsonrpc': '2.0', 'id': 10 + i, 'method': 'tools/call',
                    'params': {'name': 'jlc_get_pinout', 'arguments': {'lcsc': code, 'footprint': True}}}, sid)
    res = msgs[-1].get('result', msgs[-1])
    try:
        out[code] = json.loads(res['content'][0]['text'])
    except Exception:
        out[code] = res
    print(code, 'ok' if 'footprint' in out[code] else str(out[code])[:200], file=sys.stderr)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
