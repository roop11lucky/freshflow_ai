from datetime import date
from .db import query, execute

def batches(): return query('SELECT * FROM batches WHERE qty > 0 ORDER BY expiry_date')

def status(expiry):
    d=(date.fromisoformat(expiry)-date.today()).days
    if d < 0: return 'Expired'
    if d <= 2: return 'Critical'
    if d <= 7: return 'Expiring Soon'
    return 'Safe'

def days_left(expiry): return (date.fromisoformat(expiry)-date.today()).days

def money_at_risk(days=7):
    return sum(b['qty']*b['unit_cost'] for b in batches() if 0 <= days_left(b['expiry_date']) <= days)

def fefo(ingredient=None):
    rows=batches()
    if ingredient: rows=[b for b in rows if b['ingredient']==ingredient]
    return [b for b in rows if days_left(b['expiry_date']) >= 0]

def add_batch(values):
    execute('INSERT INTO batches(batch_id,ingredient,supplier,qty,initial_qty,unit,unit_cost,received_date,expiry_date) VALUES(?,?,?,?,?,?,?,?,?)',values)

def transact(batch_id, kind, qty, reason=''):
    b=query('SELECT * FROM batches WHERE batch_id=?',(batch_id,))[0]
    if qty <= 0 or qty > b['qty']: raise ValueError('Quantity must be greater than 0 and not exceed available stock.')
    execute('UPDATE batches SET qty=qty-? WHERE batch_id=?',(qty,batch_id))
    execute('INSERT INTO transactions(batch_id,ingredient,type,qty,reason) VALUES(?,?,?,?,?)',(batch_id,b['ingredient'],kind,qty,reason))
