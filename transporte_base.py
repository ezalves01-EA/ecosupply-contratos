import time
import datetime as dt
import urllib.request
import urllib.error
from email.utils import parsedate_to_datetime
class Erro(Exception): pass
class SemRedirecionamento(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def abrir_com_espera(opener,req):
    for attempt in range(4):
        time.sleep(2)
        try: return opener.open(req,timeout=30)
        except urllib.error.HTTPError as e:
            if e.code!=429 or attempt==3: raise
            delay=15*(2**attempt)
            retry=e.headers.get('Retry-After') if e.headers else None
            if retry:
                try: delay=max(delay,int(retry))
                except ValueError:
                    try: delay=max(delay,(parsedate_to_datetime(retry)-dt.datetime.now(dt.timezone.utc)).total_seconds())
                    except (ValueError,TypeError,OverflowError): pass
            if delay>300: raise Erro('API pediu espera superior a cinco minutos. Execute mais tarde.') from None
            e.close()
            print(f'Limite 429: aguardando {int(delay)} segundos antes da próxima tentativa.')
            time.sleep(delay)

