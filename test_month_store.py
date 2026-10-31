import unittest,tempfile,sqlite3,json,datetime as dt
from pathlib import Path
from unittest.mock import patch
from month_store import initialize,save_month,catalog,automatic_scope
class MonthTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'db'
  with sqlite3.connect(self.p) as db:
   db.execute('CREATE TABLE snapshot(id INTEGER PRIMARY KEY,payload TEXT)');db.execute('CREATE TABLE settings(name TEXT PRIMARY KEY,payload TEXT)')
  initialize(self.p)
 def tearDown(self):self.tmp.cleanup()
 def data(self,month,stamp):return {'rows':[{'id':1,'date':month+'-01'}],'meta':{'periodStart':month+'-01','periodEnd':month+'-28','importedAt':stamp,'transporterIds':['5']}}
 def test_history_preserves_current_bytes_timestamp_and_auto_scope(self):
  with patch('month_store.current_month',return_value='2026-11'):
   save_month(self.p,self.data('2026-11','current'),'2026-11-01','2026-11-30',['5'])
   with sqlite3.connect(self.p) as db:before=db.execute("SELECT payload FROM monthly_snapshot WHERE month='2026-11'").fetchone()[0]
   save_month(self.p,self.data('2026-10','history'),'2026-10-01','2026-10-31',['6'])
   save_month(self.p,self.data('2026-10','history2'),'2026-10-01','2026-10-31',['6'])
  with sqlite3.connect(self.p) as db:self.assertEqual(before,db.execute("SELECT payload FROM monthly_snapshot WHERE month='2026-11'").fetchone()[0])
  self.assertEqual(len(catalog(self.p)),2);self.assertEqual(catalog(self.p)[1]['importedAt'],'history2')
  scope=automatic_scope(self.p,dt.datetime.fromisoformat('2026-12-01T03:00:00+00:00'))['meta']
  self.assertEqual(scope['periodStart'],'2026-12-01');self.assertEqual(scope['periodEnd'],'2026-12-31');self.assertEqual(scope['transporterIds'],['5'])
 def test_migration_idempotent_and_cross_month_rejected(self):
  with sqlite3.connect(self.p) as db:db.execute('INSERT INTO snapshot VALUES(1,?)',(json.dumps(self.data('2026-10','legacy')),))
  initialize(self.p);initialize(self.p)
  self.assertEqual(len(catalog(self.p)),1);self.assertEqual(catalog(self.p)[0]['importedAt'],'legacy')
  with self.assertRaises(ValueError):save_month(self.p,{},'2026-10-01','2026-11-01',['5'])

class FortnightTests(unittest.TestCase):
 def part(self,rows,stamp):return {'rows':[{'id':i,'date':d,'measures':{'KG':kg},'signature':True,'plateConfirmed':True} for i,d,kg in rows],'meta':{'importedAt':stamp,'quality':[]}}
 def test_halves_union_replaces_only_target_and_recounts(self):
  from month_store import merge_period
  first=self.part([(1,'2026-10-01',10),(2,'2026-10-15',20)],'2026-11-01T10:00:00Z')
  d=merge_period({},first,'2026-10-01','2026-10-15',['5'])
  self.assertFalse(d['meta']['monthComplete']);self.assertEqual([h['complete'] for h in d['meta']['fortnights']],[True,False])
  second=self.part([(3,'2026-10-16',30),(4,'2026-10-31',40)],'2026-11-01T11:00:00Z')
  d=merge_period(d,second,'2026-10-16','2026-10-31',['5'])
  preserved=d['rows'][2:];self.assertTrue(d['meta']['monthComplete'])
  newer=self.part([(1,'2026-10-01',15)],'2026-11-01T12:00:00Z')
  d=merge_period(d,newer,'2026-10-01','2026-10-15',['5'])
  self.assertEqual([r['id'] for r in d['rows']],[1,3,4]);self.assertEqual(d['rows'][1:],preserved)
  self.assertEqual(sum(r['measures']['KG'] for r in d['rows']),85)
  self.assertEqual(d['meta']['fortnights'][1]['lastUpdated'],'2026-11-01T11:00:00Z')
 def test_empty_success_removes_only_selected_half(self):
  from month_store import merge_period
  d=merge_period({},self.part([(1,'2026-02-15',1),(2,'2026-02-16',2)],'x'),'2026-02-01','2026-02-28',['5'])
  d=merge_period(d,self.part([],'y'),'2026-02-01','2026-02-15',['5'])
  self.assertEqual([r['id'] for r in d['rows']],[2]);self.assertTrue(d['meta']['monthComplete'])
 def test_id_moved_within_month_deduplicates(self):
  from month_store import merge_period
  d=merge_period({},self.part([(1,'2026-10-02',1)],'a'),'2026-10-01','2026-10-15',['5'])
  d=merge_period(d,self.part([(1,'2026-10-18',2)],'b'),'2026-10-16','2026-10-31',['5'])
  self.assertEqual(len(d['rows']),1);self.assertEqual(d['rows'][0]['date'],'2026-10-18')
 def test_wrong_date_and_duplicate_rejected(self):
  from month_store import merge_period
  for rows in [[(1,'2026-10-16',1)],[(1,'2026-10-01',1),(1,'2026-10-02',1)]]:
   with self.assertRaises(ValueError):merge_period({},self.part(rows,'a'),'2026-10-01','2026-10-15',['5'])
