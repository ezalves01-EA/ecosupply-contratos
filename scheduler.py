"""Single-process daily scheduler; persistent slot claim prevents restart duplicates."""
import datetime as dt
import sqlite3
import threading
from zoneinfo import ZoneInfo
BRASILIA=ZoneInfo('America/Sao_Paulo')

def due_slot(now):
    now=now.astimezone(BRASILIA)
    if now.hour not in (0,11) or now.minute!=0:return None
    return now.strftime('%Y-%m-%d %H:00')

def tick(db_path,load,launch,configured,now):
    slot=due_slot(now)
    if not slot or not configured():return False
    meta=load().get('meta',{})
    if not meta.get('importedAt') or not meta.get('transporterIds'):return False
    key='auto:'+slot
    with sqlite3.connect(db_path) as db:
        result=db.execute('INSERT OR IGNORE INTO settings(name,payload) VALUES(?,?)',(key,'claimed'))
        if not result.rowcount:return False
    started=launch(meta['periodStart'],meta['periodEnd'],meta['transporterIds'])
    with sqlite3.connect(db_path) as db:
        db.execute('UPDATE settings SET payload=? WHERE name=?',('started' if started else 'skipped_busy',key))
        db.execute("DELETE FROM settings WHERE name LIKE 'auto:%' AND name < ?",('auto:'+(now.astimezone(BRASILIA)-dt.timedelta(days=60)).strftime('%Y-%m-%d'),))
    return started

def start_scheduler(db_path,load,launch,configured):
    def loop():
        while True:
            try:tick(db_path,load,launch,configured,dt.datetime.now(dt.timezone.utc))
            except Exception:
                import logging
                logging.getLogger(__name__).exception('Falha no agendador automático')
            threading.Event().wait(15)
    threading.Thread(target=loop,name='sisgr-scheduler',daemon=True).start()
