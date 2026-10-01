from datetime import date, datetime, timedelta
from .db import query, execute, connect


def batches(include_zero=False):
    where = '' if include_zero else 'WHERE qty > 0'
    return query(f'SELECT * FROM batches {where} ORDER BY expiry_date, ingredient')


def status(expiry):
    d = days_left(expiry)
    if d < 0: return 'Expired'
    if d <= 1: return 'Critical'
    if d <= 3: return 'High Risk'
    if d <= 7: return 'Expiring Soon'
    return 'Safe'


def days_left(expiry):
    return (date.fromisoformat(expiry) - date.today()).days


def money_at_risk(days=7):
    return sum(b['qty'] * b['unit_cost'] for b in batches() if 0 <= days_left(b['expiry_date']) <= days)


def inventory_value():
    return sum(b['qty'] * b['unit_cost'] for b in batches())


def fefo(ingredient=None, include_expired=False):
    rows = batches()
    if ingredient:
        rows = [b for b in rows if b['ingredient'] == ingredient]
    if not include_expired:
        rows = [b for b in rows if days_left(b['expiry_date']) >= 0]
    return sorted(rows, key=lambda b: (b['expiry_date'], b['received_date'], b['batch_id']))


def add_batch(values):
    execute('INSERT INTO batches(batch_id,ingredient,supplier,qty,initial_qty,unit,unit_cost,received_date,expiry_date) VALUES(?,?,?,?,?,?,?,?,?)', values)


def transact(batch_id, kind, qty, reason=''):
    b = query('SELECT * FROM batches WHERE batch_id=?', (batch_id,))[0]
    if qty <= 0 or qty > b['qty']:
        raise ValueError('Quantity must be greater than 0 and not exceed available stock.')
    execute('UPDATE batches SET qty=qty-? WHERE batch_id=?', (qty, batch_id))
    execute('INSERT INTO transactions(batch_id,ingredient,type,qty,reason) VALUES(?,?,?,?,?)', (batch_id, b['ingredient'], kind, qty, reason))


def consume_fefo(ingredient, qty):
    rows = fefo(ingredient)
    available = sum(b['qty'] for b in rows)
    if qty <= 0:
        raise ValueError('Quantity must be greater than 0.')
    if qty > available:
        raise ValueError(f'Only {available:g} available across usable FEFO batches.')
    remaining = qty
    allocations = []
    with connect() as c:
        for b in rows:
            if remaining <= 0:
                break
            used = min(remaining, b['qty'])
            c.execute('UPDATE batches SET qty=qty-? WHERE batch_id=?', (used, b['batch_id']))
            c.execute('INSERT INTO transactions(batch_id,ingredient,type,qty,reason) VALUES(?,?,?,?,?)',
                      (b['batch_id'], ingredient, 'Consumption', used, 'Auto-allocated by FEFO'))
            allocations.append({'batch_id': b['batch_id'], 'qty': used, 'unit': b['unit'], 'expiry_date': b['expiry_date']})
            remaining -= used
        c.commit()
    return allocations


def transaction_history(limit=100):
    return query('''SELECT t.id,t.created_at,t.type,t.ingredient,t.batch_id,t.qty,t.reason,b.unit,b.unit_cost,
                           t.qty*b.unit_cost AS value
                    FROM transactions t LEFT JOIN batches b ON t.batch_id=b.batch_id
                    ORDER BY t.id DESC LIMIT ?''', (limit,))


def waste_value(days=None):
    sql = "SELECT COALESCE(SUM(t.qty*b.unit_cost),0) v FROM transactions t JOIN batches b ON t.batch_id=b.batch_id WHERE t.type='Waste'"
    args = ()
    if days:
        sql += " AND datetime(t.created_at) >= datetime('now', ?)"
        args = (f'-{int(days)} days',)
    return query(sql, args)[0]['v'] or 0


def consumption_value(days=None):
    sql = "SELECT COALESCE(SUM(t.qty*b.unit_cost),0) v FROM transactions t JOIN batches b ON t.batch_id=b.batch_id WHERE t.type='Consumption'"
    args = ()
    if days:
        sql += " AND datetime(t.created_at) >= datetime('now', ?)"
        args = (f'-{int(days)} days',)
    return query(sql, args)[0]['v'] or 0


def dashboard_summary():
    rows = batches()
    expiring3 = [b for b in rows if 0 <= days_left(b['expiry_date']) <= 3]
    expired = [b for b in rows if days_left(b['expiry_date']) < 0]
    waste30 = waste_value(30)
    consumed30 = consumption_value(30)
    denominator = waste30 + consumed30
    return {
        'inventory_value': inventory_value(),
        'money_at_risk_7d': money_at_risk(7),
        'expiring_3d': len(expiring3),
        'expired_batches': len(expired),
        'expired_value': sum(b['qty']*b['unit_cost'] for b in expired),
        'waste_30d': waste30,
        'waste_pct_30d': (waste30 / denominator * 100) if denominator else 0,
        'active_batches': len(rows),
        'fefo_actions': len(set(b['ingredient'] for b in expiring3)),
    }
