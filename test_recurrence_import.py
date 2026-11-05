import io,unittest
from recurrence_import import parse_recurrences
class RecurrenceImportTests(unittest.TestCase):
 def test_csv_manual_auto(self):
  d=parse_recurrences('ID da recorrência;Identificador da rota\n3910;\n3911;HTP-0145_2\n'.encode(),'a.csv')
  self.assertTrue(d['valid']);self.assertEqual(d['items'][0]['requestedRoute'],None);self.assertEqual(d['items'][1]['requestedRoute'],'HTP-0145_2')
 def test_duplicates_reject_all(self):
  d=parse_recurrences(b'3910;A\n3910;B','a.csv');self.assertFalse(d['valid']);self.assertFalse(d['items'])
 def test_invalid_extra_and_limit(self):
  for txt in ['abc;A','3910;A;extra','\n','\n'.join(f'{i};' for i in range(1,102))]:self.assertFalse(parse_recurrences(txt.encode(),'a.csv')['valid'])
 def test_xlsx_and_formula(self):
  from openpyxl import Workbook
  w=Workbook();w.active.append(['ID','Rota']);w.active.append([3910,None]);b=io.BytesIO();w.save(b)
  self.assertEqual(parse_recurrences(b.getvalue(),'a.xlsx')['items'][0]['id'],'3910')
  w.active['B2']='="ABC"';b=io.BytesIO();w.save(b)
  with self.assertRaises(ValueError):parse_recurrences(b.getvalue(),'a.xlsx')
 def test_bad_type(self):
  with self.assertRaises(ValueError):parse_recurrences(b'3910;','a.xls')

class RecurrenceImportEndpointTests(unittest.TestCase):
 def test_authenticated_import_and_template(self):
  import tempfile,base64
  from pathlib import Path
  from app import create_app
  from werkzeug.security import generate_password_hash
  with tempfile.TemporaryDirectory() as folder:
   app=create_app({'user':'test','hash':generate_password_hash('test')},'test-token',Path(folder)/'db.sqlite');client=app.test_client();headers={'Authorization':'Basic '+base64.b64encode(b'test:test').decode()}
   self.assertEqual(client.post('/recurrences/import').status_code,401)
   r=client.post('/recurrences/import',headers=headers,data={'file':(io.BytesIO(b'3910;\n3911;HTP-0145_2'),'a.csv')})
   self.assertEqual(r.status_code,200);self.assertTrue(r.json['valid']);self.assertEqual(r.json['items'][0]['requestedRoute'],None)
   self.assertEqual(client.get('/recurrences-template.csv',headers=headers).status_code,200)
   r=client.post('/recurrences/import',headers=headers,data={'file':(io.BytesIO(b'3910;' + b'A'*5000),'a.csv')});self.assertEqual(r.status_code,200);self.assertFalse(r.json['valid'])
