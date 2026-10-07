from __future__ import annotations

import hashlib
import html
import json
import os
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DASHBOARD_KEY = os.environ.get("DASHBOARD_KEY", "han").strip()
DATA_DIR = Path(os.environ.get("DATA_DIR", "/tmp/alb_data"))
FILE_DIR = DATA_DIR / "uploads"
FILE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_name(name: str) -> str:
    name = Path(name or "file.txt").name
    return "".join(c for c in name if c.isalnum() or c in "._- ")[:120] or "file.txt"


def _authorized(handler: BaseHTTPRequestHandler) -> bool:
    if not DASHBOARD_KEY:
        return False
    cookie = handler.headers.get("Cookie", "")
    return f"alb_dash={hashlib.sha256(DASHBOARD_KEY.encode()).hexdigest()}" in cookie


def _json(handler, obj, status=200):
    raw = json.dumps(obj, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _html(handler, body, status=200):
    raw = body.encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _files():
    out = []
    for p in sorted(FILE_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_file():
            continue
        st = p.stat()
        out.append({"name": p.name, "size": st.st_size, "mtime": st.st_mtime})
    return out


def dashboard_html():
    return r'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ALB Forge • Control Center</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;color:#eef4ff;background:#07111f}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(circle at 10% 0%,#244a73 0,transparent 34%),radial-gradient(circle at 90% 20%,#54265f 0,transparent 32%),#07111f}.wrap{max-width:1250px;margin:auto;padding:28px}.glass{background:rgba(255,255,255,.075);border:1px solid rgba(255,255,255,.16);box-shadow:0 24px 70px rgba(0,0,0,.3),inset 0 1px rgba(255,255,255,.1);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border-radius:28px}.hero{padding:28px;margin-bottom:18px;display:flex;justify-content:space-between;gap:20px;align-items:center}.brand{display:flex;gap:15px;align-items:center}.logo{width:56px;height:56px;border-radius:18px;display:grid;place-items:center;background:linear-gradient(135deg,rgba(125,211,252,.4),rgba(192,132,252,.35));font-size:28px}.muted{color:#a9b8cb}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{padding:20px}.value{font-size:29px;font-weight:800;margin-top:8px}.section{margin-top:18px;padding:22px}.section h2{margin:0 0 16px}.table{width:100%;border-collapse:collapse}.table th,.table td{text-align:left;padding:12px;border-bottom:1px solid rgba(255,255,255,.09)}button,input{font:inherit}button{border:0;border-radius:14px;padding:10px 15px;cursor:pointer;color:#fff;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.15)}button:hover{background:rgba(255,255,255,.2)}.danger{background:rgba(244,63,94,.22)}.primary{background:rgba(59,130,246,.3)}.login{max-width:470px;margin:10vh auto;padding:28px}.login input{width:100%;padding:14px;border-radius:14px;border:1px solid rgba(255,255,255,.18);background:rgba(0,0,0,.2);color:#fff;margin:10px 0}.pill{display:inline-block;padding:6px 10px;border-radius:999px;background:rgba(52,211,153,.14);color:#8ff0c2}.file-actions{display:flex;gap:8px;flex-wrap:wrap}.small{font-size:12px}.empty{padding:24px;text-align:center;color:#9fb0c4}@media(max-width:850px){.grid{grid-template-columns:repeat(2,1fr)}.hero{flex-direction:column;align-items:flex-start}}@media(max-width:520px){.grid{grid-template-columns:1fr}.wrap{padding:14px}.section{overflow:auto}}
</style></head><body><div id="app" class="wrap"></div>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>{n=Number(n||0);return n<1024?n+' B':n<1048576?(n/1024).toFixed(1)+' KB':(n/1048576).toFixed(1)+' MB'};
async function api(u,o){let r=await fetch(u,o);if(r.status===401){showLogin();throw Error('auth')}let j=await r.json();if(!r.ok)throw Error(j.error||'Lỗi');return j}
function showLogin(){document.getElementById('app').innerHTML=`<div class="glass login"><div class="brand"><div class="logo">✦</div><div><h1>ALB Forge</h1><div class="muted">Dashboard quản trị</div></div></div><p class="muted">Nhập DASHBOARD_KEY đã đặt trong Render Environment.</p><input id="key" type="password" placeholder="Dashboard key"><button class="primary" onclick="login()">Mở Control Center</button></div>`}
async function login(){let key=document.getElementById('key').value;let r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})});if(r.ok)load();else alert('Key không đúng')}
async function load(){try{let s=await api('/api/stats');let f=await api('/api/files');render(s,f)}catch(e){if(e.message!=='auth')document.getElementById('app').innerHTML='<div class="glass login"><h2>Không tải được dashboard</h2><p class="muted">'+esc(e.message)+'</p></div>'}}
function render(s,f){document.getElementById('app').innerHTML=`<div class="glass hero"><div class="brand"><div class="logo">✦</div><div><h1 style="margin:0">ALB Forge Control Center</h1><div class="muted">Realtime operations • ${esc(s.bot||'Bot')}</div></div></div><span class="pill">● ${esc(s.status||'ONLINE')}</span></div>
<div class="grid"><div class="glass card"><div class="muted">Uptime</div><div class="value">${esc(s.uptime)}</div></div><div class="glass card"><div class="muted">Updates</div><div class="value">${s.updates}</div></div><div class="glass card"><div class="muted">Commands</div><div class="value">${s.commands}</div></div><div class="glass card"><div class="muted">Errors</div><div class="value">${s.errors}</div></div></div>
<div class="glass section"><h2>📊 Runtime</h2><div class="grid"><div class="card"><div class="muted">Active tasks</div><div class="value">${s.tasks}</div></div><div class="card"><div class="muted">File sessions</div><div class="value">${s.file_sessions}</div></div><div class="card"><div class="muted">Stored files</div><div class="value">${f.files.length}</div></div><div class="card"><div class="muted">Memory</div><div class="value">${esc(s.memory)}</div></div></div></div>
<div class="glass section"><h2>📂 File manager</h2><p class="muted">Upload tài liệu vào kho của bot. Chỉ tài khoản dashboard đã đăng nhập mới được upload/xóa.</p><input id="up" type="file" accept=".txt,.log,.csv"><button class="primary" onclick="upload()">⬆️ Upload</button><div id="files">${filesHtml(f.files)}</div></div>
<div class="glass section"><h2>🧾 Activity</h2><div class="muted small">Last update: ${esc(s.last_event||'Chưa có')}</div><pre style="white-space:pre-wrap;color:#c9d6e8">${esc((s.recent||[]).join('\n'))}</pre></div>`}
function filesHtml(fs){if(!fs.length)return '<div class="empty">Chưa có file.</div>';return '<table class="table"><thead><tr><th>Tên</th><th>Kích thước</th><th>Thời gian</th><th></th></tr></thead><tbody>'+fs.map(x=>`<tr><td>${esc(x.name)}</td><td>${fmt(x.size)}</td><td>${new Date(x.mtime*1000).toLocaleString('vi-VN')}</td><td><button class="danger" onclick="delFile(${JSON.stringify(x.name)})">🗑 Xóa</button></td></tr>`).join('')+'</tbody></table>'}
async function upload(){let f=document.getElementById('up').files[0];if(!f)return alert('Chọn file trước');let fd=new FormData();fd.append('file',f);let r=await fetch('/api/upload',{method:'POST',body:fd});if(!r.ok){let j=await r.json();return alert(j.error||'Upload lỗi')}load()}
async function delFile(name){if(!confirm('Xóa '+name+'?'))return;let r=await fetch('/api/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});if(!r.ok){let j=await r.json();return alert(j.error||'Xóa lỗi')}load()}
load();setInterval(load,5000);
</script></body></html>'''


def make_handler(state):
    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlparse(self.path).path
            if path in ("/", "/dashboard"):
                if not DASHBOARD_KEY:
                    _html(self, '<h2>Dashboard chưa được cấu hình</h2><p>Đặt DASHBOARD_KEY trong Render Environment.</p>', 503)
                elif _authorized(self):
                    _html(self, dashboard_html())
                else:
                    _html(self, dashboard_html())
                return
            if path == "/health":
                raw=b"alive"; self.send_response(200); self.send_header("Content-Type","text/plain"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw); return
            if path == "/api/stats":
                if not _authorized(self): return _json(self, {"error":"Unauthorized"}, 401)
                _json(self, state.snapshot())
                return
            if path == "/api/files":
                if not _authorized(self): return _json(self, {"error":"Unauthorized"}, 401)
                _json(self, {"files":_files()})
                return
            self.send_response(404); self.end_headers()

        def do_POST(self):
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length", "0"))
            if length > 2 * 1024 * 1024:
                return _json(self, {"error":"File quá lớn (tối đa 2 MB)"}, 413)
            body = self.rfile.read(length)
            if path == "/api/login":
                try: key = json.loads(body.decode()).get("key", "")
                except Exception: key = ""
                if DASHBOARD_KEY and key == DASHBOARD_KEY:
                    cookie = hashlib.sha256(DASHBOARD_KEY.encode()).hexdigest()
                    self.send_response(200); self.send_header("Set-Cookie", f"alb_dash={cookie}; HttpOnly; SameSite=Strict; Path=/"); self.send_header("Content-Length","2"); self.end_headers(); self.wfile.write(b"OK"); return
                return _json(self,{"error":"Unauthorized"},401)
            if not _authorized(self): return _json(self,{"error":"Unauthorized"},401)
            if path == "/api/delete":
                try: name = json.loads(body.decode()).get("name", "")
                except Exception: name = ""
                p = FILE_DIR / _safe_name(name)
                if p.exists() and p.is_file():
                    p.unlink(); state.event(f"Deleted file: {p.name}"); return _json(self,{"ok":True})
                return _json(self,{"error":"Không tìm thấy file"},404)
            if path == "/api/upload":
                ctype = self.headers.get("Content-Type", "")
                boundary = ctype.split("boundary=",1)[1].encode() if "boundary=" in ctype else None
                if not boundary: return _json(self,{"error":"Multipart không hợp lệ"},400)
                marker = b"--" + boundary
                for part in body.split(marker):
                    if b"filename=" not in part: continue
                    head, sep, content = part.partition(b"\r\n\r\n")
                    if not sep: continue
                    line = head.decode("utf-8","ignore")
                    import re
                    m = re.search(r'filename="([^"]*)"', line)
                    if not m: continue
                    name = _safe_name(m.group(1)); content = content.rsplit(b"\r\n",1)[0]
                    if len(content) > 256*1024: return _json(self,{"error":"File quá lớn (tối đa 256 KB)"},413)
                    if not name.lower().endswith((".txt",".log",".csv")): return _json(self,{"error":"Chỉ nhận .txt/.log/.csv"},400)
                    target = FILE_DIR / name
                    target.write_bytes(content); state.event(f"Uploaded file: {name}"); return _json(self,{"ok":True,"name":name})
                return _json(self,{"error":"Không tìm thấy file upload"},400)
            return _json(self,{"error":"Not found"},404)

        def log_message(self,*args): pass
    return DashboardHandler
