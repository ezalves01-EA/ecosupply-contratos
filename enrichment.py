import datetime as dt,re
TRANSPORTERS={'5':'5 · ECOSUPPLY RECICLADORA LTDA.','6':'6 · ECOSUPPLY RECICLADORA DO NORTE LTDA.'}

def plate(value):
    if not isinstance(value,str):return None
    v=re.sub(r'[^A-Z0-9]','',value.upper())
    if not re.fullmatch(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}',v):return None
    return v[:3]+'-'+v[3:]

def vehicle_plate(vehicle,schedule,overrides):
    vid=str(schedule.get('vehicle_id'))
    if plate(overrides.get(vid)):return plate(overrides[vid]),'Cadastro local'
    for obj in [vehicle,schedule.get('vehicle') or {}]:
        if isinstance(obj,dict):
            for key in ['place_number','plate','license_plate','placa']:
                if plate(obj.get(key)):return plate(obj[key]),obj.get('catalogSource','API SISGR')
    return None,'Placa indisponível'

def actual_date(schedule):
    for field in ['end_attendance','end_at']:
        value=schedule.get(field)
        if not isinstance(value,str) or not value.strip():continue
        try:
            parsed=dt.datetime.fromisoformat(value.strip().replace('Z','+00:00'))
            if parsed.tzinfo:parsed=parsed.astimezone(dt.timezone(dt.timedelta(hours=-4)))
            return parsed.date().isoformat(),field
        except ValueError:continue
    return None,None

def load_vehicle_export():
    import json
    from pathlib import Path
    path=Path(__file__).resolve().parent/'data'/'veiculos_exportados.json'
    if not path.exists():return {}
    data=json.loads(path.read_text(encoding='utf-8'))
    source='Exportação SISGR '+data['exportedAt']
    return {str(v['id']):{**v,'catalogSource':source} for v in data['vehicles']}

def enrich_snapshot(data,exported,manual):
    """Update saved rows by exact vehicle ID. Never infer type by plate."""
    for r in data.get('rows',[]):
        vid=str(r.get('vehicleId'));ref=exported.get(vid,{})
        api=r.get('apiPlate')
        if not api and r.get('plateConfirmed') and r.get('plateSource') in [None,'API SISGR']:api=plate(r.get('plate'))
        reference=api or plate(ref.get('place_number'))
        reference_source='API SISGR' if api else ref.get('catalogSource','Placa indisponível')
        local=plate(manual.get(vid))
        r.update(apiPlate=api,referencePlate=reference,referencePlateSource=reference_source,
                 plate=local or reference or ('Veículo ID '+vid+' · sem placa' if r.get('vehicleId') is not None else 'Sem veículo informado'),
                 plateConfirmed=bool(local or reference),plateSource='Cadastro local' if local else reference_source)
        typ=str(r.get('truckType') or '')
        if ref.get('vehicle_type') and (not typ or typ.startswith('Tipo ID ') or typ=='Sem tipo' or str(r.get('truckTypeSource','')).startswith('Exportação SISGR')):
            r['truckType']=ref['vehicle_type'];r['truckTypeSource']=ref['catalogSource']
    meta=data.get('meta')
    if isinstance(meta,dict):
        confirmed={str(r['id']) for r in data.get('rows',[]) if r.get('plateConfirmed')}
        quality=[]
        for q in meta.get('quality',[]):
            reasons=q.get('motivos',[])
            if str(q.get('id')) in confirmed:reasons=[m for m in reasons if not m.startswith(('Cadastro de veículos','Veículo não retornado'))]
            if reasons:quality.append({**q,'motivos':reasons})
        meta['quality']=quality
        meta['vehiclePending']=sum(not r.get('plateConfirmed') for r in data.get('rows',[]))
        meta['vehicleExportRows']=sum(str(r.get('plateSource','')).startswith('Exportação SISGR') for r in data.get('rows',[]))
    return data


def apply_regions(data,geo):
    regions={f['properties']['Cidade']:f['properties']['Regiao'] for f in geo['features']}
    for row in data.get('rows',[]):
        if row.get('city') in regions and row.get('state') in (None,'MT','Mato Grosso','51',51):row['region']=regions[row['city']]
    if 'geo' in data:data['geo']=geo
    return data
