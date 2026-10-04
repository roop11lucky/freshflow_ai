from datetime import date, timedelta
import math
from .db import query

def history(ingredient, days=120):
    return query("""SELECT demand_date, qty, source FROM demand_history
                    WHERE ingredient=? AND demand_date >= ?
                    ORDER BY demand_date""",
                 (ingredient,(date.today()-timedelta(days=days)).isoformat()))

def _mae(actual,pred):
    return sum(abs(a-p) for a,p in zip(actual,pred))/len(actual) if actual else 0

def _mape(actual,pred):
    vals=[abs(a-p)/a for a,p in zip(actual,pred) if a]
    return sum(vals)/len(vals)*100 if vals else 0

def evaluate_models(ingredient):
    rows=history(ingredient,120)
    if len(rows)<35:
        return {'selected':'Insufficient history','mae':None,'mape':None,'models':[]}
    vals=[r['qty'] for r in rows]
    dates=[date.fromisoformat(r['demand_date']) for r in rows]
    split=len(vals)-28
    train_vals=vals[:split]; test_vals=vals[split:]; test_dates=dates[split:]
    naive=[]; seasonal=[]
    rolling=list(train_vals)
    # rolling 7-day mean
    for a in test_vals:
        naive.append(sum(rolling[-7:])/min(7,len(rolling)))
        rolling.append(a)
    # weekday seasonal mean from training
    wd={}
    for d,v in zip(dates[:split],train_vals):
        wd.setdefault(d.weekday(),[]).append(v)
    global_mean=sum(train_vals[-28:])/min(28,len(train_vals))
    seasonal=[sum(wd.get(d.weekday(),[global_mean])[-8:])/len(wd.get(d.weekday(),[global_mean])[-8:]) for d in test_dates]
    models=[
      {'model':'7-Day Moving Average','mae':_mae(test_vals,naive),'mape':_mape(test_vals,naive)},
      {'model':'Weekday Seasonal Baseline','mae':_mae(test_vals,seasonal),'mape':_mape(test_vals,seasonal)}
    ]
    best=min(models,key=lambda x:x['mae'])
    return {'selected':best['model'],'mae':best['mae'],'mape':best['mape'],'models':models}

def forecast(ingredient,horizon=7,demand_multiplier=1.0):
    rows=history(ingredient,120)
    if not rows: return []
    ev=evaluate_models(ingredient)
    vals=[r['qty'] for r in rows]
    dates=[date.fromisoformat(r['demand_date']) for r in rows]
    future=[]
    if ev['selected']=='Weekday Seasonal Baseline':
        wd={}
        for d,v in zip(dates,vals): wd.setdefault(d.weekday(),[]).append(v)
        for i in range(1,horizon+1):
            d=date.today()+timedelta(days=i)
            arr=wd.get(d.weekday(),vals[-28:])
            y=sum(arr[-8:])/min(8,len(arr))
            future.append({'date':d.isoformat(),'forecast':y*demand_multiplier})
    else:
        avg=sum(vals[-7:])/min(7,len(vals))
        for i in range(1,horizon+1):
            d=date.today()+timedelta(days=i)
            future.append({'date':d.isoformat(),'forecast':avg*demand_multiplier})
    return future
