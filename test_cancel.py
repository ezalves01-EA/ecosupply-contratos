import unittest
from sisgr import is_canceled
from routes import apply_routes
class CancelTests(unittest.TestCase):
 def test_true_and_false(self):
  for v in [True,1,'1','true','SIM','s']:self.assertTrue(is_canceled({'canceled':v}))
  for v in [False,0,'0','false','Não',None,'']:self.assertFalse(is_canceled({'canceled':v,'status':'ROTA'}))
 def test_status_and_date(self):
  self.assertTrue(is_canceled({'status':'cancelado'}));self.assertTrue(is_canceled({'canceled_at':'2026-11-04'}))
 def test_old_snapshot_and_audit(self):
  r={'id':1,'status':'ROTA','canceled':True,'city':'Cuiabá','plate':'HTP-0171','date':'2026-11-12'}
  d={'meta':{},'rows':[r]};apply_routes(d);self.assertEqual(len(d['rows']),1);self.assertEqual(r['status'],'CANCELADO');self.assertEqual(r['originalStatus'],'ROTA');self.assertEqual(r['routeAudit'],'Cancelado — fora da auditoria')

 def test_false_string_keeps_active(self):
  r={'id':2,'canceled':'false','status':'ROTA','city':'Cuiabá','plate':'HTP-0171','date':'2026-11-12'}
  apply_routes({'meta':{},'rows':[r]});self.assertIs(r['canceled'],False);self.assertEqual(r['routeAudit'],'Conforme')
