import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
@contextmanager
def db(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path,timeout=10);conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE IF NOT EXISTS artifacts (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(kind,name,version))')
    conn.execute('CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    try:
        with conn:yield conn
    finally:conn.close()
def unpack(row):return {**dict(row),'payload':json.loads(row['payload'])}
def save(path,kind,name,payload):
    with db(path) as conn:
        conn.execute('BEGIN IMMEDIATE');version=conn.execute('SELECT COALESCE(MAX(version),0)+1 FROM artifacts WHERE kind=? AND name=?',(kind,name)).fetchone()[0]
        cur=conn.execute('INSERT INTO artifacts(kind,name,version,payload) VALUES (?,?,?,?)',(kind,name,version,json.dumps(payload)))
        return unpack(conn.execute('SELECT * FROM artifacts WHERE id=?',(cur.lastrowid,)).fetchone())
def get(path,id):
    with db(path) as conn:
        row=conn.execute('SELECT * FROM artifacts WHERE id=?',(id,)).fetchone();return unpack(row) if row else None
def artifacts(path):
    with db(path) as conn:return [unpack(r) for r in conn.execute('SELECT * FROM artifacts ORDER BY id DESC')]
def create_run(path,payload):
    with db(path) as conn:
        cur=conn.execute('INSERT INTO runs(status,payload) VALUES (?,?)',('queued',json.dumps(payload)));return cur.lastrowid
def update_run(path,id,status,payload):
    with db(path) as conn:conn.execute('UPDATE runs SET status=?,payload=? WHERE id=?',(status,json.dumps(payload),id))
def runs(path):
    with db(path) as conn:return [unpack(r) for r in conn.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 100')]
def run(path,id):
    with db(path) as conn:
        row=conn.execute('SELECT * FROM runs WHERE id=?',(id,)).fetchone();return unpack(row) if row else None
