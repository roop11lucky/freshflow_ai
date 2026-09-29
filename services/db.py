import sqlite3
from pathlib import Path
from datetime import date, timedelta

DB = Path(__file__).resolve().parents[1] / 'data' / 'freshflow.db'

def connect():
    DB.parent.mkdir(exist_ok=True)
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS batches(
          id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id TEXT UNIQUE, ingredient TEXT,
          supplier TEXT, qty REAL, initial_qty REAL, unit TEXT, unit_cost REAL,
          received_date TEXT, expiry_date TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS transactions(
          id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id TEXT, ingredient TEXT,
          type TEXT, qty REAL, reason TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        ''')
        if c.execute('SELECT COUNT(*) FROM batches').fetchone()[0] == 0:
            today=date.today()
            rows=[
              ('CH-102','Chicken Breast','ABC Foods',12,12,'kg',400,today.isoformat(),(today+timedelta(days=2)).isoformat()),
              ('CH-101','Chicken Breast','ABC Foods',16,16,'kg',400,(today-timedelta(days=1)).isoformat(),(today+timedelta(days=5)).isoformat()),
              ('PN-201','Paneer','Fresh Dairy',18,18,'kg',330,today.isoformat(),(today+timedelta(days=4)).isoformat()),
              ('RC-301','Basmati Rice','Grain House',25,25,'kg',95,(today-timedelta(days=4)).isoformat(),(today+timedelta(days=45)).isoformat()),
              ('CR-401','Fresh Cream','Fresh Dairy',8,8,'L',240,today.isoformat(),(today+timedelta(days=1)).isoformat())]
            c.executemany('INSERT INTO batches(batch_id,ingredient,supplier,qty,initial_qty,unit,unit_cost,received_date,expiry_date) VALUES(?,?,?,?,?,?,?,?,?)',rows)

def query(sql,args=()):
    with connect() as c: return [dict(x) for x in c.execute(sql,args).fetchall()]

def execute(sql,args=()):
    with connect() as c: c.execute(sql,args); c.commit()
