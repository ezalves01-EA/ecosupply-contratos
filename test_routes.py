import unittest
from routes import apply_routes,load_routes,UNDEFINED,schedule_week
class RoutesTest(unittest.TestCase):
 def row(self,**kw):
  r=dict(id=1,city='Cuiabá',plate='HTP-0171',date='2026-11-12',state='MT');r.update(kw);apply_routes({'meta':{},'rows':[r]});return r
 def test_catalog(self):
  c=load_routes();self.assertEqual(len(c),74);self.assertEqual(len({r['route'] for r in c}),19)
 def test_boundaries(self):
  for d,w in [(1,1),(7,1),(8,2),(14,2),(15,3),(21,3),(22,4),(30,4)]:self.assertEqual(schedule_week(f'2026-11-{d:02}'),w)
  self.assertIsNone(schedule_week('2026-11-31'))
 def test_capital(self):
  for city,plate in [('Cuiabá','HTP-0171'),('Várzea Grande','HTP-0B45')]:
   for day,w in [(3,1),(12,2),(20,3),(30,4)]:
    r=self.row(city=city,plate=plate,date=f'2026-11-{day:02}');self.assertEqual(r['route'],f'{plate}_{w}');self.assertEqual(r['routeAudit'],'Conforme')
 def test_reschedule_one_id(self):
  r=self.row();self.assertEqual(r['routeWeek'],2);r['date']='2026-11-20';d={'meta':{},'rows':[r]};apply_routes(d);self.assertEqual(len(d['rows']),1);self.assertEqual(r['routeWeek'],3)
 def test_rondon(self):
  for day in (10,24):self.assertEqual(self.row(city='Rondonópolis',plate='DAH-7H63',date=f'2026-11-{day}')['routeAudit'],'Conforme')
  r=self.row(city='Rondonópolis',plate='DAH-7H63',date='2026-11-03');self.assertEqual(r['routeAudit'],'Semana divergente');self.assertEqual(r['plannedWeeks'],[2,4]);self.assertEqual(r['routeWeek'],1)
 def test_fallback_and_unknown(self):
  self.assertEqual(self.row(plate='OTHER')['route'],'HTP-0171_2');r=self.row(city='Outra filial');self.assertEqual(r['route'],UNDEFINED);self.assertEqual(r['routeAudit'],'Sem rota cadastrada')
  self.assertEqual(self.row(state='SP')['route'],UNDEFINED)
 def test_invalid(self):self.assertEqual(self.row(date='errada')['routeAudit'],'Data inválida')
if __name__=='__main__':unittest.main()
