"""Painel de programação Ecosupply. Python 3.11+."""
import getpass
import json
import os
import sqlite3
import threading
import secrets
import datetime as dt
from month_store import initialize,save_month,catalog,automatic_scope,current_month
from sisgr import Client, synchronize, Erro
from enrichment import plate, TRANSPORTERS, load_vehicle_export, enrich_snapshot, apply_regions
from pathlib import Path
from flask import Flask, Response, jsonify, request, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parent
AUTH_FILE = ROOT / 'instance' / 'auth.json'

def create_app(auth=None, token=None, db_path=None):
    app = Flask(__name__, static_folder=None)
    app.config['MAX_CONTENT_LENGTH']=4096
    token=token or os.environ.get('SISGR_TOKEN','').strip()
    db_path=Path(db_path or os.environ.get('DATABASE_PATH') or ROOT/'instance'/'painel.sqlite')
    hosted=bool(os.environ.get('RENDER'))
    allowed_hosts={'127.0.0.1','localhost'} | {h.strip() for h in os.environ.get('ALLOWED_HOSTS','').split(',') if h.strip()}
    if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):allowed_hosts.add(os.environ['RENDER_EXTERNAL_HOSTNAME'])
    if hosted:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
    db_path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(db_path) as db:db.execute('CREATE TABLE IF NOT EXISTS snapshot (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
    with sqlite3.connect(db_path) as db:db.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    initialize(db_path)
    def plate_map():
        with sqlite3.connect(db_path) as db:row=db.execute("SELECT payload FROM settings WHERE name='plates'").fetchone()
        return json.loads(row[0]) if row else {}
    csrf=secrets.token_urlsafe(32)
    lock=threading.Lock()
    state={'running':False,'message':'Pronto para sincronizar.','success':None}
    geo=json.loads((ROOT/'data'/'geografia.json').read_text(encoding='utf-8'))
    def load(month=None):
        items=catalog(db_path)
        selected=month or (current_month() if any(x['month']==current_month() for x in items) else items[0]['month'] if items else None)
        with sqlite3.connect(db_path) as db:
            row=db.execute('SELECT payload FROM monthly_snapshot WHERE month=?',(selected,)).fetchone()
            if not items and not month:row=db.execute('SELECT payload FROM snapshot WHERE id=1').fetchone()
        if row:
            data=apply_regions(enrich_snapshot(json.loads(row[0]),load_vehicle_export(),plate_map()),geo)
            if 'meta' in data:data['meta'].update(months=items,selectedMonth=selected,currentMonth=current_month())
            return data
        today=dt.datetime.now(dt.timezone(dt.timedelta(hours=-4))).date().isoformat()
        return {'rows':[],'geo':geo,'meta':{'schemaVersion':4,'source':'API SISGR · aguardando primeira sincronização','sourceRows':0,'periodStart':today,'periodEnd':today,'quality':[],'volumePending':0,'signatureUnknown':0,'months':items,'selectedMonth':selected,'currentMonth':current_month()}}

    if auth is None:
        if os.environ.get('DASHBOARD_USER') and os.environ.get('DASHBOARD_PASSWORD_HASH'):
            auth = {'user': os.environ['DASHBOARD_USER'], 'hash': os.environ['DASHBOARD_PASSWORD_HASH']}
        elif not hosted and AUTH_FILE.exists():
            auth = json.loads(AUTH_FILE.read_text(encoding='utf-8'))
        else:
            auth = {}

    @app.before_request
    def authenticate():
        if request.host.split(':')[0] not in allowed_hosts:
            return Response('Host não autorizado.',403)
        if request.path == '/health':
            return None
        if not auth.get('user') or not auth.get('hash'):
            return Response('Configure o acesso executando python app.py.', 503)
        supplied = request.authorization
        if not supplied or supplied.type != 'basic' or supplied.username != auth['user'] or not check_password_hash(auth['hash'], supplied.password or ''):
            return Response('Autenticação necessária.', 401, {'WWW-Authenticate': 'Basic realm="Ecosupply", charset="UTF-8"'})

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        if hosted:response.headers['Strict-Transport-Security']='max-age=31536000'
        return response

    @app.get('/health')
    def health():
        return jsonify(status='ok')

    @app.get('/')
    def index():
        return send_from_directory(ROOT / 'web', 'index.html')

    @app.get('/app.js')
    def script():
        return send_from_directory(ROOT / 'web', 'app.js')

    @app.get('/driver_metrics.js')
    def driver_metrics():
        return send_from_directory(ROOT / 'web', 'driver_metrics.js')

    @app.get('/completion.js')
    def completion():
        return send_from_directory(ROOT / 'web', 'completion.js')

    @app.get('/style.css')
    def style():
        return send_from_directory(ROOT / 'web', 'style.css')

    @app.get('/data.json')
    def data():
        month=request.args.get('month')
        if month:
            try:
                from month_store import month_bounds
                month_bounds(month)
            except ValueError:return jsonify(error='Mês inválido.'),400
        return jsonify(load(month))

    @app.get('/sync/status')
    def sync_status():
        with lock:copy=dict(state)
        return jsonify(**copy,csrf=csrf,configured=bool(token),version='1.10',automatic=os.environ.get('AUTO_SYNC','0')=='1',schedule='00h e 11h · Brasília',autoPeriod='Mês corrente de Brasília; histórico manual separado')

    @app.get('/vehicles/local')
    def vehicle_local():
        data=load();mapping=plate_map();found={}
        for r in data.get('rows',[]):
            vid=r.get('vehicleId')
            if vid is None:continue
            found[str(vid)]={'id':str(vid),'referencePlate':r.get('referencePlate') or '', 'referenceSource':r.get('referencePlateSource',''), 'localPlate':mapping.get(str(vid),'')}
        return jsonify(vehicles=sorted(found.values(),key=lambda r:int(r['id']) if r['id'].isdigit() else 0))

    @app.post('/vehicles/local')
    def save_vehicle_local():
        if not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),csrf):return jsonify(error='Recarregue a página.'),403
        if request.headers.get('Origin') and request.headers['Origin']!=request.host_url.rstrip('/'):return jsonify(error='Origem inválida.'),403
        changes=(request.get_json(silent=True) or {}).get('vehicles')
        if not isinstance(changes,list) or len(changes)>100:return jsonify(error='Lista de placas inválida.'),400
        mapping=plate_map()
        for item in changes:
            if not isinstance(item,dict) or not str(item.get('id','')).isdigit():return jsonify(error='ID inválido.'),400
            raw=item.get('plate','')
            if not isinstance(raw,str) or (raw.strip() and not plate(raw)):return jsonify(error='Placa inválida. Use AAA-1234 ou AAA-1A23.'),400
            if raw.strip():mapping[str(item['id'])]=plate(raw)
            else:mapping.pop(str(item['id']),None)
        with lock:
            if state['running']:return jsonify(error='Aguarde a sincronização terminar.'),409
            data=load()
            data=enrich_snapshot(data,load_vehicle_export(),mapping)
            with sqlite3.connect(db_path) as db:
                db.execute("INSERT INTO settings VALUES('plates',?) ON CONFLICT(name) DO UPDATE SET payload=excluded.payload",(json.dumps(mapping),))
                pass # Monthly data is preserved; local overrides are applied at read time.
        return jsonify(saved=True)

    @app.post('/sync')
    def sync_start():
        if not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),csrf):return jsonify(error='Recarregue a página.'),403
        if request.headers.get('Origin') and request.headers['Origin']!=request.host_url.rstrip('/'):
            return jsonify(error='Origem inválida.'),403
        if not token:return jsonify(error='Configure SISGR_TOKEN no servidor.'),400
        values=request.get_json(silent=True) or {}
        try:
            start=values['start'];end=values['end'];a=dt.date.fromisoformat(start);b=dt.date.fromisoformat(end)
            if not 0<=(b-a).days<31 or start[:7]!=end[:7]:raise ValueError()
            transporters=values.get('transporterIds')
            if not isinstance(transporters,list) or not transporters or len(transporters)>20 or any(not isinstance(t,str) or not t.isdigit() for t in transporters):raise ValueError()
            transporters=list(dict.fromkeys(transporters))
        except (KeyError,TypeError,ValueError):return jsonify(error='Escolha até 31 dias e ao menos uma transportadora (ID numérico).'),400
        if not launch_sync(start,end,transporters):return jsonify(error='Já existe uma atualização em andamento.'),409
        return jsonify(started=True),202

    def launch_sync(start,end,transporters):
        with lock:
            if state['running']:return False
            state.update(running=True,message='Iniciando atualização…',success=None)
        def progress(message):
            with lock:state['message']=message
        def worker():
            try:
                data=synchronize(Client(token,progress),start,end,geo,transporter_ids=transporters,plate_overrides=plate_map())
                data=enrich_snapshot(data,load_vehicle_export(),plate_map())
                payload=json.dumps(data,ensure_ascii=False,allow_nan=False)
                save_month(db_path,data,start,end,transporters)
                with lock:state.update(success=True,message=f"Atualização concluída: {len(data['rows'])} agendamentos. {data['meta'].get('vehiclePending',0)} sem placa confirmada. Período atualizado; demais datas e meses preservados.")
            except Erro as e:
                with lock:state.update(success=False,message=str(e))
            except Exception:
                with lock:state.update(success=False,message='Formato de dados inesperado. Última base preservada; confira o diagnóstico antes de repetir.')
            finally:
                with lock:state['running']=False
        threading.Thread(target=worker,daemon=True).start()
        return True

    if os.environ.get('AUTO_SYNC','0')=='1':
        from scheduler import start_scheduler
        start_scheduler(db_path,lambda:automatic_scope(db_path,dt.datetime.now(dt.timezone.utc)),launch_sync,lambda:bool(token))
    return app

def configure():
    if AUTH_FILE.exists() or (os.environ.get('DASHBOARD_USER') and os.environ.get('DASHBOARD_PASSWORD_HASH')):
        return
    print('Primeiro acesso: crie um usuário local para este painel.')
    user = input('Usuário: ').strip()
    if not user:
        raise SystemExit('Informe um usuário.')
    password = getpass.getpass('Senha (mínimo 12 caracteres): ')
    if len(password) < 12 or password != getpass.getpass('Confirme a senha: '):
        raise SystemExit('Senha curta ou confirmação diferente. Execute novamente.')
    AUTH_FILE.parent.mkdir(exist_ok=True)
    with os.fdopen(os.open(AUTH_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as f:
        json.dump({'user': user, 'hash': generate_password_hash(password)}, f)

if __name__ == '__main__':
    configure()
    token=os.environ.get('SISGR_TOKEN','').strip() or getpass.getpass('Token SISGR (oculto; somente em memória): ').strip()
    if token.lower().startswith('bearer '):token=token[7:].strip()
    if not token or any(c in token for c in '\r\n'):raise SystemExit('Token inválido.')
    print('Ecosupply API v1.10. Abra http://127.0.0.1:8051 no navegador e use o acesso criado. Mantenha este terminal aberto.')
    create_app(token=token).run(host='127.0.0.1', port=8051, debug=False)
