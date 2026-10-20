> Relatório original da descoberta, anterior às correções. Consulte [correções e validação](FINDINGS_AND_FIXES.md) para o estado atual.

# Investigação exploratória funcional — 20/10/2026

Base investigada: `6073b656073f79f86e56105edb39cb36013df446`.
**Resultado: seis defeitos confirmados e uma suspeita separada. Nenhum arquivo
versionado de produção foi alterado.** Os probes têm prefixo `probe_`, para não
introduzir falhas esperadas na descoberta normal de testes do projeto.

## Como a exploração foi conduzida

### Mapa de interações e dependências

| Camada | Estados/objetos compartilhados | Sequências priorizadas |
| --- | --- | --- |
| MainWindow / GraphicsView | QAction, flags `_adding_*`, foco, mouse capturado, seleção, navegação | Alternar ferramentas antes de desenhar; iniciar/interromper gestos |
| CanvasGroups / GroupItem | Pai Qt, posição local/cena, clipping, membros serializados, bloqueio | Agrupar, aninhar, mover, separar, mudar forma e restaurar |
| ShapeItem / LineItem / ImageItem | Geometria, transformações transitórias, estilo e SVG persistido | Resize por várias bordas; rotação; salvar/reconstruir após edição |
| HistorySession / HistoryDocument | Profundidade de operação, requisições pendentes, cursor, estados retidos | Movimentos repetidos, Undo/Redo, saltos, nova edição após Undo, limpeza, limite de 100 |
| Storage / HTTP / WebSocket | Codec, arquivos do projeto, confirmação do servidor, ecos e restauração da cena | Comparar estado atual e servidor, Undo/Redo e fechamento/reabertura |

### Invariantes usadas e suas ressalvas

- Geometria de uma forma editável não deve adquirir dimensões negativas em um
  arraste pequeno que não cruza a borda oposta. Esta restrição é coerente com os
  limites dos diálogos e com imagens/containers. Não se presumiu que o tamanho
  de um container devesse sempre expandir para conter seus filhos: clipping e
  limites fixos são comportamentos deliberados.
- O bloqueio deve impedir mudança de posição por um arraste. A reprodução usa
  a ação `lockActionSlot`, não um bloqueio inventado pelo teste. O problema
  confirmado também muda a posição de um item bloqueado, mesmo se alguém
  interpretar o bloqueio apenas como trava de posição.
- A última ferramenta escolhida deve determinar a próxima criação. A revisão
  das regras de `addLine` confirma o modelo de uma ferramenta de criação por vez.
  O caso foi validado pelo tipo efetivamente criado, não apenas por duas flags.
- Um ciclo SVG de gravação/leitura deve conservar cor/opacidade suportadas pelo
  próprio seletor da GUI. Não se exigiu identidade byte a byte de XML ou fontes
  visualmente idênticas em sistemas diferentes.
- Seleção de “Keep aspect ratio” deve conservar a razão também nos valores aceitos
  pelos campos. Não se exigiu que um valor inviável fosse aceito: rejeitá-lo ou
  ajustar ambos os campos seria válido.
- Hierarquias devem permanecer acíclicas e conservar pais/posições após save/restore
  sem uma nova edição. Não se exigiu que filhos continuassem no mesmo lugar após
  mudar deliberadamente a forma do container: `fitMembers` pode reposicioná-los.
- O histórico deve coincidir com um oráculo de estados retidos, descartar o futuro
  após nova edição e respeitar o limite de 100. Noops não criam novos estados.

### Geração e execução

Foram gerados **6.020 passos** com sementes reproduzíveis, incluindo passos sem
mudança quando suas pré-condições não se aplicavam:

- 25 sementes × 60 passos: grupos/aninhamento, movimentos, forma do container,
  separação e restauração de hierarquia.
- 20 sementes × 40 passos: mover linhas com origem fracionária, alterar pontas,
  rotacionar, serializar e reconstruir a geometria em coordenadas de cena.
- 12 sementes × 310 passos: edição repetida/agrupada, Undo, Redo, saltos de cursor,
  limpeza e roundtrip do codec. Os primeiros 130 passos forçam edições para
  ultrapassar o limite de 100. Um oráculo independente mantém os estados retidos
  e compara documento, cursor e transporte simulado após cada passo.

Nenhuma nova violação foi encontrada nessas três famílias de sequências geradas.
Isso é cobertura das invariantes verificadas, não prova de ausência de outros bugs.
As falhas abaixo vieram das matrizes de interação, borda e serialização adjacentes.

Eventos de mouse/ações Qt foram executados em widgets reais; o caso de ferramentas
usa MainWindow real. Para velocidade, os probes de hierarquia usam os fixtures do
projeto com transporte simulado. O caso B01 foi adicionalmente reproduzido com
HTTP Qt, WebSockets, servidor GNS3 2.2.61 e um projeto descartável real, incluindo
Undo/Redo e fechamento/reabertura. O projeto criado foi removido no encerramento.

Ambiente: Ubuntu 24.04.5, Python 3.12.3; Qt 6.4.2/PyQt 6.6.1. As falhas de
geometria/bloqueio/cores/proporção foram repetidas também em Qt/PyQt 6.10.2.
Geometria, bloqueio, cores, proporção e ferramenta errada foram confirmados em
X11/Xvfb. As interações são injetadas por QTest e QAction, sem mouse físico nem
PyAutoGUI nesta investigação. Configurações e servidor ficam em diretórios
isolados de /tmp. O autostart do servidor é desativado no harness de GUI.

## Defeitos confirmados

### B01 — Resize superior/esquerdo dentro de container gera geometria inválida

**Gravidade: alta**, pela gravação de geometria inválida e sua permanência após
reabrir, embora Undo consiga recuperar a forma. Não foi observada exclusão de
recursos ou perda de dados de dispositivos.

**Estado inicial:** retângulo 80×40 na posição de cena (160,120), agrupado em um
container retangular e com edição interna ativa.

**Reprodução mínima:** criar o retângulo → agrupá-lo → entrar no container →
arrastar sua borda superior cerca de 10 pixels para baixo → soltar.

**Esperado:** altura próxima de 30 e borda oposta preservada.
**Observado:** no probe Qt, altura **−61**, y de cena **221**. No servidor real,
a pequena diferença de margem/posição produziu altura **−59**, y **219,7**.
O SVG salvo contém `height="-59"`. Undo volta a 80×40; Redo e reabertura voltam
a **80×−59**. O histórico permanece válido: ele registra fielmente a edição
inválida produzida pelo resize.

**Causa sustentada pelo código e pelos dados:** `ShapeItem.mouseMoveEvent` mistura
`self.x()/self.y()` locais com `event.scenePos()` nas bordas superior/esquerda.
A condição de sinal também não impede a dimensão negativa obtida nessa sequência.
O mesmo arraste no nível raiz é um controle que não apresenta esse deslocamento.
O código de ShapeItem é idêntico ao do master comparado; os novos pais Qt dos
containers expõem uma suposição antiga de que posição local equivale à de cena.

Evidências: [JSON com estado do servidor, Undo/Redo e reabertura](server-geometry.json),
[captura inicial](server-geometry-before.png), [captura após resize](server-geometry-after.png),
[probe](probes/probe_exploratory_sequences.py),
[integração](probe_server_geometry.py).
Código envolvido: `gns3/items/shape_item.py`, linhas 106–123.

### B02 — Forma bloqueada continua redimensionável e pode mudar de posição

**Gravidade: média.**

**Reprodução mínima:** selecionar um retângulo 80×40 em (160,120) → acionar Lock →
arrastar a borda esquerda 10 pixels para a direita → soltar.

**Esperado:** posição e geometria preservadas.
**Observado:** posição **(171,120)** e tamanho **69×40**, ainda bloqueado.
A borda direita também redimensiona o retângulo bloqueado de 80×40 para 89×40.
Foi reproduzido no nível raiz e dentro de container.

**Causa confirmada:** ShapeItem arma `_edge` e aplica resize sem testar `locked()`.
A ausência de ItemIsMovable impede a movimentação padrão do Qt, mas não o
`setPos`/`setRect` manual desse handler. Imagens, linhas e containers possuem
proteções de resize por bloqueio, o que reforça a inconsistência funcional.

Evidência: [estado após Lock + arraste](run-latest/shape-False-True-left.json).
Código envolvido: `gns3/items/shape_item.py`, linhas 63–79 e 102–123.
O handler já existia no master; não atribuímos sua introdução às mudanças recentes.

### B03 — Alternar Retângulo → Elipse desenha um retângulo

**Gravidade: média.**

**Reprodução mínima:** ativar Draw rectangle → sem desenhar, ativar Draw ellipse →
arrastar uma área vazia → confirmar o diálogo.

**Esperado:** uma elipse.
**Observado:** um `RectangleItem`; as duas ferramentas ficam inicialmente marcadas.
Note → Rectangle também mantém dois modos armados, mas não é contado como outro
bug. Line → Rectangle e Rectangle → Line são controles que limpam o modo anterior.

**Causa confirmada:** `addRectangle`, `addEllipse` e `addNote` armam suas próprias
flags sem consumir as demais; mousePressEvent prioriza retângulo quando os dois
estão ativos. QAction não forma um grupo exclusivo para essas ferramentas.

Evidências: [duas flags ativas](tool-Rectangle-Ellipse.json),
[tipo efetivamente criado](run-latest/tool-wrong-shape.json),
[screenshot](run-latest/tool-wrong-shape.png), [confirmação em X11](tool-x11.log).
Componentes: `gns3/graphics_view.py::addRectangle/addEllipse/addNote/mousePressEvent`
e slots de ferramentas em `gns3/main_window.py`. A investigação não fez bisect
para determinar o primeiro commit em que isso passou a ocorrer.

### B04 — Bordas semitransparentes de formas ficam opacas após reconstrução

**Gravidade: média.**

**Reprodução mínima:** criar retângulo/elipse → escolher cor da borda com cerca de
50% de opacidade → salvar/recarregar o desenho, ou duplicá-lo pelo caminho SVG.

**Esperado:** cor e opacidade preservadas.
**Observado no roundtrip real de classes:** `#80123456` vira **`#ff123456`**.
O RGB é preservado nesse caso, mas a opacidade passa de aproximadamente 50% para
100%. O SVG emitido não possui stroke-opacity. A reprodução automatizada cobre
serialização/reconstrução, não uma exportação portátil completa deste caso.

**Causa confirmada:** `_styleSvg` grava RGB da borda sem seu alpha; o caminho
ShapeItem não recompõe a opacidade. LineItem tem tratamento próprio para esse
atributo, por isso essa perda de 50% não ocorre na linha de controle.

Evidência: [cores e SVGs gerados](run-latest/alpha-rect.json),
[elipse](run-latest/alpha-ellipse.json).
Código: `gns3/items/drawing_item.py::_styleSvg/_penFromSVGElement`.
Esse trecho de serialização já existia no código base.

### B05 — Opacidade muito baixa altera também o RGB de notas e linhas

**Gravidade: baixa**, por afetar valores próximos da transparência total.

**Reprodução mínima:** criar nota ou linha → escolher RGB (18,52,86) e alpha 1/255
→ serializar/reconstruir o desenho.

**Esperado:** `#01123456`.
**Observado:** **`#01023456`**. O SVG contém `stroke="#23456"` ou `fill="#23456"`,
perdendo um dígito do RGB. Foram explorados alpha 0,1,2,8,15,16,64,128,255;
a perda aparece nos valores baixos. Não é apenas arredondamento do canal alpha.

**Causa confirmada:** `hex(color.rgba())[4:]` pressupõe um número com oito dígitos,
mas hex omite zeros à esquerda. A extração de RGB remove então dígitos da cor.
É distinto de B04: aqui o próprio RGB muda mesmo quando alpha é reconstruído.

Evidências: [nota](run-latest/alpha-text.json), [linha](run-latest/alpha-line.json).
Código: `gns3/items/text_item.py::toSvg` e
`gns3/items/drawing_item.py::_styleSvg`. A expressão já existia no código base;
a linha nova reutiliza o helper.

### B06 — Keep aspect ratio aceita proporção errada no limite mínimo

**Gravidade: baixa.**

**Reprodução mínima:** importar imagem 100×50 → manter Keep aspect ratio marcado
→ mudar Width para **1** → confirmar.

**Esperado:** conservar 2:1 ajustando ambos os campos ou impedir o valor inviável.
**Observado:** o diálogo aceita **1×1**, razão 1:1, com a opção ainda marcada.
Larguras 2,3,100 e 1.000.000 foram controles que preservaram a razão.

**Causa confirmada:** widthChanged pede altura 0,5, mas o mínimo do campo é 1.
O QSignalBlocker impede ajuste compensatório da largura após esse clamp.

Evidência: [log da matriz de limites](run-latest/image-ratio.log).
Código: `gns3/dialogs/image_properties_dialog.py`, linhas 31–39.

## Suspeita que ainda precisa de confirmação por interação nativa

### S01 — Imagem mantém transformação transitória após resize interrompido

Sequência injetada em Qt: iniciar resize da imagem 100×50 → mover até 150×75 →
enviar FocusOut sem release na view → voltar e clicar no corpo da imagem.
O gráfico permanece **150×75**, com escala 1,5; o SVG reconstruído mede **100×50**
e `_resize_edge` já é None.

O descompasso é real nessa sequência de eventos. Ainda **não foi demonstrado**
que Alt+Tab/release em outra janela produza exatamente essa sequência no sistema
operacional. Não contamos S01 entre os seis bugs confirmados por uso reproduzível.

Hipótese: GraphicsView.focusOutEvent finaliza linhas/containers, mas não o preview
de ImageItem. O próximo mousePress limpa `_resize_edge` sem consolidar ou reverter
a transformação. É preciso validar desativação de janela e liberação de captura
com entrada nativa antes de propor correção.

Evidência: [estado](run-latest/image-interrupted.json),
[probe](probes/probe_exploratory_sequences.py).

## Limitações, controles e reprodução

- Nesta rodada não houve execução em Windows/macOS nem compositor Wayland.
- Dispositivos em execução, console, QEMU/VMware/VirtualBox, falhas de compute,
  duplicação assíncrona de dispositivos e remoção de links com interfaces reais
  ficaram fora da geração exploratória. Não se afirma que estejam corretos.
- Seleção/gestos foram usados para reproduzir falhas, mas não houve fuzzer
  exaustivo de foco/menus contextuais, objetos excluídos durante callbacks ou
  eventos de vários botões simultâneos.
- A geração de histórico usa transporte simulado e roundtrip do codec. Não é
  equivalente a 3.720 operações contra servidor real nem substitui exportação/
  importação de todos os cenários. O teste real de servidor é o de B01.
- Erros iniciais do harness (singletons Qt entre casos e autostart local em
  ambiente restrito) foram separados dos achados e não contam como bugs do produto.
  O runner usa processos novos por família, configuração temporária e autostart
  desativado no fixture. As capturas de geometria forçam renderização da janela;
  são adequadas para dimensões, não para detectar rastros de framebuffer.
- A suíte existente continua separada: **537 aprovados, 1 ignorado**.

Rodar a geração e os casos reduzidos:

```sh
python3 exploration/run_probes.py
# Com display X11 isolado, os mesmos casos Qt:
QT_QPA_PLATFORM=xcb xvfb-run -a -s '-screen 0 1600x1000x24' python3 exploration/run_probes.py exploration/run-x11
```

O runner grava manifest.json, logs e evidências em run-latest (ou diretório
fornecido). **Falhas de assert são esperadas nos casos que expõem os bugs**; o
runner não converte todo retorno não zero em “bug confirmado”. Os logs precisam
ser inspecionados para excluir erros do próprio teste.

Com servidor descartável GNS3 2.2.61 já iniciado e PyQt/Pillow disponíveis:

```sh
XDG_CONFIG_HOME=/tmp/gns3-exploratory-config XDG_DATA_HOME=/tmp/gns3-exploratory-data QT_QPA_PLATFORM=xcb xvfb-run -a -s '-screen 0 1600x1000x24' python3 exploration/probe_server_geometry.py --server http://127.0.0.1:3099
```

O probe cria/remove somente seu próprio projeto. Ele não inicia o servidor.
Os arquivos em exploration e os dois módulos probe_ são material de investigação;
não foram aplicadas correções nem feitos commits/push nesta etapa.

## Complemento: classes comuns de bugs

A investigação foi ampliada para reconexões/loops, callbacks fora de ordem,
exceções de carregamento, hit testing visual e persistência do histórico.
O [relatório combinado](COMMON_BUGS_REPORT.md) reúne os seis achados acima e os
novos B07–B10, separando riscos condicionados dos defeitos confirmados.
