import sqlite3
from pathlib import Path
from datetime import date, timedelta

DB = Path(__file__).resolve().parents[1] / 'data' / 'freshflow.db'


def connect():
    DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
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
            today = date.today()
            seed = [
              ('CH-102','Chicken Breast','Coastal Proteins',12,12,'kg',400,today.isoformat(),(today+timedelta(days=1)).isoformat()),
              ('CH-101','Chicken Breast','Coastal Proteins',16,16,'kg',400,(today-timedelta(days=1)).isoformat(),(today+timedelta(days=5)).isoformat()),
              ('CH-099','Chicken Breast','Fresh Farms',5,5,'kg',390,(today-timedelta(days=5)).isoformat(),(today-timedelta(days=1)).isoformat()),
              ('PN-201','Paneer','Fresh Dairy',18,18,'kg',330,today.isoformat(),(today+timedelta(days=3)).isoformat()),
              ('PN-198','Paneer','Fresh Dairy',8,8,'kg',325,(today-timedelta(days=2)).isoformat(),(today+timedelta(days=1)).isoformat()),
              ('ML-110','Milk','Fresh Dairy',24,24,'L',62,today.isoformat(),(today+timedelta(days=2)).isoformat()),
              ('CR-401','Fresh Cream','Fresh Dairy',8,8,'L',240,today.isoformat(),(today+timedelta(days=1)).isoformat()),
              ('CD-120','Curd','Fresh Dairy',15,15,'kg',95,today.isoformat(),(today+timedelta(days=5)).isoformat()),
              ('FS-501','Fish Fillet','Harbour Seafoods',10,10,'kg',520,today.isoformat(),(today+timedelta(days=2)).isoformat()),
              ('MT-210','Mutton','Prime Meats',14,14,'kg',780,today.isoformat(),(today+timedelta(days=4)).isoformat()),
              ('EG-310','Eggs','Farm Basket',180,180,'units',7,today.isoformat(),(today+timedelta(days=12)).isoformat()),
              ('TM-601','Tomato','Green Basket',30,30,'kg',42,today.isoformat(),(today+timedelta(days=4)).isoformat()),
              ('ON-610','Onion','Green Basket',45,45,'kg',38,today.isoformat(),(today+timedelta(days=18)).isoformat()),
              ('CP-620','Capsicum','Green Basket',12,12,'kg',90,today.isoformat(),(today+timedelta(days=5)).isoformat()),
              ('CO-630','Coriander','Green Basket',6,6,'kg',110,today.isoformat(),(today+timedelta(days=2)).isoformat()),
              ('PT-640','Potato','Green Basket',50,50,'kg',34,today.isoformat(),(today+timedelta(days=25)).isoformat()),
              ('RC-301','Basmati Rice','Grain House',50,50,'kg',95,(today-timedelta(days=4)).isoformat(),(today+timedelta(days=90)).isoformat()),
              ('AT-701','Atta','Grain House',40,40,'kg',48,today.isoformat(),(today+timedelta(days=75)).isoformat()),
              ('DL-710','Toor Dal','Grain House',25,25,'kg',155,today.isoformat(),(today+timedelta(days=120)).isoformat()),
              ('OI-801','Cooking Oil','Metro Supplies',30,30,'L',145,today.isoformat(),(today+timedelta(days=150)).isoformat()),
              ('FF-901','French Fries','Frozen Hub',20,20,'kg',175,today.isoformat(),(today+timedelta(days=60)).isoformat()),
              ('FP-910','Frozen Peas','Frozen Hub',15,15,'kg',130,today.isoformat(),(today+timedelta(days=80)).isoformat()),
            ]
            c.executemany('INSERT INTO batches(batch_id,ingredient,supplier,qty,initial_qty,unit,unit_cost,received_date,expiry_date) VALUES(?,?,?,?,?,?,?,?,?)', seed)
            # Seed a few operational events so charts are meaningful from first launch.
            tx = [
              ('TM-601','Tomato','Waste',2.5,'Spoiled'),
              ('CH-102','Chicken Breast','Consumption',3.0,'Auto-allocated by FEFO'),
              ('PN-198','Paneer','Consumption',2.0,'Auto-allocated by FEFO'),
              ('CO-630','Coriander','Waste',0.6,'Prep waste'),
              ('ML-110','Milk','Consumption',4.0,'Auto-allocated by FEFO'),
            ]
            c.executemany('INSERT INTO transactions(batch_id,ingredient,type,qty,reason) VALUES(?,?,?,?,?)', tx)
            # Reflect seeded events in stock.
            for bid, _, typ, qty, _ in tx:
                c.execute('UPDATE batches SET qty=qty-? WHERE batch_id=?', (qty, bid))


def query(sql,args=()):
    with connect() as c:
        return [dict(x) for x in c.execute(sql,args).fetchall()]


def execute(sql,args=()):
    with connect() as c:
        c.execute(sql,args)
        c.commit()
