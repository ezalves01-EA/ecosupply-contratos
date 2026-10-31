# Publicação no Render
Consulte RENDER.md para a versão online, configuração e persistência. As instruções abaixo são para execução local.

# Ecosupply — API v1.8

## Atualizar uma instalação existente
1. Pare o servidor com Ctrl+C.
2. Faça uma cópia da pasta instance (usuário, banco e placas locais).
3. Copie os arquivos e pastas deste pacote para a pasta atual do projeto, substituindo os antigos. Inclua enrichment.py, a pasta web e a pasta data. Preserve instance e .venv.
4. Execute `.venv\Scripts\python app.py` (Windows) ou `.venv/bin/python app.py` (Linux/macOS).
5. Informe o token no terminal e abra http://127.0.0.1:8051. Use Ctrl+F5. A tela deve mostrar Versão 1.8.
6. Faça uma nova sincronização para preencher transportadora, motorista de atendimento e data de realização na base antiga.

## Primeira instalação — Python 3.11 ou superior
Windows:
```
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```
Linux/macOS:
```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```
Crie usuário local e senha de no mínimo 12 caracteres. Informe o token SISGR no prompt oculto; ele fica em memória. Alternativamente use a variável SISGR_TOKEN. O token nunca é enviado ao navegador ou gravado no banco. Use o usuário local criado ao abrir http://127.0.0.1:8051.

## Buscar e filtrar transportadoras
Na sincronização, marque 5 (Ecosupply Recicladora LTDA.), 6 (Ecosupply Recicladora do Norte LTDA.) ou ambas, conforme os IDs do SISGR fornecidos. Outros IDs podem ser digitados separados por vírgula. Pelo menos um ID é obrigatório. O sistema busca os agendamentos do período e seleciona os IDs de transportadora antes de consultar os demais cadastros e volumes.

Nos filtros do painel, Transportadora permite selecionar uma ou várias entre as que foram carregadas. Cada filtro usa OU entre opções; filtros distintos são combinados por E. Para adicionar uma transportadora que não foi carregada, sincronize novamente incluindo seu ID.

Cada sincronização substitui toda a base local pelo período de agendamento escolhido (até 31 dias) e pelas transportadoras selecionadas. Não acumula meses, não faz histórico e não sincroniza automaticamente. Inicie por um dia. Consultas podem levar minutos. Mantenha o terminal aberto.

## Motoristas: coletas, kg e dias com coleta
A aba Motoristas mostra todos os motoristas presentes na base operacional selecionada, inclusive os que não fizeram coleta no recorte de realização. Não limita a Top 10. Há gráficos separados de coletas feitas, kg e dias com coleta e uma tabela com litros e datas.

Data realizada: end_attendance (Fim do Atendimento); se vazio/inválido, end_at (Fim da Coleta). A data do agendamento não é usada para substituir uma data realizada ausente. Datas com fuso são convertidas para UTC-4; datas sem fuso são consideradas locais de Cuiabá. A origem do campo está registrada em cada linha e no CSV exportado. Esta regra precisa ser conferida com os horários reais do SISGR para o período carregado.

Dias com coleta = quantidade de datas distintas com COLETA em REALIZADO ou EFETIVADO. Dez coletas no mesmo dia contam como um dia. Isso não comprova dias de trabalho sem coleta, viagens, entregas ou jornada de ponto.

A aba usa o profissional motoristaIniciouAtendimento_id quando disponível. Na ausência, usa driver_id do agendamento e informa essa quantidade na nota do painel. Os demais gráficos operacionais continuam usando o motorista programado.

Ao entrar na aba, os filtros De/Até passam a usar a data realizada e inicialmente cobrem as datas realizadas existentes na base. Ao voltar às outras abas, retomam o período de agendamento carregado. O filtro de status é ignorado nessa aba: só coletas feitas entram nos resultados.

Coletas sem data realizada reconhecida são contadas separadamente e ficam fora dos gráficos por período. A aba não busca agendamentos adicionais: para incluir uma coleta realizada hoje que estava agendada em outro período, é necessário carregar também esse período de agendamento. Por enquanto a busca na API é por schedule_date; não há garantia de extrair todas as realizações de um mês consultando apenas os agendamentos desse mesmo mês.

## Placas
A API /vehicles continua sendo tentada com paginação. Erro 5xx permite continuar pelo ID do veículo; erros de autenticação ou limite de consultas preservam a base anterior. Quando presente, são reconhecidos place_number, plate, license_plate e placa em objetos de veículo. Não há associação de IDs a placas por adivinhação.

Se a API não fornecer a placa, abra “Conferir e cadastrar placas por ID”, clique em Carregar veículos da base, informe a placa ao lado do ID correto do SISGR e salve. O cadastro fica neste computador e é aplicado à base atual e às próximas sincronizações. A origem aparece como Cadastro local no CSV. Esvaziar o cadastro local restaura a placa da API, se disponível. Sem informação, permanece Veículo ID … · sem placa.

## Regiões e mapa
Mapa ampliado para os 142 municípios de Mato Grosso da Malha Municipal IBGE 2024. As regiões operacionais já propostas foram preservadas. Municípios adicionais usam a respectiva Região Geográfica Imediata indicada na própria malha, com o prefixo IBGE · (ex.: IBGE · Sinop). São classificações de origens diferentes, identificadas no arquivo data/regioes.csv para conferência; não representam rotas otimizadas.

Fonte: https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2024/UFs/MT/MT_Municipios_2024.zip
Limites simplificados em 0,002 grau para exibição. Cidades fora de MT continuam nas tabelas, com região Sem classificação. data/regioes.csv é um relatório da classificação incorporada; editar esse CSV não altera automaticamente o mapa.

Coordenadas da geradora são aceitas somente dentro do município correspondente. Pontos sem coordenada válida permanecem nas tabelas. Um endereço específico do agendamento pode diferir da geradora: schedule_address_id ainda não é resolvido nesta versão.

## Contagem e volume
Um registro por ID de agendamento. REALIZADO e EFETIVADO = feitos; ROTA = pendente. Outros status permanecem explicitamente no denominador da conclusão. Não são convertidos automaticamente em ROTA.

Volume: destination.measure com residue.unity, somente COLETA feita. KG, L e M3 ficam separados; toneladas são convertidas para KG. IDs de coleta repetidos são consolidados. Destinos repetidos em coletas distintas, quantidades ausentes, unidades não reconhecidas e coletas canceladas bloqueiam o volume daquele agendamento e geram pendência para revisão. Os totais são dos volumes válidos, com cobertura informada.

Mapeamento de volume validado em seis agendamentos contra o Excel. Ampliar conferência antes do uso oficial. FALTA EFETIVAR = sign_image preenchido e status diferente de EFETIVADO; imagem não armazenada. Assinatura ausente ou formato não reconhecido gera pendência.

## Persistência e segurança local
Banco SQLite em instance/painel.sqlite; senha como hash em instance/auth.json. Placas locais na tabela settings. A última base válida só é substituída após a conclusão da sincronização. Falhas não aplicam dados parciais. Fechar o terminal cancela consultas em andamento. Não há retomada de páginas entre execuções.

Requisições têm pausa de dois segundos. Em 429 há até três novas tentativas respeitando Retry-After; espera acima de cinco minutos interrompe. Cadastros repetidos são reaproveitados durante a mesma sincronização.

Servidor somente localhost, sem publicação no Render nesta versão. Não envie instance ao Git. CPF, RG, imagens e respostas brutas não são salvos no banco; nomes, endereços, coordenadas, placas e volumes necessários ao painel são persistidos localmente. A migração para Render exigirá configuração de produção, banco persistente e worker/agendador.

## Verificação
No ambiente ativo: `python -m unittest -v`. Com Node instalado: `node test_driver_metrics.cjs`.
Os testes usam respostas simuladas, incluindo erro 500 de veículos, datas de realização diferentes do agendamento, filtro de transportadoras e cadastro de placas. Teste visual feito com dados simulados. Nenhum teste autenticado com seu token foi executado nesta atualização.

## v1.5 — gráficos de motoristas no estilo solicitado
Novo quadro azul com colunas agrupadas (vermelho = atrasadas; verde = feitas), números sobre as colunas, alternância na legenda e atalhos de tipo de caminhão. Inclui tabela por tipo e roscas geral/por tipo. Todos os motoristas aparecem; gráficos largos têm rolagem horizontal. Gráficos de coletas feitas, kg e dias com coleta agora usam colunas verticais separadas.

O quadro Feitas × Atrasadas compara a mesma coorte: período de AGENDAMENTO, escolhido dentro do próprio quadro, com motorista programado. Feitas = REALIZADO + EFETIVADO; atrasadas = ROTA com data de agendamento anterior à data atual de Cuiabá. Agendamentos de hoje e futuros em ROTA não são atrasados. Outros status e coletas ainda não atrasadas são informados na tabela, excluídos das duas séries e dos percentuais das roscas. Percentual da rosca = feitas ÷ (feitas + atrasadas). Não é a conclusão geral sobre todos os agendamentos. Filtro de status é ignorado.

Os gráficos de produção real abaixo continuam pela DATA DE REALIZAÇÃO (filtros De/Até principais) e pelo motorista de atendimento, com os critérios já descritos. O filtro de motorista pode afetar os blocos de modo diferente se o programado e o executor forem pessoas diferentes. As datas dos dois blocos são identificadas para evitar misturar as populações.

## Veículos — diagnóstico isolado
O painel tenta a consulta paginada e, após um erro 5xx, a lista direta /vehicles sem parâmetros. Se as duas falharem, mantém veículo por ID e o aviso. O HTTP 500 ainda depende de confirmação na API real; não houve teste autenticado nesta atualização.

Para investigar, fora da sincronização execute `.venv\Scripts\python vehicle_probe.py` (Windows), informe o token no prompt oculto e envie diagnostico_veiculos.json. O teste faz duas consultas de leitura e grava apenas HTTP, estrutura, campos e contagens; não salva token, nomes, IDs, placas ou resposta bruta. Não rode junto da sincronização. Em 401/403/429 interrompe a sequência. Esse relatório ajuda a distinguir falha de servidor de diferença no formato de retorno.

Avisos de qualidade repetidos ficam agrupados, com os IDs acessíveis em Ver IDs. A pendência Quantidade/unidade ausente ou inválida (ex.: #132713) é independente da consulta de veículos e continua excluindo o volume não comprovado.

## v1.6 — base ajustada de veículos
Incorporados os 72 IDs da exportação ajustada exportacao_veiculos30-10-26(2).xls de 30/10/2026. Placa e tipo são associados pelo ID exato do veículo, inclusive quando a mesma placa aparece em IDs diferentes. A consulta /vehicles apresentou HTTP 500 no diagnóstico enviado; esta versão contorna a falta do cadastro usando a exportação, sem corrigir o servidor SISGR.

Ao reiniciar e usar Ctrl+F5, a base já salva recebe as placas e os tipos ausentes, sem precisar consultar a API novamente. Inclua a pasta data ao atualizar. Prioridade das placas: cadastro local, API, exportação. Apagar uma placa local restaura a referência da API ou da exportação. Tipos já descritos pela API são preservados; rótulos Tipo ID são preenchidos pela exportação. A origem aparece na conferência e no CSV. IDs fora da exportação continuam sinalizados. Novos veículos ou alterações exigem atualizar o cadastro de referência.

## v1.8 — nove regiões e atualização automática
Todas as 142 cidades de MT foram agrupadas nas nove regiões operacionais. A classificação IBGE complementar foi absorvida. Confira data/regioes.csv. A base salva e o mapa recebem o agrupamento ao recarregar, sem consulta à API. Classificação operacional proposta: Sinop/Alta Floresta/Peixoto/Juara → Norte; Sorriso → Centro-Norte; Juína → Extremo Oeste; demais cidades incorporadas às respectivas regiões de entorno.

No Render existente, configure AUTO_SYNC=1 em Environment e faça deploy dos novos arquivos. O blueprint já contém a variável para novas instalações. Atualizações às 00h e 11h de America/Sao_Paulo (Brasília); continuam manuais também. Repete exatamente o período de agendamento e as transportadoras da última base bem-sucedida. Não avança datas automaticamente. Faça uma carga manual inicial ou para trocar o recorte. Requer serviço ativo, um worker e disco persistente. Não usar --preload.

O agendador verifica a cada 15 segundos durante o minuto marcado, registra o horário no SQLite para evitar repetição após reinício e não inicia se outra consulta está em andamento. Horários perdidos por indisponibilidade, concorrência ou falha não são recuperados automaticamente; a última base concluída é preservada. O navegador não precisa estar aberto. Para desativar, AUTO_SYNC=0.

## v1.9 — armazenamento por mês (substitui regras anteriores de período)
Cada atualização substitui somente a partição do mês escolhido; os outros meses permanecem intactos. Escolha o mês no menu Atualizar dados: as datas são preenchidas do primeiro ao último dia. Não consulte dois meses na mesma operação. Para atualizar um mês fechado inteiro, mantenha essas datas completas; uma consulta parcial substitui a partição daquele mês pelo recorte parcial informado. A seleção de transportadoras também vale somente para a carga daquele mês.

A base anterior é migrada automaticamente no primeiro início; preserve o disco e DATABASE_PATH. Se o recorte antigo atravessava meses, a migração distribui as linhas por mês e preserva o horário original de carga. Essa migração não significa que os meses foram consultados completos. Meses ainda não carregados são identificados no cabeçalho.

A atualização automática (AUTO_SYNC=1) agora busca o mês corrente completo no horário de Brasília, às 00h e 11h. Usa as transportadoras configuradas pela última carga do mês corrente; a carga histórica não altera essa configuração. Na primeira instalação usa as transportadoras da primeira carga bem-sucedida. O período avança na virada do mês. Atualizações históricas são somente manuais.

O seletor Consultar mês muda o mês exibido nas visões. Cabeçalho mostra período e última carga da base em exibição, além da última carga do mês corrente e do anterior, com horários identificados de Brasília. Uma nova carga histórica não altera o timestamp do atual. Falhas preservam o mês anteriormente salvo. Não há comparação combinada entre meses nesta versão.

Atualizar: envie os arquivos v1.9 ao GitHub, mantenha AUTO_SYNC=1, um worker e o disco persistente e faça deploy. Não recrie o disco. Faça uma carga manual do mês anterior.

## v1.10 — meses anteriores por quinzena (substitui a regra v1.9 de carga parcial)
No menu Atualizar dados, selecione um mês anterior e Parte do mês: Mês completo, 1ª quinzena (01–15) ou 2ª quinzena (16–último dia). A data final considera fevereiro e anos bissextos. A consulta substitui somente os agendamentos das datas escolhidas, preservando a outra quinzena e os outros meses. IDs repetidos não duplicam totais; IDs presentes na resposta substituem o registro anterior no mesmo mês. Uma resposta vazia bem-sucedida limpa somente o intervalo escolhido. Falhas não gravam dados parciais.

O cabeçalho informa quais quinzenas foram carregadas, cargas parciais e última atualização de cada uma. O total mensal reúne as quinzenas disponíveis; só é considerado carga mensal completa quando todas as datas foram consultadas, inclusive dias sem coleta. A abrangência por transportadora continua sendo a selecionada em cada carga; use as mesmas transportadoras nas duas quinzenas para comparar os totais. Alterações de data de agendamento feitas no SISGR exigem recarregar ambas as quinzenas para reconciliar o mês inteiro.

A automática permanece no mês corrente completo, às 00h e 11h de Brasília. Não dispara duas cargas históricas de uma vez: conclua uma quinzena antes de iniciar a outra. A divisão reduz o tamanho de cada operação, mas não garante menos consultas ao carregar as duas metades.

Deploy: substitua os arquivos pelo conteúdo v1.10, preserve DATABASE_PATH e disco, mantenha AUTO_SYNC=1 e um worker, faça deploy e Ctrl+F5. Não há nova variável.
