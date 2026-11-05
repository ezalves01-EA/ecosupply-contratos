"""Importação sem gravação: A=ID da recorrência; B=identificador ou automático."""
import csv,io,re,unicodedata,zipfile

def normalized(s):return ''.join(c for c in unicodedata.normalize('NFD',str(s or '')).lower() if c.isalnum())
def parse_recurrences(content,filename):
    if not content or len(content)>2_000_000:raise ValueError('Arquivo vazio ou maior que 2 MB.')
    suffix=filename.lower().rsplit('.',1)[-1]
    if suffix=='xlsx':
        from openpyxl import load_workbook
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                if sum(i.file_size for i in z.infolist())>20_000_000:raise ValueError('Planilha descompactada excede 20 MB.')
            wb=load_workbook(io.BytesIO(content),read_only=True,data_only=False)
            sheet=wb.worksheets[0]
            if sheet.max_row>1001:raise ValueError('Use uma planilha com até 1000 linhas e no máximo 100 IDs por lote.')
            records=[]
            for cells in sheet.iter_rows():
                if any(c.data_type=='f' for c in cells[:2]):raise ValueError('Colunas A/B não podem conter fórmulas. Cole como valores.')
                records.append([c.value for c in cells[:3]])
            wb.close()
        except ValueError:raise
        except Exception:raise ValueError('Não foi possível ler o XLSX. Use um arquivo válido, sem senha.') from None
    elif suffix=='csv':
        try:txt=content.decode('utf-8-sig')
        except UnicodeError:
            try:txt=content.decode('cp1252')
            except UnicodeError:raise ValueError('CSV com codificação inválida. Salve como CSV UTF-8.') from None
        try:dialect=csv.Sniffer().sniff(txt[:4096],delimiters=';,\t')
        except csv.Error:dialect=csv.excel;dialect.delimiter=';'
        records=list(csv.reader(io.StringIO(txt),dialect))
        if len(records)>1001:raise ValueError('Arquivo excede 1000 linhas.')
    else:raise ValueError('Use .xlsx ou .csv (A=ID e B=identificador).')
    items=[];errors=[];seen={}
    for line,values in enumerate(records,1):
        values=list(values)+[None,None,None];a,b=values[:2]
        if not any(v is not None and str(v).strip() for v in values):continue
        if line==1 and normalized(a) in {'id','idrecorrencia','iddarecorrencia','recorrencia'}:continue
        if isinstance(a,(int,float)) and not isinstance(a,bool) and float(a).is_integer():a=str(int(a))
        else:a=str(a or '').strip()
        if not re.fullmatch(r'[1-9][0-9]{0,14}',a):errors.append({'line':line,'message':'ID inválido na coluna A.'});continue
        if a in seen:errors.append({'line':line,'message':f'ID {a} repetido; primeira ocorrência na linha {seen[a]}.'});continue
        seen[a]=line
        if values[2] not in (None,''):errors.append({'line':line,'message':'Há conteúdo na coluna C; mantenha apenas A e B.'});continue
        route='' if b is None else str(b).strip()
        if len(route)>150 or any(ord(c)<32 for c in route):errors.append({'line':line,'message':'Identificador inválido na coluna B (máximo 150 caracteres).'});continue
        items.append({'id':a,'requestedRoute':route or None,'sourceRow':line})
    if not items and not errors:errors.append({'line':0,'message':'Nenhum ID encontrado.'})
    if len(items)>100:errors.append({'line':0,'message':'Limite de 100 IDs por lote. Divida a planilha.'})
    return {'items':items if not errors else [],'errors':errors,'valid':not errors}
