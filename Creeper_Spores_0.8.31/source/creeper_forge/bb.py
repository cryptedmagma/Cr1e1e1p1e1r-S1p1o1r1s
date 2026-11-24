"""Tiny client for the Blockbench MCP plugin (HTTP, localhost:3000/bb-mcp)."""
import json, urllib.request, base64
URL = 'http://localhost:3000/bb-mcp'
_sid = None
_id = 0

def _post(payload, timeout=120):
    h = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    if _sid: h['mcp-session-id'] = _sid
    r = urllib.request.urlopen(urllib.request.Request(URL, json.dumps(payload).encode(), h), timeout=timeout)
    body = r.read().decode()
    sid = r.headers.get('mcp-session-id')
    if body.lstrip().startswith(('event', 'data')):
        datas = [l[5:].strip() for l in body.splitlines() if l.startswith('data:')]
        body = datas[-1] if datas else ''
    return sid, (json.loads(body) if body.strip() else None)

def connect():
    global _sid
    _sid, _ = _post({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "creeper-forge", "version": "1"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"})

def rpc(method, params=None, timeout=120):
    global _id
    if _sid is None: connect()
    _id += 1
    _, d = _post({"jsonrpc": "2.0", "id": _id, "method": method, "params": params or {}}, timeout)
    if 'error' in d: raise RuntimeError(d['error'])
    return d['result']

def tool(name, timeout=120, **args):
    return rpc('tools/call', {'name': name, 'arguments': args}, timeout)

def text(res):
    return '\n'.join(c.get('text', '') for c in res.get('content', []) if c.get('type') == 'text')

def save_images(res, path_prefix):
    out = []
    for i, c in enumerate(c for c in res.get('content', []) if c.get('type') == 'image'):
        p = f'{path_prefix}_{i}.png' if i else f'{path_prefix}.png'
        open(p, 'wb').write(base64.b64decode(c['data'])); out.append(p)
    return out

def js(code, timeout=120):
    return text(tool('risky_eval', timeout, code=code))
