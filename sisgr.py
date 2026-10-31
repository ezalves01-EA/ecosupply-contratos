import json,datetime as dt,urllib.request,urllib.parse,urllib.error
from decimal import Decimal,InvalidOperation
from enrichment import TRANSPORTERS, vehicle_plate, actual_date, load_vehicle_export
from transporte_base import SemRedirecionamento,abrir_com_espera,Erro
BASE='https://ecosupply.sisgr.com/api/v1'
class APIError(Erro):
    def __init__(self,code,path):
        self.code=code
        super().__init__(f'API retornou HTTP {code} em {path.split("/")[1]}.')

class Client:
    def __init__(self,token,progress=lambda s:None):
        self.token=token;self.progress=progress;self.opener=urllib.request.build_opener(SemRedirecionamento);self.cache={};self.loaded_catalogs=set();self.catalog_errors={};self.exported_vehicles=load_vehicle_export()
    def get(self,path,params=None):
        url=BASE+path+('?' + urllib.parse.urlencode(params) if params else '')
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+self.token,'Accept':'application/json'})
        try:
            with abrir_com_espera(self.opener,req) as r:
                if 'json' not in r.headers.get('Content-Type','').lower():raise Erro('API não retornou JSON.')
                raw=r.read(20_000_001)
                if len(raw)>20_000_000:raise Erro('Resposta da API excedeu o limite.')
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raise APIError(e.code,path) from None
        except (urllib.error.URLError,TimeoutError,OSError):raise Erro('Falha de conexão com SISGR; última base preservada.') from None
        except (ValueError,UnicodeError):raise Erro('Resposta JSON inválida.') from None
    def list(self,path,params):
        records={};previous=None
        for page in range(1,501):
            p=self.get(path,{**params,'page':page,'per_page':100})
            if isinstance(p,list) and len(p)==1 and isinstance(p[0],dict) and 'data' in p[0]:p=p[0]
            batch=p.get('data') if isinstance(p,dict) else p
            if not isinstance(batch,list):raise Erro('Lista da API em formato inesperado.')
            signature=[]
            for r in batch:
                if not isinstance(r,dict) or r.get('id') is None:raise Erro('Registro sem ID.')
                rid=str(r['id']);signature.append(rid)
                if rid in records and records[rid]!=r:raise Erro('ID mudou durante a paginação. Repita a atualização.')
                records[rid]=r
            if batch and signature==previous:
                if path=='/vehicles':return list(records.values())
                raise Erro('API repetiu a mesma página. Atualização interrompida.')
            previous=signature
            if isinstance(p,dict) and 'last_page' in p:
                try:current=int(p['current_page']);last=int(p['last_page'])
                except (KeyError,TypeError,ValueError):raise Erro('Paginação inválida.') from None
                if current!=page or last<current:raise Erro('Paginação inconsistente.')
                if page==last:return list(records.values())
            elif not batch:return list(records.values())
        raise Erro('Limite de páginas atingido; resultado não aplicado.')
    def detail(self,path,id):
        if id is None:return {}
        key=(path,str(id))
        if path=='/vehicles':
            if path not in self.loaded_catalogs:
                self.progress('Carregando cadastro de veículos…')
                try:
                    vehicles=self.list(path,{})
                except APIError as e:
                    if e.code<500:raise
                    # A documentação também permite a lista direta sem paginação.
                    try:
                        payload=self.get(path)
                        if isinstance(payload,dict):
                            if int(payload.get('last_page',1))>1:raise Erro('Lista direta de veículos incompleta; consulte o diagnóstico isolado.')
                            payload=payload.get('data')
                        if not isinstance(payload,list):raise Erro('Lista direta de veículos em formato inesperado.')
                        vehicles=payload
                    except APIError as direct:
                        if direct.code<500:raise
                        self.catalog_errors[path]='Cadastro de veículos indisponível: consulta paginada HTTP '+str(e.code)+' e lista direta HTTP '+str(direct.code)+'. Placas não confirmadas.'
                        vehicles=[]
                for vehicle in vehicles:
                    if not isinstance(vehicle,dict) or vehicle.get('id') is None:raise Erro('Cadastro de veículos em formato inesperado.')
                    item_key=(path,str(vehicle['id']))
                    if item_key in self.cache and self.cache[item_key]!=vehicle:raise Erro('Veículo repetido com dados divergentes.')
                    self.cache[item_key]=vehicle
                self.loaded_catalogs.add(path)
            if key not in self.cache and str(id) in self.exported_vehicles:return self.exported_vehicles[str(id)]
            return self.cache.get(key,{'id':id,'catalogWarning':self.catalog_errors.get(path,'Veículo não retornado na lista; placa não confirmada.')})
        if key not in self.cache:
            value=self.get(path+'/'+urllib.parse.quote(str(id),safe=''))
            if isinstance(value,dict) and isinstance(value.get('data'),(dict,list)):value=value['data']
            if isinstance(value,list):
                matches=[r for r in value if isinstance(r,dict) and str(r.get('id'))==str(id)]
                if len(matches)==1:value=matches[0]
            if not isinstance(value,dict) or str(value.get('id'))!=str(id):raise Erro('Cadastro retornou ID ou formato inesperado.')
            self.cache[key]=value
        return self.cache[key]

def signature(row):
    if 'sign_image' not in row:return None
    v=row['sign_image']
    if v is None or v is False or v==0:return False
    if isinstance(v,str):return bool(v.strip()) and v.strip().lower() not in ['null','none','false','0']
    return None

def measures(collects,schedule_id):
    sums={};destinations=set();issues=[];seen=set()
    for r in collects:
        rid=str(r.get('id'))
        if rid in seen:continue
        seen.add(rid)
        links=[r[k] for k in ['agendamento_id','schedule_id'] if r.get(k) is not None]
        if not links or any(str(v)!=str(schedule_id) for v in links):raise Erro('Coleta vinculada a outro agendamento. Atualização não aplicada.')
        if r.get('canceled_at'):issues.append('Coleta cancelada: quantidade requer revisão');continue
        dest=r.get('destination') or {};res=r.get('residue') or {};did=dest.get('id')
        if did is not None and str(did) in destinations:issues.append('Destino repetido: risco de duplicar quantidade');continue
        if did is not None:destinations.add(str(did))
        unit=str(res.get('unity') or '').strip().upper()
        unit={'KG':'KG','L':'L','M3':'M3','M³':'M3','T':'T','TON':'T','TONELADA':'T','TONELADAS':'T'}.get(unit)
        raw=dest.get('measure')
        try:
            if raw is None or raw=='' or isinstance(raw,bool) or not unit:raise ValueError()
            amount=Decimal(str(raw))
            if not amount.is_finite() or amount<0:raise ValueError()
        except (InvalidOperation,ValueError):issues.append('Quantidade/unidade ausente ou inválida');continue
        if unit=='T':unit='KG';amount*=1000
        sums[unit]=sums.get(unit,Decimal(0))+amount
    if not collects:issues.append('Nenhuma coleta retornada')
    if issues:return {'KG':0,'L':0,'M3':0},[],sorted(set(issues))
    return {u:float(sums.get(u,0)) for u in ['KG','L','M3']},list(sums),[]

def norm(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD',str(s)) if unicodedata.category(c)!='Mn').casefold().strip()

def inside_ring(point,ring):
    x,y=point;inside=False
    for i in range(len(ring)):
        x1,y1=ring[i-1][:2];x2,y2=ring[i][:2]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:inside=not inside
    return inside

def coordinate(address,feature):
    if not feature:return None
    geo=address.get('geolocation') or {}
    try:x=float(geo['long']);y=float(geo['lat'])
    except (KeyError,ValueError,TypeError):return None
    g=feature['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    for poly in polys:
        if inside_ring((x,y),poly[0]) and not any(inside_ring((x,y),hole) for hole in poly[1:]):return [x,y]
    return None

def synchronize(client,start,end,geo,transporter_ids=None,plate_overrides=None):
    a=dt.date.fromisoformat(start);b=dt.date.fromisoformat(end)
    if not 0<=(b-a).days<31:raise Erro('Escolha um período de até 31 dias.')
    client.progress('Consultando agendamentos…')
    schedules=client.list('/schedules',{'schedule_date$bw':start+','+end})
    total_found=len(schedules)
    if transporter_ids is not None:schedules=[s for s in schedules if str(s.get('transporter_id')) in transporter_ids]
    plate_overrides=plate_overrides or {}
    features={norm(f['properties']['Cidade']):f for f in geo['features']}
    rows=[];quality=[];source_rows=0
    for index,s in enumerate(schedules,1):
        date=str(s.get('schedule_date',''))[:10]
        if not start<=date<=end:raise Erro('API não respeitou o período solicitado.')
        dt.date.fromisoformat(date)
        client.progress(f'Atualizando agendamento {index} de {len(schedules)}…')
        gen=client.detail('/generators',s.get('generator_id'));driver=client.detail('/professionals',s.get('driver_id'));vehicle=client.detail('/vehicles',s.get('vehicle_id'))
        confirmed_plate,plate_source=vehicle_plate(vehicle,s,plate_overrides)
        reference_plate,reference_source=vehicle_plate(vehicle,s,{})
        api_plate=reference_plate if reference_source=='API SISGR' else None
        if not confirmed_plate and vehicle.get('catalogWarning'):quality.append({'id':s['id'],'motivos':[vehicle['catalogWarning']]})
        actual_driver_id=s.get('motoristaIniciouAtendimento_id') or s.get('driver_id')
        actual_driver=driver if str(actual_driver_id)==str(s.get('driver_id')) else client.detail('/professionals',actual_driver_id)
        collection_date,date_source=actual_date(s)
        address=gen.get('address') or {};cityobj=address.get('city') or {};city=cityobj.get('name','Sem cidade') if isinstance(cityobj,dict) else str(cityobj)
        state=cityobj.get('state') or {} if isinstance(cityobj,dict) else {}
        state_name=str(state.get('uf') or state.get('sigla') or state.get('name') or ('MT' if str(state.get('id') or state.get('code'))=='51' else '')) if isinstance(state,dict) else str(state)
        feature=features.get(norm(city)) if norm(state_name) in ['mt','mato grosso'] else None
        city=feature['properties']['Cidade'] if feature else city
        status=str(s.get('status') or 'SEM STATUS').strip().upper()
        amount={'KG':0,'L':0,'M3':0};units=[];issues=[];collects=[]
        typ=str(s.get('type') or 'SEM TIPO').strip().upper()
        if typ=='COLETA' and status in ['REALIZADO','EFETIVADO']:
            collects=client.list('/collects',{'schedule':s['id']})
            amount,units,issues=measures(collects,s['id'])
        if issues:quality.append({'id':s['id'],'motivos':issues})
        sign=signature(s)
        if sign is None:quality.append({'id':s['id'],'motivos':['Assinatura sem campo/formato reconhecido']})
        source_rows+=len(collects)
        rows.append({'id':s['id'],'date':date,'collectionDate':collection_date,'collectionDateSource':date_source,'transporterId':str(s.get('transporter_id') or ''),'transporter':TRANSPORTERS.get(str(s.get('transporter_id')),'Transportadora ID '+str(s.get('transporter_id'))),'actualDriver':actual_driver.get('nome') or actual_driver.get('name') or 'Sem motorista','actualDriverId':actual_driver_id,'actualDriverSource':'atendimento' if s.get('motoristaIniciouAtendimento_id') else 'agendamento','pointId':s.get('generator_id') or 'Sem geradora','point':gen.get('name') or 'Geradora não informada','city':city,'state':state_name,'region':feature['properties']['Regiao'] if feature else 'Sem classificação','plate':confirmed_plate or ('Veículo ID '+str(s['vehicle_id'])+' · sem placa' if s.get('vehicle_id') is not None else 'Sem veículo informado'),'vehicleId':s.get('vehicle_id'),'plateConfirmed':bool(confirmed_plate),'plateSource':plate_source,'apiPlate':api_plate,'referencePlate':reference_plate,'referencePlateSource':reference_source,'driverId':s.get('driver_id'),'driver':driver.get('nome') or driver.get('name') or 'Sem motorista','truckTypeSource':'API SISGR' if s.get('vehicle_type') else vehicle.get('catalogSource','API SISGR'), 'truckType':str(s.get('vehicle_type') or vehicle.get('vehicle_type') or ('Tipo ID '+str(s['vehicle_type_id']) if s.get('vehicle_type_id') else 'Sem tipo')),'type':typ,'status':status,'signature':sign,'measures':amount,'measureUnits':units,'sourceRows':len(collects),'duplicateLines':0,'category':str(gen.get('type') or ''),'address':', '.join(str(v) for v in [address.get('street'),address.get('number'),city,state_name] if v),'coords':coordinate(address,feature),'volumeIssues':issues})
    return {'rows':rows,'geo':geo,'meta':{'schemaVersion':4,'source':'API SISGR · base local','sourceRows':source_rows,'periodStart':start,'periodEnd':end,'importedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'apiConnected':True,'regionProposal':True,'quality':quality,'volumePending':sum(bool(r['volumeIssues']) for r in rows),'signatureUnknown':sum(r['signature'] is None for r in rows),'vehiclePending':sum(not r['plateConfirmed'] for r in rows),'transporterIds':transporter_ids,'appointmentsBeforeTransportFilter':total_found,'driverDateRule':'end_attendance; fallback end_at; fuso UTC-4. Datas sem fuso consideradas locais.'}}
