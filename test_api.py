import unittest,tempfile,json,base64,datetime
from pathlib import Path
from unittest.mock import patch,Mock
from werkzeug.security import generate_password_hash
from sisgr import measures,signature,synchronize,Client,Erro,APIError
from app import create_app

class Rules(unittest.TestCase):
 def test_vehicle_catalog_avoids_individual_endpoint(self):
  c=Client('test');c.get=Mock(side_effect=[{'data':[{'id':1,'place_number':'AAA1234'},{'id':2,'place_number':'BBB1234'}],'current_page':1,'last_page':1}])
  self.assertEqual(c.detail('/vehicles',1)['place_number'],'AAA1234')
  self.assertEqual(c.detail('/vehicles',2)['place_number'],'BBB1234')
  c.get.assert_called_once_with('/vehicles',{'page':1,'per_page':100})
  self.assertIn('catalogWarning',c.detail('/vehicles',99999))
 def test_vehicle_500_does_not_block_or_repeat_request(self):
  c=Client('test');c.get=Mock(side_effect=APIError(500,'/vehicles'))
  self.assertIn('catalogWarning',c.detail('/vehicles',99991))
  self.assertEqual(c.detail('/vehicles',99992)['id'],99992)
  self.assertEqual(c.get.call_count,2)
 def test_direct_vehicle_fallback_after_500(self):
  c=Client('test');c.get=Mock(side_effect=[APIError(500,'/vehicles'),[{'id':4,'place_number':'ABC1234'}]])
  self.assertEqual(c.detail('/vehicles',4)['place_number'],'ABC1234')
  self.assertEqual(c.get.call_args_list[0].args,('/vehicles',{'page':1,'per_page':100}))
  self.assertEqual(c.get.call_args_list[1].args,('/vehicles',))
 def test_probe_does_not_save_plate_values(self):
  from vehicle_probe import describe
  result=describe([{'id':4,'place_number':'ABC1234','name':'PrivateName'}])
  self.assertEqual(result['placas_reconhecidas'],1)
  self.assertNotIn('ABC1234',json.dumps(result));self.assertNotIn('PrivateName',json.dumps(result))
 def test_vehicle_auth_failure_still_blocks(self):
  c=Client('test');c.get=Mock(side_effect=APIError(401,'/vehicles'))
  with self.assertRaises(APIError):c.detail('/vehicles',4)
 def test_volume_and_duplicate_id(self):
  r={'id':1,'agendamento_id':10,'destination':{'id':2,'measure':12.5},'residue':{'unity':'KG'}}
  amounts,units,errors=measures([r,r],10)
  self.assertEqual(amounts['KG'],12.5);self.assertFalse(errors)
 def test_conflicting_destination_and_missing(self):
  rows=[{'id':i,'agendamento_id':10,'destination':{'id':2,'measure':12},'residue':{'unity':'KG'}} for i in [1,2]]
  values,units,errors=measures(rows,10)
  self.assertTrue(errors);self.assertEqual(units,[]);self.assertEqual(sum(values.values()),0)
  self.assertTrue(measures([],10)[2])
 def test_wrong_link(self):
  with self.assertRaises(Erro):measures([{'id':1,'agendamento_id':11}],10)
 def test_units(self):
  r=lambda id,u,v:{'id':id,'agendamento_id':1,'destination':{'id':id,'measure':v},'residue':{'unity':u}}
  vals,units,err=measures([r(1,'T',1.2),r(2,'L',8)],1)
  self.assertEqual(vals,{'KG':1200.,'L':8.,'M3':0.});self.assertFalse(err)
  self.assertTrue(measures([r(1,'UND',5)],1)[2])
 def test_signature_unknown_and_empty(self):
  self.assertIsNone(signature({}));self.assertFalse(signature({'sign_image':''}));self.assertTrue(signature({'sign_image':'private-image'}))
 def test_pagination_and_repeated_page(self):
  c=Client('test');c.get=Mock(side_effect=[{'data':[{'id':1}],'current_page':1,'last_page':2},{'data':[{'id':2}],'current_page':2,'last_page':2}])
  self.assertEqual(len(c.list('/schedules',{})),2)
  c.get=Mock(return_value=[{'id':1}])
  with self.assertRaises(Erro):c.list('/schedules',{})
 def test_normalize_without_sensitive_fields(self):
  c=Mock();c.list.side_effect=[[{'id':1,'schedule_date':'2026-10-28','generator_id':2,'driver_id':3,'vehicle_id':4,'status':'efetivado','type':'coleta','sign_image':'DO_NOT_SAVE'}],[{'id':5,'agendamento_id':1,'destination':{'id':6,'measure':94},'residue':{'unity':'KG'}}]]
  c.detail.side_effect=[{'id':2,'name':'Ponto','cpf_cnpj':'DO_NOT_SAVE','address':{'city':{'name':'X','state':{'uf':'MT'}}}},{'id':3,'nome':'Motorista','cpf':'DO_NOT_SAVE'},{'id':4,'place_number':'ABC1234'}]
  d=synchronize(c,'2026-10-28','2026-10-28',{'features':[]})
  self.assertEqual(d['rows'][0]['measures']['KG'],94);self.assertNotIn('DO_NOT_SAVE',json.dumps(d))

class Server(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'db.sqlite'
  self.app=create_app({'user':'test','hash':generate_password_hash('test-only-password')},'test-token',self.path);self.client=self.app.test_client()
  self.headers={'Authorization':'Basic '+base64.b64encode(b'test:test-only-password').decode()}
 def tearDown(self):self.tmp.cleanup()
 def test_auth_and_secret(self):
  self.assertEqual(self.client.get('/data.json').status_code,401)
  for url in ['/data.json','/sync/status']:
   r=self.client.get(url,headers=self.headers);self.assertEqual(r.status_code,200);self.assertNotIn(b'test-token',r.data)
  self.assertEqual(self.client.get('/instance/painel.sqlite',headers=self.headers).status_code,404)
 def test_csrf_host_and_period(self):
  self.assertEqual(self.client.post('/sync',json={},headers=self.headers).status_code,403)
  self.assertEqual(self.client.get('/',headers=self.headers,base_url='http://evil.invalid').status_code,403)
  csrf=self.client.get('/sync/status',headers=self.headers).json['csrf']
  r=self.client.post('/sync',headers={**self.headers,'X-CSRF-Token':csrf},json={'start':'2026-01-01','end':'2026-12-31','transporterIds':['5']})
  self.assertEqual(r.status_code,400)
 def test_failed_sync_preserves_database(self):
  import sqlite3
  with sqlite3.connect(self.path) as db:db.execute('INSERT INTO snapshot VALUES(1,?)',(json.dumps({'saved':True}),))
  csrf=self.client.get('/sync/status',headers=self.headers).json['csrf']
  class Immediate:
   def __init__(self,target,**kw):self.target=target
   def start(self):self.target()
  with patch('app.threading.Thread',Immediate),patch('app.synchronize',side_effect=Erro('Simulated failure')):
   self.client.post('/sync',headers={**self.headers,'X-CSRF-Token':csrf},json={'start':'2026-10-28','end':'2026-10-28','transporterIds':['5','6']})
  self.assertEqual(self.client.get('/data.json',headers=self.headers).json,{'saved':True})
  self.assertFalse(self.client.get('/sync/status',headers=self.headers).json['success'])
 def test_successful_commit(self):
  csrf=self.client.get('/sync/status',headers=self.headers).json['csrf']
  class Immediate:
   def __init__(self,target,**kw):self.target=target
   def start(self):self.target()
  with patch('app.threading.Thread',Immediate),patch('app.synchronize',return_value={'rows':[],'meta':{'tested':True}}):
   r=self.client.post('/sync',headers={**self.headers,'X-CSRF-Token':csrf},json={'start':'2026-10-28','end':'2026-10-28','transporterIds':['5','6']})
  self.assertEqual(r.status_code,202);self.assertTrue(self.client.get('/data.json',headers=self.headers).json['meta']['tested'])
class PlateServerTests(Server):
 def test_save_plate_and_remove_override(self):
  import sqlite3
  seed={'rows':[{'id':10,'vehicleId':15,'plate':'Veículo ID 15 · sem placa','plateConfirmed':False}], 'meta':{'quality':[]}}
  with sqlite3.connect(self.path) as db:db.execute('INSERT INTO snapshot VALUES(1,?)',(json.dumps(seed),))
  csrf=self.client.get('/sync/status',headers=self.headers).json['csrf']
  headers={**self.headers,'X-CSRF-Token':csrf}
  result=self.client.post('/vehicles/local',headers=headers,json={'vehicles':[{'id':'15','plate':'ABC1D23'}]})
  self.assertEqual(result.status_code,200)
  data=self.client.get('/data.json',headers=self.headers).json
  self.assertEqual(data['rows'][0]['plate'],'ABC-1D23');self.assertEqual(data['meta']['vehiclePending'],0)
  result=self.client.post('/vehicles/local',headers=headers,json={'vehicles':[{'id':'15','plate':''}]})
  self.assertEqual(result.status_code,200)
  from enrichment import load_vehicle_export
  self.assertEqual(self.client.get('/data.json',headers=self.headers).json['rows'][0]['plate'],load_vehicle_export()['15']['place_number'])
 def test_reject_bad_plate_and_csrf(self):
  self.assertEqual(self.client.post('/vehicles/local',headers=self.headers,json={'vehicles':[]}).status_code,403)
  csrf=self.client.get('/sync/status',headers=self.headers).json['csrf']
  self.assertEqual(self.client.post('/vehicles/local',headers={**self.headers,'X-CSRF-Token':csrf},json={'vehicles':[{'id':'15','plate':'<script>'}]}).status_code,400)

class EnrichmentTests(unittest.TestCase):
 def test_actual_date_uses_realization_and_timezone(self):
  from enrichment import actual_date
  self.assertEqual(actual_date({'schedule_date':'2026-10-01'}),(None,None))
  self.assertEqual(actual_date({'schedule_date':'2026-10-01','end_attendance':'2026-10-29T02:00:00Z'}),('2026-10-28','end_attendance'))
  self.assertEqual(actual_date({'end_attendance':None,'end_at':'2026-10-30 15:00:00'}),('2026-10-30','end_at'))
 def test_plate_source_and_override(self):
  from enrichment import vehicle_plate,plate
  self.assertEqual(vehicle_plate({'place_number':'ABC1234'},{'vehicle_id':15},{}),('ABC-1234','API SISGR'))
  self.assertEqual(vehicle_plate({}, {'vehicle_id':15},{'15':'ABC1D23'}),('ABC-1D23','Cadastro local'))
  self.assertIsNone(plate('Sem placa'))
 def test_mt_regions_cover_sinop(self):
  from app import ROOT
  geo=json.loads((ROOT/'data/geografia.json').read_text(encoding='utf-8'))
  self.assertEqual(len(geo['features']),142)
  sinop=next(f for f in geo['features'] if f['properties']['Cidade']=='Sinop')
  self.assertEqual(sinop['properties']['Regiao'],'Norte')
 def test_transport_filter_and_actual_driver(self):
  c=Mock();c.list.side_effect=[[{'id':1,'transporter_id':5,'schedule_date':'2026-10-28','generator_id':2,'driver_id':3,'motoristaIniciouAtendimento_id':9,'vehicle_id':4,'status':'realizado','type':'coleta','sign_image':'image','end_attendance':'2026-10-29 10:00:00'},{'id':2,'transporter_id':99,'schedule_date':'2026-10-28'}],[{'id':6,'agendamento_id':1,'destination':{'id':7,'measure':245},'residue':{'unity':'KG'}}]]
  c.detail.side_effect=[{'id':2,'name':'Ponto','address':{'city':{'name':'Sinop','state':{'id':51}}}},{'id':3,'nome':'Programado'},{'id':4,'place_number':'ABC1234'},{'id':9,'nome':'Executou'}]
  from app import ROOT
  geo=json.loads((ROOT/'data/geografia.json').read_text(encoding='utf-8'))
  data=synchronize(c,'2026-10-28','2026-10-28',geo,transporter_ids=['5'])
  self.assertEqual(len(data['rows']),1);r=data['rows'][0]
  self.assertEqual(r['actualDriver'],'Executou');self.assertEqual(r['collectionDate'],'2026-10-29');self.assertEqual(r['region'],'Norte')
  self.assertEqual(r['transporterId'],'5')

if __name__=='__main__':unittest.main()

class ExportTests(unittest.TestCase):
 def test_export_fallback_and_quality(self):
  from enrichment import load_vehicle_export,enrich_snapshot
  exported=load_vehicle_export();self.assertEqual(len(exported),72)
  vid='15';d={'rows':[{'id':1,'vehicleId':15,'truckType':'Tipo ID 1'}],'meta':{'quality':[{'id':1,'motivos':['Cadastro de veículos indisponível no SISGR (HTTP 500); placas não confirmadas.','Quantidade/unidade ausente ou inválida']}]}}
  enrich_snapshot(d,exported,{})
  self.assertEqual(d['rows'][0]['plate'],exported[vid]['place_number'])
  self.assertEqual(d['rows'][0]['truckType'],exported[vid]['vehicle_type'])
  self.assertEqual(d['meta']['vehiclePending'],0)
  self.assertEqual(d['meta']['quality'][0]['motivos'],['Quantidade/unidade ausente ou inválida'])
 def test_precedence_and_exact_id(self):
  from enrichment import enrich_snapshot
  exported={'1':{'place_number':'ABC-1234','vehicle_type':'BAU GRANDE','catalogSource':'Exportação SISGR teste'},'2':{'place_number':'ABC-1234','vehicle_type':'BAU PEQUENO','catalogSource':'Exportação SISGR teste'}}
  d={'rows':[{'id':1,'vehicleId':1,'apiPlate':'DEF-1234','truckType':'API TYPE'},{'id':2,'vehicleId':2,'truckType':'Tipo ID 2'}]}
  enrich_snapshot(d,exported,{'1':'GHI1234'})
  self.assertEqual(d['rows'][0]['plate'],'GHI-1234');self.assertEqual(d['rows'][0]['truckType'],'API TYPE')
  self.assertEqual(d['rows'][1]['truckType'],'BAU PEQUENO')
  enrich_snapshot(d,exported,{})
  self.assertEqual(d['rows'][0]['plate'],'DEF-1234')
 def test_500_uses_export(self):
  from enrichment import load_vehicle_export
  c=Client('test');c.get=Mock(side_effect=APIError(500,'/vehicles'))
  self.assertEqual(c.detail('/vehicles',15)['place_number'],load_vehicle_export()['15']['place_number'])
  self.assertEqual(c.get.call_count,2)

class HostedTests(unittest.TestCase):
 def test_render_host_auth_persistence_and_origin(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict('os.environ',{'RENDER':'true','RENDER_EXTERNAL_HOSTNAME':'painel.onrender.com','DATABASE_PATH':str(Path(tmp)/'persistent.sqlite'),'DASHBOARD_USER':'cloud','DASHBOARD_PASSWORD_HASH':generate_password_hash('cloud-test-password')},clear=False):
   a=create_app(token='test');c=a.test_client();h={'Authorization':'Basic '+base64.b64encode(b'cloud:cloud-test-password').decode(),'X-Forwarded-Proto':'https'}
   self.assertEqual(c.get('/health',base_url='https://painel.onrender.com').status_code,200)
   self.assertEqual(c.get('/data.json',base_url='https://painel.onrender.com').status_code,401)
   self.assertEqual(c.get('/data.json',base_url='https://evil.invalid',headers=h).status_code,403)
   status=c.get('/sync/status',base_url='https://painel.onrender.com',headers=h)
   self.assertEqual(status.status_code,200);self.assertIn('Strict-Transport-Security',status.headers)
   h['X-CSRF-Token']=status.json['csrf'];h['Origin']='https://painel.onrender.com'
   self.assertEqual(c.post('/vehicles/local',base_url='https://painel.onrender.com',headers=h,json={'vehicles':[{'id':'15','plate':'ABC1234'}]}).status_code,200)
   c2=create_app(token='test').test_client()
   self.assertEqual(c2.get('/sync/status',base_url='https://painel.onrender.com',headers=h).status_code,200)
   import sqlite3
   with sqlite3.connect(Path(tmp)/'persistent.sqlite') as db:self.assertIn('ABC-1234',db.execute("SELECT payload FROM settings WHERE name='plates'").fetchone()[0])
 def test_update_menu_is_separate(self):
  from app import ROOT
  html=(ROOT/'web/index.html').read_text();css=(ROOT/'web/style.css').read_text()
  self.assertIn('data-view="atualizar"',html)
  self.assertIn('.sync-box{display:none}',css)
  self.assertIn('.view-atualizar .sync-box{display:block}',css)
