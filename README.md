
## Versão 1.14 — roteiros e conclusão semanal

Na aba Mapas e regiões, o novo quadro Caminhão × semana, mapa dos municípios e lista de periodicidades complementam o mapa operacional existente. O filtro Rota aceita múltiplas opções e se combina com os demais filtros. O CSV inclui rota e semana planejada.

O cadastro em `data/rotas_planejadas.json` foi importado da planilha Ecosupply_Base_Unificada_Rotas_MT_Com_Regiao(1).xlsx: 66 vínculos, 62 localidades, 4 caminhões e 11 roteiros. O cruzamento usa cidade e placa, ignorando acentos e pontuação; quando houver UF, também deve coincidir. As regiões existentes são preservadas. Combinações fora do cadastro recebem **Rota a definir**, continuam nos totais e podem ser filtradas. A classificação ocorre na leitura, inclusive nas bases já salvas, sem exigir nova consulta ao SISGR nem alterar o histórico de meses.

Rondonópolis/DAH-7H63 consta nas semanas 2 e 4: recebe **Rota a confirmar**, com os dois candidatos, sem atribuição automática a uma das semanas. A periodicidade não determina o mês ativo; não se inventa fase para atendimentos bimestrais, trimestrais ou outros.

Conclusão da semana = IDs REALIZADO ou EFETIVADO / todos os IDs classificados naquela semana na seleção, incluindo outros status. Cada ID conta uma vez. Semana significa a semana do roteiro cadastrado, não semana de calendário nem data efetiva da coleta. O percentual ignora o filtro de status, respeita os demais e mede apenas a base carregada. Sem IDs, exibe —. Rota a definir/confirmar permanece nos totais gerais, fora dos indicadores semanais; a cobertura de classificação aparece abaixo dos cartões.

O mapa novo mostra cobertura municipal, sem calcular sequência ou trajeto rodoviário. A malha MT usada não contém Cerejeiras/RO, Vilhena/RO nem o distrito Espigão do Leste; essas localidades permanecem na lista.

Atualização: substituir os arquivos do projeto pelo conteúdo deste pacote, incluindo `routes.py`, `data/rotas_planejadas.json` e os novos scripts de `web/`. Preservar as variáveis do Render e o banco no disco persistente. Esta versão não exige reinstalar a extensão de reagendamento. O pacote não publica automaticamente no GitHub ou no Render.


## Versão 1.15 — associação e filtros dependentes

Substitui o cadastro pela planilha Ecosupply_Base_Unificada_Rotas_MT_Com_Regiao(2).xlsx: 68 vínculos, 64 localidades, 6 caminhões e 13 roteiros. Inclui CUIABA/HTP-0171 e VARZEA GRANDE/HTP-0B45, semana 1 e periodicidade SEMANAL exatamente como cadastradas. Não replica automaticamente para semanas 2–4.

A associação prioriza cidade + placa. Sem essa combinação, busca os roteiros da cidade, mantendo a checagem de UF. Uma rota única é associada mesmo quando o caminhão do agendamento é outro; a placa real do SISGR permanece intacta. Mais de uma possibilidade fica Rota a confirmar, mas o filtro de qualquer rota candidata inclui o ID uma única vez. Cidades fora do cadastro continuam Rota a definir. A semana ambígua fica fora do percentual semanal até definição. O campo routeSource distingue Cidade de Cidade + placa.

Filtros dependentes: cada lista mostra os valores compatíveis com os outros filtros e período; ignora sua própria seleção para permitir escolher múltiplos valores. Seleções já marcadas permanecem visíveis para poder limpar, mesmo sem correspondência. Na aba de reagendamento, as opções derivam apenas dos pendentes em ROTA. O quadro Caminhão × semana recebeu tons de azul alinhados ao painel.

Após implantar os arquivos e concluir o deploy, recarregar o navegador com Ctrl+F5. Não é necessário sincronizar novamente o SISGR para reclassificar os dados já salvos. Preservar banco e variáveis de ambiente.

## Versão 1.16 — semana pela data e Auditoria

Esta regra substitui a regra de semana das versões anteriores. A data do agendamento (`date`), não a data de realização, define `scheduleWeek` e `routeWeek`: dias 1–7 = 1, 8–14 = 2, 15–21 = 3 e 22 ao fim do mês = 4. Datas inválidas ficam sem semana. Cada ID continua único; reagendar muda sua semana após atualizar a base salva.

Cuiabá/HTP-0171 e Várzea Grande/HTP-0B45 passam a ter semanas 1–4. O cadastro contém agora 74 vínculos e 19 roteiros, preservando os demais registros da planilha. As seis linhas novas foram incluídas conforme solicitação do usuário.

Prioriza cidade/UF + placa; sem combinação exata, busca pela cidade/UF. A família do roteiro é mantida e o sufixo segue a semana da data, mesmo se essa semana não estiver prevista na planilha. Exemplo: Rondonópolis/DAH-7H63, dia 3: DAH-7H63_1, Semana divergente, semanas previstas 2 e 4. Dias 10 e 24 ficam Conforme. Havendo múltiplas famílias sem resolução pela data, sinaliza Rota ambígua. Sem cidade cadastrada, Rota a definir. A placa real nunca é substituída pela placa do planejamento.

Novo menu Auditoria de semanas compara, por ID, data/semana agendada, semanas previstas, cidade, placa real, motorista, rota, origem da associação e resultado. Respeita filtros globais, permite filtrar resultado e não altera datas no SISGR. Semana divergente é um ponto para conferência, não confirmação de erro; Sem rota cadastrada não é divergência de data. O CSV global inclui semana agendada, semanas previstas e resultado da auditoria. Os percentuais semanais usam a semana agendada, inclusive para cidades sem roteiro; o detalhamento por roteiro exige associação resolvida.

Implantar os arquivos do pacote preservando banco e variáveis do Render. Ctrl+F5 após deploy. A classificação é recalculada ao ler a base existente, sem nova sincronização. A auditoria reflete a última sincronização, não consulta alterações de data ao vivo.

## Versão 1.17 — cancelamento de agendamentos

O campo canceled da API é armazenado e normalizado (true, 1, '1', 'true', 'sim', 'yes', 's'), além de canceled_at e status CANCELADO/CANCELADA/CANCELED/CANCELLED. Cancelamento prevalece sobre o status operacional. Armazena originalStatus para rastreabilidade. Valores false, 0, '0', 'false', 'não' e vazios não cancelam por si só.

O status CANCELADO aparece no filtro e em um cartão da evolução. Registros permanecem no histórico, exportação e tabelas da base. Os indicadores operacionais, mapas/gráficos de programação, conclusão, volumes, produtividade, FALTA EFETIVAR, conclusão semanal, seleção para reagendamento e divergências da auditoria excluem cancelados. Totais da evolução/histórico incluem cancelados; o total operacional de agendamentos não inclui. Uma seleção apenas de cancelados resulta em zero indicadores operacionais, mantendo o histórico visível.

O cancelamento é reavaliado nas bases existentes se elas já contiverem canceled, canceled_at ou status de cancelamento. Bases antigas que não armazenaram esses campos precisam de nova sincronização dos respectivos períodos para descobrir cancelamentos. Não é possível deduzir os cancelados apenas da rota, assinatura ou data. As mesmas regras de preservação de outros meses permanecem.

Implantar o pacote no GitHub/Render, preservar banco e variáveis, e recarregar com Ctrl+F5. Para meses antigos, atualizar manualmente o mês ou a quinzena desejada. A atualização automática continua no mês atual.

## Versão 1.18 — identificador de rota em lote

Menu Rota em lote: usa filtros globais, permite selecionar até 100 coletas em ROTA, mantém seleção fora dos filtros com contador e exige novo identificador e conferência. Exclui cancelados. Envia plano à extensão v1.1 para revisão e confirmação, sem envio automático na preparação.

A operação observada no SISGR é POST /rotas/trocarMotoristaVeiculoAction, com identificadorRota e agendamentos[], mais os IDs individuais de transportadora/veículo/motorista preservados da base salva. Por isso, a conferência deve verificar a alocação atual no SISGR. Não envia campos de alteração de data. Uma resposta que peça confirmarTrocaVeiculoDistinto interrompe o lote sem confirmação automática. Não há consulta independente do resultado final: após execução, conferir rota, data e alocação no SISGR e sincronizar o período.

A sincronização agora salva sisgrRoute quando a listagem contém identificadorRota; ausência é exibida como Não disponível na base. A descoberta desse campo foi confirmada apenas no detalhe de um ID. Esta versão não faz consultas extras por ID para preencher campos ausentes, evitando ampliar o consumo da API. A rota calculada e o identificador SISGR permanecem distintos.

Atualizar o site pelo pacote e a extensão usando /sisgr-extension.zip (v1.1). Substituir arquivos na mesma pasta da extensão e clicar Recarregar em chrome://extensions ou edge://extensions; não desinstalar, para manter histórico de tentativas. Preservar banco/variáveis do Render e usar Ctrl+F5. Nenhuma alteração real de rota foi executada durante os testes de desenvolvimento.

## Versão 1.19 — conclusão por identificador SISGR e cancelados

Novo menu Conclusão por rota SISGR: agrupa somente coletas pelo identificador recebido da API. Mostra previstas ativas, feitas (REALIZADO + EFETIVADO), pendentes ROTA, atrasadas (ROTA com data agendada anterior a hoje no fuso Cuiabá), outros ativos, cancelados e conclusão. Cada ID conta uma vez; cancelados ficam fora do denominador e do numerador. Rota com apenas cancelados exibe percentual —. Clique no identificador para aplicar filtro global e ver seus agendamentos, cidades, motoristas, placas e status. Detalhamento inclui cancelados. Percentuais ignoram o filtro de status e respeitam os demais filtros. Medem somente a base carregada no período, não capacidade ou atendimento de toda a carteira.

Filtros globais novos, com múltipla seleção e opções dependentes: Identificador de rota SISGR e Semana agendada. Rota calculada continua separada. Identificador usa texto recebido, sem converter nomes/placas nem inferir pela planilha. Sem identificador de rota agrupa campo vazio ou ausente na última sincronização. Bases antigas exigem sincronização para receber sisgrRoute; se a API de listagem não retornar esse campo, a base permanece Sem identificador, sem consultas extras automáticas por ID. O detalhe já foi observado contendo identificadorRota, mas isso não comprova cobertura da listagem.

Cancelados adicionados como coluna/valor nos detalhamentos de conclusão por cidade/região, frota, pontos, volume por cidade, performance, semanas/roteiros e motoristas. Totais ativos e percentuais excluem cancelados; o histórico e as colunas separadas os preservam. No detalhamento realizado dos motoristas, a coluna Cancelados (data agendada) usa a data agendada no intervalo De/Até: não há data realizada confiável para cancelados. No quadro de motoristas por tipo, usa o período próprio de agendamento do quadro. Cancelados não somam dias ou produção.

Instalar os arquivos do pacote no GitHub/Render, preservando banco e variáveis. Usar Ctrl+F5 após deploy. Esta versão mantém a extensão v1.1 já entregue na v1.18; não requer nova instalação para os filtros/indicadores. Para preencher identificador SISGR e cancelamentos antes ausentes, sincronizar o período desejado. Não foram executadas alterações reais no SISGR durante o desenvolvimento.

## Versão 1.20 — recorrências em lote por planilha

Novo menu Recorrências em lote, independente dos filtros e mês da base. Importar primeira aba de XLSX ou CSV: A=ID da recorrência; B=identificador desejado. Cabeçalho opcional. B vazia solicita cálculo pela placa do veículo vinculado e semana da Próxima data. Regra 1–7, 8–14, 15–21, 22 ao fim do mês. Exemplo: placa HTP-0145 e próxima data 06/01/2027 → HTP-0145_1. Um B explícito é enviado como informado (sem espaços nas pontas).

Validação bloqueia o arquivo inteiro se houver IDs repetidos, IDs inválidos, fórmulas em A/B, conteúdo em C ou mais de 100 IDs. Limite de arquivo 1,9 MB no navegador e 2 MB no servidor; XLSX descompactado até 20 MB, até 1000 linhas. O upload apenas valida em memória, sem salvar planilha ou alterar a base. Modelo CSV A/B disponível na tela. .xls não é aceito; salvar como XLSX/CSV.

Extensão v1.2 lê GET /recorrentes/editar/ID, mostra atual → proposto e bloqueia formulário incompleto, próxima data inválida ou placa automática ausente/ambígua. B explícito não exige extração da placa. Clique Ler / continuar leitura e depois confirme apenas as linhas prontas. Iguais e bloqueadas não são enviadas. A cada envio, relê os controles e bloqueia mudanças desde a conferência. Reenvia FormData preservando todos os demais campos submetidos, substituindo somente identificadorRota; depois verifica identificador e demais controles por nova leitura. Formulários com controles carregados apenas por JavaScript podem exigir adaptação depois de um teste real; nesse caso bloqueia sem salvar. Não altera agendamentos já gerados.

Dependências novas: openpyxl 3.1.5 e defusedxml 0.7.1. Render deve instalar requirements.txt atualizado. Nova extensão no download /sisgr-extension.zip (arquivo v3, versão 1.2). Substituir arquivos na MESMA pasta e Recarregar extensão; preservar perfil e histórico. Não foi feito teste de escrita real no SISGR. Começar com um ID de recorrência de teste e conferir todos os campos após o envio. Preservar banco e variáveis do Render, usar Ctrl+F5 após deploy.
