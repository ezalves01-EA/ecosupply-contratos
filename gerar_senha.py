import getpass
from werkzeug.security import generate_password_hash
password=getpass.getpass('Nova senha do painel (mínimo 12 caracteres): ')
if len(password)<12 or password!=getpass.getpass('Confirme: '):raise SystemExit('Senha curta ou confirmação diferente.')
print('Copie para DASHBOARD_PASSWORD_HASH no Render:')
print(generate_password_hash(password))
