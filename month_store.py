"""Independent monthly snapshots; only successful syncs replace a partition."""
import calendar,datetime as dt,json,sqlite3
from zoneinfo import ZoneInfo

def month_bounds(month):
    first=dt.date.fromisoformat(month+'-01')
    return first.isoformat(),first.replace(day=calendar.monthrange(first.year,first.month)[1]).isoformat()

def current_month(now=None):return (now or dt.datetime.now(ZoneInfo('America/Sao_Paulo'))).strftime('%Y-%m')

def initialize(path):
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS monthly_snapshot(month TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        old=db.execute('SELECT payload FROM snapshot WHERE id=1').fetchone()
        if old and not db.execute('SELECT 1 FROM monthly_snapshot LIMIT 1').fetchone():
            data=json.loads(old[0]);meta=data.get('meta',{})
            if meta.get('periodStart'):
                months={r['date'][:7] for r in data.get('rows',[]) if r.get('date')} or {meta['periodStart'][:7]}
                for month in months:
                    piece={**data,'rows':[r for r in data.get('rows',[]) if r.get('date','')[:7]==month], 'meta':{**meta,'periodStart':max(month_bounds(month)[0],meta['periodStart']),'periodEnd':min(month_bounds(month)[1],meta['periodEnd'])}}
                    db.execute('INSERT INTO monthly_snapshot VALUES(?,?)',(month,json.dumps(piece,ensure_ascii=False)))
                if meta.get('transporterIds'):db.execute("INSERT OR IGNORE INTO settings VALUES('auto_transporters',?)",(json.dumps(meta['transporterIds']),))

def merge_period(old,data,start,end,transporters):
    """Replace only the queried schedule dates; preserve other dates verbatim."""
    first,last=month_bounds(start[:7])
    if start[:7]!=end[:7] or not first<=start<=end<=last:raise ValueError('Período inválido.')
    incoming=data.get('rows',[])
    if any(not start<=r.get('date','')<=end for r in incoming):raise ValueError('Agendamento fora do período solicitado.')
    ids=[str(r['id']) for r in incoming]
    if len(ids)!=len(set(ids)):raise ValueError('ID de agendamento duplicado.')
    retained=[r for r in old.get('rows',[]) if not start<=r.get('date','')<=end and str(r['id']) not in set(ids)]
    rows=sorted(retained+incoming,key=lambda r:(r.get('date',''),str(r['id'])))
    previous=old.get('meta',{});meta={**previous,**data.get('meta',{})}
    coverage=dict(previous.get('dateCoverage',{}))
    if not coverage and previous.get('importedAt') and previous.get('periodStart'):
        cursor=dt.date.fromisoformat(max(first,previous['periodStart']));stop=dt.date.fromisoformat(min(last,previous['periodEnd']))
        while cursor<=stop:
            coverage[cursor.isoformat()]={'importedAt':previous['importedAt'],'transporterIds':previous.get('transporterIds',[])};cursor+=dt.timedelta(days=1)
    cursor=dt.date.fromisoformat(start);stop=dt.date.fromisoformat(end)
    while cursor<=stop:
        coverage[cursor.isoformat()]={'importedAt':meta.get('importedAt'),'transporterIds':transporters};cursor+=dt.timedelta(days=1)
    retained_ids={str(r['id']) for r in retained}
    quality=[q for q in previous.get('quality',[]) if str(q.get('id')) in retained_ids]+data.get('meta',{}).get('quality',[])
    halves=[]
    for label,lo,hi in [('1ª quinzena',first,first[:8]+'15'),('2ª quinzena',first[:8]+'16',last)]:
        dates=[(dt.date.fromisoformat(lo)+dt.timedelta(days=n)).isoformat() for n in range((dt.date.fromisoformat(hi)-dt.date.fromisoformat(lo)).days+1)]
        known=[coverage[d] for d in dates if d in coverage]
        halves.append({'label':label,'complete':len(known)==len(dates),'daysLoaded':len(known),'daysTotal':len(dates),'lastUpdated':max((d.get('importedAt') or '' for d in known),default=None)})
    meta.update(periodStart=first,periodEnd=last,dateCoverage=coverage,fortnights=halves,monthComplete=all(h['complete'] for h in halves),quality=quality,
        transporterIds=sorted({str(t) for d in coverage.values() for t in d.get('transporterIds',[])}),
        sourceRows=sum(r.get('sourceRows',0) for r in rows),volumePending=sum(bool(r.get('volumeIssues')) for r in rows),signatureUnknown=sum(r.get('signature') is None for r in rows),vehiclePending=sum(not r.get('plateConfirmed') for r in rows))
    return {**old,**data,'rows':rows,'meta':meta}

def save_month(path,data,start,end,transporters):
    month=start[:7]
    if month!=end[:7]:raise ValueError('Escolha um único mês por atualização.')
    with sqlite3.connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        previous=db.execute('SELECT payload FROM monthly_snapshot WHERE month=?',(month,)).fetchone()
        merged=merge_period(json.loads(previous[0]) if previous else {},data,start,end,transporters)
        db.execute('INSERT INTO monthly_snapshot VALUES(?,?) ON CONFLICT(month) DO UPDATE SET payload=excluded.payload',(month,json.dumps(merged,ensure_ascii=False,allow_nan=False)))
        if month==current_month() or not db.execute("SELECT 1 FROM settings WHERE name='auto_transporters'").fetchone():
            db.execute("INSERT INTO settings VALUES('auto_transporters',?) ON CONFLICT(name) DO UPDATE SET payload=excluded.payload",(json.dumps(transporters),))

def catalog(path):
    with sqlite3.connect(path) as db:items=db.execute('SELECT month,payload FROM monthly_snapshot ORDER BY month DESC').fetchall()
    return [{'month':m,**{k:json.loads(p).get('meta',{}).get(k) for k in ['periodStart','periodEnd','importedAt','fortnights','monthComplete']}} for m,p in items]

def automatic_scope(path,now):
    with sqlite3.connect(path) as db:r=db.execute("SELECT payload FROM settings WHERE name='auto_transporters'").fetchone()
    if not r:return {}
    start,end=month_bounds(now.astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%Y-%m'))
    return {'meta':{'importedAt':'configured','periodStart':start,'periodEnd':end,'transporterIds':json.loads(r[0])}}
