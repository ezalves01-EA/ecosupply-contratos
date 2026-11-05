# Publicação no Render — v1.8

1. Crie um repositório exclusivo para este painel e envie o conteúdo desta pasta (render.yaml na raiz). Não envie instance, .venv nem tokens.
2. No Render, New → Blueprint, conecte o repositório e revise o plano e o disco antes de criar. O blueprint solicita serviço Starter e disco persistente de 1 GB, ambos sujeitos à cobrança exibida pelo Render. Não reutilize o banco dos outros sistemas.
3. Preencha SISGR_TOKEN com o token atual, DASHBOARD_USER com seu usuário e DASHBOARD_PASSWORD_HASH com a saída de `python gerar_senha.py`. Configure como variáveis secretas, nunca no Git. O token publicado anteriormente deve ser substituído.
4. Publique. Acesse a URL HTTPS gerada e entre com usuário/senha. O menu Atualizar dados do SISGR concentra atualização, qualidade e conferência de placas. As demais visões mostram período e última atualização.
5. Sincronize primeiro um dia e confira os totais. A instalação começa vazia. Para migrar a base local, pare atualizações e copie instance/painel.sqlite para /var/data/painel.sqlite pelo shell do serviço antes de reiniciar; não publique esse arquivo no Git.

SQLite fica no disco deste serviço, separado dos bancos existentes. Um único worker e uma única instância são obrigatórios: lock, estado e thread da atualização ficam no processo. Não use autoscaling nem múltiplos workers. A sincronização continua manual; não há agendamento automático. Reinício/deploy interrompe consulta em andamento e preserva a última base concluída; repita depois. O disco mantém a base entre deploys, mas não substitui backup.

Para domínio próprio, adicione o hostname exato em ALLOWED_HOSTS, separado por vírgula. O hostname padrão do Render é reconhecido automaticamente. Use HTTPS. Todos os usuários configurados nesta versão têm acesso à atualização; há um único usuário por instalação.

Verificação local: `python -m unittest discover -v` e `node test_driver_metrics.cjs`. Testes de nuvem são simulados; a publicação real e a consulta autenticada ainda precisam ser verificadas na sua conta.

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

## v1.11 — quinzena manual no mês atual e mudança de mês por ID
Mês completo, 1ª e 2ª quinzenas agora podem ser escolhidos manualmente também no mês corrente. A automática continua no mês corrente completo às 00h e 11h de Brasília.

A gravação substitui apenas as datas consultadas. Exceção: se a resposta trouxer um ID de agendamento já salvo em outro mês, o registro desse ID é removido do mês antigo e atualizado no mês de destino. As demais linhas e a data da última carga do mês antigo são preservadas; contagens auxiliares são recalculadas. Tudo ocorre na mesma transação SQLite; falha ou resposta inválida não aplica a mudança.

A mudança entre meses só é confirmada quando o mês/período de destino é consultado e a API devolve o mesmo ID com a nova data. Não há consulta individual de todos os IDs antigos para procurar mudanças em meses fora da carga. Se o SISGR gerar um ID novo, não se presume que seja o mesmo agendamento.

Atualize os arquivos, mantenha disco e variáveis existentes, faça deploy e Ctrl+F5. Nenhuma variável nova.

## v1.12 — visão Reagendamento em lote com executor local
Menu com pendentes ROTA da base mensal, filtros já existentes de cidade/motorista/data e demais campos, busca, marcação individual, seleção do resultado filtrado e adição de IDs colados (somente pendentes nos filtros). Seleção mantida entre filtros, limpa ao trocar mês/base, limitada a 100. O resumo exibe todos os selecionados. Status é fixo ROTA nesta visão, ignorando o filtro de status geral.

A tela baixa um plano JSON revisado, sem credenciais. O botão Baixar executor local fornece v3; extraia no computador e copie historico.sqlite da v2, se houver. Abra INICIAR_LOTE_DO_PAINEL e escolha o plano. O envio continua pela sessão Chrome do computador e exige conferência e confirmação local. O servidor Render não faz POST no SISGR.

Após confirmar as novas datas no SISGR, sincronize os períodos de origem e destino para atualizar o painel com dados oficiais. Não há importação automática do relatório ou alteração otimista de status/data. O seletor de mês determina a base consultada; pendentes não carregados não aparecem.

Deploy mantém disco e variáveis. Substitua arquivos, incluindo reschedule.js e downloads/Ecosupply_Executor_Painel_v3.zip. O download exige o login normal do painel. Não envie historico.sqlite, cookies ou resultados para o Git.

## v1.13 — extensão para reagendar pela aba SISGR
Inclui downloads/Ecosupply_Extensao_SISGR_v1.zip e web/extension.js. No menu de reagendamento, baixe a extensão, extraia, abra chrome://extensions (ou edge://extensions), habilite Modo do desenvolvedor e Carregar sem compactação; selecione a pasta com manifest.json. Depois recarregue painel e SISGR no mesmo perfil Chrome/Edge. Extensão não compatível com Firefox nesta versão.

Painel integrado: https://ecosupply-logistica-api.onrender.com/. No menu, clique Conectar extensão. Selecione IDs e dados, marque a conferência e Enviar para conferência na extensão. Ela abre uma aba própria com os dados; confira, confirme e mantenha aberta até terminar. Os resultados aparecem no painel. Senha/cookies não são enviados ao Render. Cada ID/data tem intenção persistida no perfil antes do envio; erros e respostas incertas param o lote sem repetição automática.

A versão ainda não foi validada em execução autenticada real. Comece com poucos IDs desejados. A data final deve ser conferida no SISGR. Atualize origem/destino pela sincronização para refletir dados oficiais. Histórico da extensão é separado do executor Python e de outros perfis/máquinas. Não rode o mesmo lote simultaneamente em perfis diferentes.

Serviço e variáveis do Render continuam os mesmos. Substitua o pacote, incluindo downloads e web, e faça deploy. Usuários precisam instalar a extensão uma vez em seus computadores. Não remover o disco persistente.
