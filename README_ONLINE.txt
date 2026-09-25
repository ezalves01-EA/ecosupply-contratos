ECOSUPPLY - SISTEMA DE CONTRATOS V7 (ONLINE)

PRINCIPAIS MUDANCAS
- Login por usuario.
- Perfil ADMIN para cadastro de usuarios.
- Mantida a senha 123456 para a area Acoes (pode ser alterada pela variavel ACTION_PASSWORD).
- Banco PostgreSQL quando DATABASE_URL estiver configurada.
- SQLite continua funcionando para testes locais.
- Pronto para Gunicorn e Render.

ACESSO LOCAL INICIAL
Usuario: admin
Senha: 123456
Em producao, configure ADMIN_PASSWORD com uma senha forte.

PUBLICACAO NO RENDER
1. Crie um repositorio privado no GitHub e envie esta pasta.
2. No Render, escolha New > Blueprint e selecione o repositorio.
3. O arquivo render.yaml cria o Web Service e o PostgreSQL.
4. Informe ADMIN_PASSWORD quando o Render solicitar.
5. Aguarde o deploy e abra o endereco HTTPS criado pelo Render.
6. Entre como admin e use o menu Usuarios para cadastrar os demais acessos.

VARIAVEIS
DATABASE_URL = conexao PostgreSQL
SECRET_KEY = chave secreta da sessao
ADMIN_USER = usuario administrador inicial
ADMIN_PASSWORD = senha administrador inicial
ACTION_PASSWORD = senha da coluna Acoes (padrao 123456)

IMPORTANTE
Os arquivos Word/PDF sao gerados sob demanda. O cadastro permanente fica no PostgreSQL.
