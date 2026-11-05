# Ecosupply — extensão SISGR v1

## Instalar uma vez no Chrome ou Edge
1. Extraia este ZIP em uma pasta fixa. Não apague nem mova a pasta depois de instalar.
2. No Chrome, abra chrome://extensions. No Edge, edge://extensions.
3. Ative Modo do desenvolvedor.
4. Clique Carregar sem compactação e selecione a pasta que contém manifest.json.
5. Abra/recarregue o painel: https://ecosupply-logistica-api.onrender.com/.
6. No mesmo perfil do navegador, abra https://ecosupply.sisgr.com/ e faça login normalmente.

Esta versão é para Chrome/Edge. Não é pacote instalável do Firefox. Se estiver usando Firefox para o painel, abra painel e SISGR no Chrome/Edge com a extensão instalada. Não precisa Python.

## Reagendar
1. No painel v1.13, vá a Reagendamento em lote. Clique Conectar extensão se necessário.
2. Escolha mês, cidade, motorista, datas e os IDs ROTA desejados (até 100).
3. Informe nova data, motivo e saída do veículo. Confira o resumo completo e marque a confirmação.
4. Clique Enviar para conferência na extensão. Uma aba própria da extensão abre com os dados.
5. Confira no SISGR se os IDs continuam pendentes e marque a conferência da extensão. Clique Confirmar envio no SISGR.
6. Mantenha essa aba aberta. O lote envia um ID por vez, aguardando pelo menos 3 segundos entre solicitações.
7. Acompanhe resultados na extensão e no painel. Use Baixar relatório para conservar os resultados.
8. Confira as novas datas no SISGR. Sincronize origem e destino no painel para atualizar a base com a API. A extensão não altera o banco do painel pelo simples aceite.

## Sessão e permissões
Apenas o endereço padrão do painel acima e o domínio SISGR da Ecosupply estão integrados. Domínio próprio exige ajustar manifest.json, bridge.js e core.js e reinstalar/recarregar a extensão. Não amplie para todos os sites. A extensão pede scripting, storage e permissão para atuar no SISGR; não pede permissão de ler cookies. Ela usa a sessão da aba e não transfere senha/cookie ao Render. Não há token da API nem credenciais no código.

Use somente uma aba SISGR logada por perfil para evitar ambiguidade; o lote fixa a aba escolhida no início. Se sessão expirar, retornar login/HTML, ocorrer erro HTTP, timeout de 20 segundos ou resposta sem confirmação por ID, o lote para. Não tenta contornar autenticação nem repetir uma solicitação. Timeout pode ocorrer após gravação no servidor: confira o cadastro antes de qualquer nova tentativa.

O status ROTA e a data de origem vêm da base salva, não de uma consulta ao vivo antes do POST. A conferência local é obrigatória. A rota POST /agendamentos/reagendar e os campos foram observados nos testes locais anteriores; ainda é necessário um teste real desta extensão com poucos IDs. Não é uma integração oficialmente documentada da API pública SISGR.

## Histórico e interrupções
Intenção de cada ID/data é gravada no armazenamento da extensão ANTES do envio. O mesmo ID para a mesma data não é reenviado automaticamente nesse perfil, mesmo se o motivo mudar. Os registros locais não importam historico.sqlite do executor Python; não selecione de novo itens já concluídos com o executor para a mesma data.

Se fechar a aba da extensão, use seu ícone na barra de extensões para reabrir o último lote. Um envio com resultado desconhecido bloqueia o lote para conferência. Não limpe o armazenamento, reinstale ou troque de perfil para forçar reenvio. Cancelar/interromper não desfaz envios já aceitos; se clicar durante um envio, ele pode terminar antes da interrupção.

Histórico e resultados ficam neste perfil e não são compartilhados entre computadores. Não rode o mesmo lote em máquinas/perfis diferentes. Sessão fechada ou suspensão do computador interrompe o fluxo; a extensão não é um agendador em nuvem.

A seleção de pendentes e o botão Enviar ficam no painel, mas o Chrome exige a confirmação e execução pela extensão instalada. Se já houver um lote em revisão/execução, finalize/cancele esse antes de preparar outro. O antigo executor local por arquivo continua como alternativa.

## Validação
Testes simulados: node test_extension.cjs. Incluem rejeição de origem indevida, bloqueio de envio pelo painel sem revisão, validação de plano, ID repetido, datas inválidas, pausa, interrupção, histórico, recuperação de intenção incompleta e transporte de formulário na rota fixa. Não houve acesso autenticado nem alteração no SISGR pelo assistente durante a construção desta versão.

## Versão 1.1 — identificador de rota em lote

Recebe planos ecosupply-route-plan do menu Rota em lote. A conferência mostra identificador atual (quando disponível), novo identificador e IDs de transportadora, veículo e motorista de cada agendamento. Estes IDs vêm da base salva: confira no SISGR antes de confirmar; a extensão não garante que a alocação ainda esteja igual em tempo real.

Envia um ID por POST a /rotas/trocarMotoristaVeiculoAction. data_de/data_ate são filtros da tela; não envia novaData nem schedule_date. Mantém os IDs de alocação informados no plano. Só considera aceita a resposta erro=false, mensagem='Alteração realizada.' e confirmarTrocaVeiculoDistinto=false. Confirmação de veículo diferente, falha ou resposta inesperada interrompe o lote. Não copia cookies; usa a sessão da aba SISGR. Não repete automaticamente uma tentativa para mesmo ID/identificador. Conferir resultado e alocação no SISGR após execução.

Para atualizar uma extensão já instalada, substitua os arquivos na mesma pasta e clique Recarregar em chrome://extensions (ou edge://extensions). Mantenha o mesmo perfil/pasta para preservar o histórico local. Não remova a extensão para atualizar. Recarregue também o painel. Os fluxos de data continuam disponíveis.

## Versão 1.2 — recorrências importadas A/B

A=ID da recorrência, B=identificador explícito. B vazia usa a placa exibida no veículo vinculado e a semana da Próxima data: 1–7, 8–14, 15–21, 22 ao fim do mês. Somente uma placa reconhecida no formulário permite automático; múltiplas placas/placa ausente bloqueiam automático. B explícita dispensa extrair a placa, mas não dispensa um formulário válido e uma próxima data válida.

A aba da extensão começa na etapa de leitura. Clique Ler / continuar leitura. Não há POST nessa etapa. A conferência mostra atual → novo, placa, próxima data, origem e bloqueios. O botão Confirmar envia apenas linhas prontas; iguais são ignoradas e bloqueadas não são enviadas. A operação não altera agendamentos já gerados.

GET /recorrentes/editar/ID lê o formulário atual. Apenas os controles submetidos pelo próprio formulário são serializados com FormData, preservando campos repetidos, produtos, quantidades, receptores, rota, periodicidade, próxima data e os campos ocultos. O único valor substituído é identificadorRota. Se o formulário depender de controles que não vieram no HTML ou não for reconhecido, a leitura bloqueia sem tentar preencher dados por suposição. Os dados de formulário e cookies não são exportados nem persistidos; a extensão armazena a impressão digital do formulário e os dados necessários à conferência.

Antes do POST /recorrentes/salvar/ID, relê e compara o formulário com a impressão digital da conferência. Se mudou, não envia. Após resposta erro=false e mensagem='Solicitação realizada.', relê para verificar identificador e impressão digital dos demais controles. Campos ocultos dinâmicos podem provocar bloqueio mesmo sem edição manual; nesse caso não force repetição. Timeout/falha interrompe e exige conferência no SISGR; não há reenvio automático.

Recarregar na MESMA pasta e perfil para preservar tentativas. Testado com formulários simulados; primeiro validar uma recorrência no SISGR. Este fluxo edita o cadastro recorrente; não atualiza retroativamente os agendamentos existentes.
