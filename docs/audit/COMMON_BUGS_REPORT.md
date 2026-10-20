> Relatório original da descoberta, anterior às correções. Consulte [correções e validação](FINDINGS_AND_FIXES.md) para o estado atual.

# Relatório combinado: interações e classes comuns de bugs

Investigação adicional em 20/10/2026, sobre `6073b656`.
Este documento reúne os seis achados da [primeira exploração](REPORT.md) e quatro
novos defeitos confirmados. Também separa dois cenários que ainda precisam de
validação por uma sequência nativa completa. Não houve correção de produção.

## Índice combinado, por impacto

| ID | Categoria | Defeito | Gravidade / confirmação |
| --- | --- | --- | --- |
| B08 | Loop / reconexão / eventos duplicados | Reconectar WebSocket acumula handlers exponencialmente | Alta; rede Qt real, teste limitado |
| B01 | Condicional / coordenadas / persistência | Resize de forma em container gera dimensão negativa que permanece ao reabrir | Alta; GUI e servidor real, relatório anterior |
| B07 | Integridade do histórico / persistência | Remapeamento de UUID altera texto da nota no manifesto e causa arquivamento do histórico ao reabrir | Alta; servidor real e reabertura |
| B09 | Exceção / carregamento | SVG válido com stroke-width fracionário interrompe carregamento de desenhos | Média; loader real Qt, sem encerramento completo comprovado |
| B02 | Condicional / bloqueio | Forma bloqueada pode ser redimensionada e deslocada | Média; relatório anterior |
| B03 | Estado de ferramenta | Retângulo → Elipse mantém modos simultâneos e desenha retângulo | Média; relatório anterior |
| B04 | Persistência visual | Borda semitransparente de forma perde alpha no SVG | Média; relatório anterior |
| B10 | Visual / hit testing / zoom | Parte visível da alça da linha move o corpo em vez de redimensionar | Média; Qt real, X11 e duas versões |
| B05 | Serialização de cor | Alpha baixo remove dígitos do RGB de notas/linhas | Baixa; relatório anterior |
| B06 | Condição de contorno | Keep aspect ratio aceita 1×1 para imagem 2:1 | Baixa; relatório anterior |

Os IDs B01–B06 mantêm as reproduções e evidências no relatório anterior. “Alta”
indica impacto funcional importante; não implica perda de discos ou configuração
interna de dispositivos. Nem todos os defeitos foram introduzidos pelo fork.

## Novos defeitos confirmados

### B07 — Remapeamento de UUID contamina conteúdo do histórico

**Estado inicial:** dois switches ligados; uma nota contém literalmente o UUID
do link, por exemplo `Reference 0620813c-5ad9-4c2e-aa39-e6c13c1579ef`.

**Sequência mínima:** criar a nota → remover o link → Undo → fechar/reabrir.
A preparação dos recursos e a exclusão usam a API real interceptada pelo histórico;
o Undo usa HistorySession. Não são necessárias VMs nem imagens de appliances.

**Esperado:** restaurar o link com o identificador alocado pelo servidor sem
alterar texto livre, preservando um manifesto equivalente à topologia salva.

**Observado no GNS3 Server 2.2.61:** o servidor atribuiu outro UUID ao link;
o texto da nota na GUI e no servidor permaneceu original, mas o SVG dessa nota
no **histórico** passou a conter o novo UUID. O histórico continuou marcado como
válido. Ao reabrir, o cursor passou de **5 para 0** e os registros anteriores
foram arquivados pelo mecanismo de recuperação, por divergência com a topologia.
A nota não foi apagada nem mudou de texto no teste real. O problema é a alteração
indevida do manifesto e a perda da navegação disponível após reabrir, não uma
mudança visual da nota que não ocorreu nessa execução.

**Causa confirmada:** `HistoryDocument.rebind_links` aplica substituição de UUIDs
recursivamente a **toda string**, incluindo texto livre dentro de SVG, em vez de
restringir a transformação aos campos de referência e metadados estruturais.
A etapa de replay reatribui IDs corretamente ao link, mas contamina recursos que
não participavam dessa operação. `remap_import` tem um padrão amplo semelhante;
o caso confirmado aqui é rebind_links, não toda possibilidade de importação.

Código: `gns3/history/model.py:222`, integração em `gns3/history/session.py:418`.

Evidências:

- [Estado real da GUI, servidor e histórico, antes/depois de reabrir](common/rebind-real-server.json).
- [Log da integração](common/rebind-server.log).
- [Probe real com projeto descartável](probe_server_rebinding.py).
- [Reprodução reduzida com transporte simulado](common/rebind-user-text.json).

Gravidade **alta**, por corromper a consistência persistida do histórico após uma
operação válida. Os arquivos arquivados são preservados; não se demonstrou
exclusão permanente desses backups.

### B08 — Reconexão WebSocket duplica callbacks exponencialmente

**Estado inicial:** projeto com controlador ainda marcado como conectado, mas
endpoint de notificações inacessível. Isso representa o intervalo em que a
conexão de notificações falhou e a aplicação ainda não declarou o controlador
inteiro desconectado.

**Reprodução controlada:** conectar o QWebSocket real a uma porta efêmera local
que acaba de ser liberada → observar ConnectionRefused → permitir oito erros →
marcar o controlador desconectado para encerrar o experimento.
Nenhum servidor pessoal é contatado e nenhum projeto persistido é aberto.

**Esperado:** quantidade estável de handlers, uma execução por mensagem e uma
política de retentativa que não amplifique o custo a cada falha.

**Observado:** em aproximadamente **25 ms**, o número de handlers de mensagem
cresceu **1 → 2 → 4 → 8 → 16 → 32 → 64 → 128**. O sinal de erro tinha 129
conexões contando o observador do próprio teste. Depois de interromper as
retentativas, uma única mensagem `ping` injetada no sinal Qt foi despachada
**128 vezes** ao processamento de eventos. Não são 128 mensagens enviadas por
um servidor: são 128 processamentos da mesma mensagem por conexões duplicadas.

**Causa confirmada:** `_websocket_error` reinicia imediatamente a escuta;
`_startListenNotifications` reutiliza o mesmo QWebSocket e reconecta seus sinais
sem desconectar os handlers anteriores. Cada erro passa a executar várias
retentativas, conectando ainda mais handlers. Não há backoff nessa rota.
O controlador contém estrutura semelhante; a medição dinâmica foi feita no
WebSocket do projeto, sem atribuir medidas não executadas ao controlador.

Código: `gns3/project.py:694–717`. Essa estrutura já existia no código base;
não é uma consequência necessária da implementação de histórico.

Evidências:

- [Qt 6.4.2: cronologia e número de despachos](common/notification-retry-6.4.2.json).
- [PyQt 6.10.2: compilação Qt 6.10.0 / runtime registrado no JSON](common/notification-retry-6.10.0.json).
- [Experimento limitado e reproduzível](probe_notification_retry.py).

Gravidade **alta** pelo crescimento de trabalho e processamento repetido. O teste
foi interrompido deliberadamente após oito erros: **não se afirma que houve um
travamento completo, OOM ou crash nativo**. Esses são impactos plausíveis se a
amplificação continuar, não resultados medidos.

### B09 — Espessura SVG fracionária interrompe o carregamento do projeto

**Entrada mínima:** desenho de linha com SVG válido contendo
`stroke="#123456" stroke-width="2.5"`, dimensões e demais campos de desenho válidos.

**Sequência:** carregar a lista de desenhos pelo callback real
`Project._listDrawingsCallback` → Topology.createDrawing → LineItem.fromSvg.

**Esperado:** carregar a linha de 2,5 unidades ou usar um fallback seguro sem
abortar a carga restante do projeto.

**Observado:** `ValueError: invalid literal for int() with base 10: '2.5'`.
A chamada de carga é interrompida, nenhum desenho é registrado e
`history.ready` permanece False. Não foi necessário XML corrompido: o valor é
uma espessura SVG legítima. As ferramentas atuais de linha só oferecem espessura
inteira; o caso é relevante para projetos/SVGs vindos de outras origens ou edições.
Não foi demonstrado que o seletor atual da GUI produza esse arquivo sozinho.

**Causa confirmada:** `_penFromSVGElement` usa `int(string)` diretamente e o loader
não contém a exceção por recurso para continuar carregando os demais desenhos.
Esse parser já existia no código base.

Código: `gns3/items/drawing_item.py:439`,
`gns3/project.py:602`, `gns3/topology.py::createDrawing`.

Evidência: [payload, exceção e estado do carregamento](common/fractional-svg-load.json).
Confirmado em Qt 6.4.2, Qt/PyQt mais recente disponível e X11.
Gravidade **média**, condicionada ao conteúdo do projeto. É uma **exceção que
interrompe a carga**, não um encerramento completo da aplicação comprovado.
O GNS3 possui um exception hook global; não se confundiu falha de callback com
um crash nativo do processo.

### B10 — Alça visível da linha e área de resize divergem com o zoom

**Estado inicial:** linha selecionada, pontas (0,0) e (60,0), zoom 500%.

**Sequência mínima:** clicar dentro da alça direita, 12 pixels à direita do seu
centro → arrastar 30 pixels → soltar.

**Esperado:** a ponta esquerda fica fixa; a ponta direita é redimensionada.
**Observado:** ambas as pontas se deslocam: **(0,0) → (6,0)** e
**(60,0) → (66,0)**. O controller escolhe o modo `body`, apesar de o clique estar
dentro do quadrado branco desenhado como alça.

**Causa confirmada:** LineItem pinta um quadrado de 8 unidades de cena, ampliado
pelo zoom. Em 500%, ele mede 40×40 pixels. CanvasLines.endpointAt aceita apenas
±7 pixels do centro, independentemente do tamanho pintado. Parte da alça oferece
assim uma operação diferente daquela indicada visualmente.

Código: `gns3/items/line_item.py:62` e `gns3/canvas_lines.py:92`.
Evidências: [estado antes/depois](common/zoom-handle.json),
[screenshot da alça ampliada](common/zoom-handle-before.png),
[após o arraste](common/zoom-handle-after.png).
Repetido em X11 e nas duas versões disponíveis do Qt. Gravidade **média**.

## Cenários suspeitos / confirmação ainda incompleta

### R01 — Respostas de escrita fora de ordem podem regredir o manifesto

Um transporte simulado aplicou duas escritas do mesmo dispositivo, x=10 e x=20,
nessa ordem, e entregou as confirmações em ordem inversa. O servidor terminou em
**x=20**, mas o histórico em **x=10**, sem marcar invalid.

O descompasso é reproduzível no componente: observe/capture não ordena essas
confirmações. Entretanto, a interface bloqueia várias novas ações enquanto há
requisições pendentes. Ainda não foi reduzida uma sequência **nativa da GUI** que
dispare exatamente essas duas escritas concorrentes e essa ordem de respostas.
Por isso o cenário continua como **risco operacional condicionado**, não é
contado como um quinto bug novo de uso confirmado.

Evidência: [ordem de callbacks e estados](common/reversed-ack.json).
Probe: `tests/history/probe_common_failures.py`.

### S01 — Resize de imagem interrompido por perda de foco

Permanece a suspeita da [primeira exploração](REPORT.md): o evento de foco
injetado deixou a imagem visualmente em 150×75, mas o SVG em 100×50. Falta
confirmar Alt+Tab, release em outra janela e retorno usando eventos nativos.
Não foi promovida a bug confirmado nesta rodada.

## Controles que não confirmaram defeito

- Callback de desenho após destruição da cena: a proteção `@qslot` ignorou o
  wrapper C++ já destruído. A leitura estática inicial sugeria possível acesso
  inválido, mas a execução descartou essa hipótese nesse caminho.
- Restauração de container agendada antes de trocar de projeto: o guard de
  identidade do projeto impediu restauração no projeto seguinte e limpou a flag.
- Os 6.020 passos gerados anteriores continuam documentados, sem alegar que
  encontrar zero falhas nessas invariantes prova correção global.

Não foi comprovado crash completo do processo nesta rodada. As categorias sem
achado confirmado não foram preenchidas com especulação para aumentar a lista.

## Escopo, isolamento e repetição

Produção permaneceu intacta. Novos módulos `probe_` são opt-in e não alteram a
coleta normal da suíte. O teste real criou e removeu seu próprio projeto no
servidor descartável. O teste de loop foi limitado e usou somente uma porta local
reservada/liberada pelo próprio script. Nenhum console/emulador foi operado.

Execuções adicionais:

```sh
QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/history/probe_common_failures.py tests/items/probe_common_failures.py
QT_QPA_PLATFORM=offscreen python3 exploration/probe_notification_retry.py
```

As falhas de assert nos probes são a evidência dos achados, não uma suíte nova
que deveria ficar verde antes de corrigir produção. Inspecionar os logs para
separar falhas do produto de problemas de configuração do harness.

Para B07, somente com servidor GNS3 2.2.61 **descartável** já iniciado:

```sh
XDG_CONFIG_HOME=/tmp/gns3-common-config XDG_DATA_HOME=/tmp/gns3-common-data QT_QPA_PLATFORM=xcb xvfb-run -a -s '-screen 0 1600x1000x24' python3 exploration/probe_server_rebinding.py --server http://127.0.0.1:3099
```

Logs: [componentes/history](common/history.log), [componentes/items](common/items.log),
[X11](common/items-x11.log), [Qt mais recente](common/items-qt610.log).
A investigação não cobre crashes em drivers gráficos, consumo de memória a longo
prazo, Windows/macOS, falhas de disco reais ou emuladores executando. Não foram
induzidas falhas destrutivas para testar esses itens.

Prioridade sugerida de correção: B08 (amplificação de eventos), B01 (geometria
inválida persistida), B07 (manifesto contaminado), depois os demais defeitos de
interação, carregamento e serialização.
