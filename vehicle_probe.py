"""Teste isolado de veículos: nunca salva token, placas ou resposta bruta."""
import getpass,json,os
from pathlib import Path
from sisgr import Client,APIError,Erro
from enrichment import vehicle_plate

def describe(payload):
    body=payload
    if isinstance(body,dict):body=body.get('data')
    if not isinstance(body,list):return {'formato_valido':False,'tipo_raiz':type(payload).__name__}
    valid=[r for r in body if isinstance(r,dict)]
    return {'formato_valido':len(valid)==len(body),'tipo_raiz':type(payload).__name__,'registros_na_resposta':len(body),'campos_veiculo':sorted({k for r in valid for k in r}),'veiculos_com_id':sum(r.get('id') is not None for r in valid),'placas_reconhecidas':sum(vehicle_plate(r,{}, {})[0] is not None for r in valid)}

def main():
    token=os.environ.get('SISGR_TOKEN','').strip() or getpass.getpass('Token SISGR (oculto): ').strip()
    if token.lower().startswith('bearer '):token=token[7:].strip()
    if not token or any(c in token for c in '\r\n'):raise Erro('Token inválido.')
    client=Client(token);result={'consultas':[]}
    for label,params in [('vehicles_com_paginacao',{'page':1,'per_page':100}),('vehicles_sem_parametros',None)]:
        item={'consulta':label};result['consultas'].append(item)
        try:item.update(http=200,**describe(client.get('/vehicles',params)))
        except APIError as e:
            item['http']=e.code
            if e.code in [401,403,429]:break
        except Erro as e:item['erro']=str(e)
    path=Path(__file__).resolve().parent/'diagnostico_veiculos.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Resultado salvo em diagnostico_veiculos.json. Pode enviar esse arquivo; não contém token ou placas.')
if __name__=='__main__':
    try:main()
    except (Erro,EOFError,KeyboardInterrupt) as e:print('Teste interrompido: '+(str(e) or 'cancelado.'));raise SystemExit(1)
