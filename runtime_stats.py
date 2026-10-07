from __future__ import annotations
import os, resource, threading, time
from collections import deque
from datetime import datetime

class RuntimeStats:
    def __init__(self, started_at):
        self.started_at=started_at; self.lock=threading.Lock(); self.updates=0; self.commands=0; self.errors=0; self.events=deque(maxlen=80); self.bot=''; self.status='STARTING'; self.provider=lambda: {}
    def update(self):
        with self.lock: self.updates += 1
    def command(self):
        with self.lock: self.commands += 1
    def error(self, e):
        with self.lock: self.errors += 1; self.events.appendleft(f"{datetime.now():%Y-%m-%d %H:%M:%S} ERROR {type(e).__name__}: {e}")
    def event(self, s):
        with self.lock: self.events.appendleft(f"{datetime.now():%Y-%m-%d %H:%M:%S} {s}")
    def set_provider(self, fn):
        self.provider=fn
    def snapshot(self):
        with self.lock:
            rss = getattr(resource.getrusage(resource.RUSAGE_SELF),'ru_maxrss',0)
            memory = f"{rss/1024:.1f} MB" if rss else 'n/a'
            extra=self.provider() or {}
            return {'status':self.status,'bot':self.bot,'uptime':self._uptime(),'updates':self.updates,'commands':self.commands,'errors':self.errors,'tasks':extra.get('tasks',0),'file_sessions':extra.get('file_sessions',0),'memory':memory,'last_event':self.events[0] if self.events else 'Chưa có','recent':list(self.events)[:30]}
    def _uptime(self):
        s=int(time.time()-self.started_at); h,s=divmod(s,3600); m,s=divmod(s,60); return f'{h:02d}:{m:02d}:{s:02d}'
