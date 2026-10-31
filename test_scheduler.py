import unittest,tempfile,sqlite3,datetime as dt,json
from pathlib import Path
from unittest.mock import Mock
from scheduler import tick,due_slot
from enrichment import apply_regions
class AutomaticTests(unittest.TestCase):
 def test_brasilia_slots(self):
  for utc,expected in [('2026-10-31T03:00:00+00:00','2026-10-31 00:00'),('2026-10-30T14:00:00+00:00','2026-10-30 11:00'),('2026-10-30T11:00:00+00:00',None),('2026-10-30T14:01:00+00:00',None)]:self.assertEqual(due_slot(dt.datetime.fromisoformat(utc)),expected)
 def test_persistent_claim_and_scope(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'db';now=dt.datetime.fromisoformat('2026-10-30T14:00:00+00:00')
   with sqlite3.connect(p) as db:db.execute('CREATE TABLE settings(name TEXT PRIMARY KEY,payload TEXT)')
   load=lambda:{'meta':{'importedAt':'x','periodStart':'2026-10-01','periodEnd':'2026-10-30','transporterIds':['5','6']}}
   launch=Mock(return_value=True)
   self.assertTrue(tick(p,load,launch,lambda:True,now));self.assertFalse(tick(p,load,launch,lambda:True,now))
   launch.assert_called_once_with('2026-10-01','2026-10-30',['5','6'])
 def test_no_initial_base(self):
  launch=Mock();self.assertFalse(tick('unused',lambda:{},launch,lambda:True,dt.datetime.fromisoformat('2026-10-30T14:00:00+00:00')));launch.assert_not_called()
 def test_nine_regions_and_snapshot_migration(self):
  geo=json.loads((Path(__file__).parent/'data/geografia.json').read_text())
  self.assertEqual(len(geo['features']),142);self.assertEqual(len({f['properties']['Regiao'] for f in geo['features']}),9)
  data={'rows':[{'city':'Sinop','state':'MT','region':'IBGE · Sinop'},{'city':'Sinop','state':'MS','region':'original'}],'geo':{}}
  apply_regions(data,geo);self.assertEqual(data['rows'][0]['region'],'Norte');self.assertEqual(data['rows'][1]['region'],'original');self.assertEqual(data['geo'],geo)
