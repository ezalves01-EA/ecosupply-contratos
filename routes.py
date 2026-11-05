"""Associação de roteiros e auditoria pela data de agendamento."""
import json,unicodedata
from datetime import date
from sisgr import is_canceled
from pathlib import Path
UNDEFINED='Rota a definir'
AMBIGUOUS='Rota a confirmar'
def norm(value):return ''.join(c for c in unicodedata.normalize('NFD',str(value or '')).upper() if c.isalnum())
def load_routes():return json.loads((Path(__file__).parent/'data/rotas_planejadas.json').read_text(encoding='utf-8'))['rows']
def schedule_week(value):
    try:return min(4,(date.fromisoformat(str(value)[:10]).day-1)//7+1)
    except (ValueError,TypeError):return None
def apply_routes(data):
    catalog=load_routes()
    for row in data.get('rows',[]):
        if is_canceled(row):
            row.setdefault('originalStatus',row.get('status'))
            row['canceled']=True;row['status']='CANCELADO'
        else:
            row['canceled']=False
        row['sisgrRouteFilter']=str(row.get('sisgrRoute') or '').strip() or 'Sem identificador de rota'
        row['scheduleWeekFilter']='Semana '+str(schedule_week(row.get('date'))) if schedule_week(row.get('date')) else 'Sem semana'
        city=[c for c in catalog if norm(c['city'])==norm(row.get('city'))]
        state=norm(row.get('state'))
        if state:
            uf={'MATOGROSSO':'MT','51':'MT','RONDONIA':'RO','11':'RO'}.get(state,state)
            city=[c for c in city if norm(c['uf'])==uf]
        exact=[c for c in city if norm(c['truck'])==norm(row.get('plate'))]
        candidates=exact or city
        row['routeSource']='Cidade + placa' if exact else 'Cidade' if city else 'Sem cadastro'
        week=schedule_week(row.get('date'));row['scheduleWeek']=week;row['routeWeek']=week
        expected=sorted({int(c['week']) for c in candidates});row['plannedWeeks']=expected
        row['plannedRoutes']=sorted({c['route'] for c in candidates})
        families=sorted({c['truck'] for c in candidates})
        dated=[c for c in candidates if c['week']==week]
        dated_families=sorted({c['truck'] for c in dated})
        family=families[0] if len(families)==1 else dated_families[0] if len(dated_families)==1 else None
        row['route']=f'{family}_{week}' if family and week else AMBIGUOUS if candidates else UNDEFINED
        row['routeCandidates']=[row['route']] if family and week else sorted({c['route'] for c in dated})
        row['routeAudit']='Cancelado — fora da auditoria' if row.get('canceled') else 'Data inválida' if week is None else 'Sem rota cadastrada' if not candidates else 'Semana divergente' if week not in expected else 'Rota ambígua' if family is None else 'Conforme'
    if isinstance(data.get('meta'),dict):
        data['routeCatalog']=catalog
        data['meta']['routeUndefined']=sum(r['route']==UNDEFINED for r in data.get('rows',[]))
        data['meta']['routeAmbiguous']=sum(r['route']==AMBIGUOUS for r in data.get('rows',[]))
    return data
