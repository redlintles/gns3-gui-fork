# Notificações transitórias de links e descrições de renomeação

## Reprodução e causa — 20/10/2026

O console imprimia `Invalid event received: A history link needs two endpoints`
ao criar links de uma topologia comum. Não era necessário um projeto antigo ou
histórico corrompido.

No servidor GNS3 2.2.61, `handlers/api/controller/link_handler.py::LinkHandler.create`
aplica `link_style` antes de chamar `link.add_node` para cada ponta.
`controller/link.py::update_link_style` emite `link.updated` imediatamente,
com `nodes: []`. Depois da segunda ponta, o servidor emite `link.created` completo.
A GUI oferece estilo padrão ao criar links, tornando esse caminho habitual.

Em `gns3/project.py::_event_received`, a notificação incompleta chegava a
`HistorySession.observe` e então a `model.canonical`, que corretamente exige duas
pontas. A exceção era capturada pelo receptor WebSocket e impressa no console.
A screenshot do usuário é compatível com esse fluxo; a causa foi confirmada com
HTTP/WebSocket reais em um projeto descartável, registrado no log anexado.

## Correções

- O dispatcher descarta apenas `link.updated` externos com uma lista explícita de
  zero ou uma ponta. Não entrega estado de construção ao histórico nem ao objeto
  visual. `link.created`, respostas HTTP e arquivos persistidos continuam sujeitos
  à validação estrita. Updates parciais sem o campo nodes continuam aceitos.
- A resposta completa/`link.created` registra normalmente a criação. A correção não
  altera o servidor nem o formato dos projetos. Falhas na criação não produzem
  links fantasmas a partir da notificação intermediária.
- `model.description` identifica alteração do campo `name` de um dispositivo antes
  de aplicar o hint genérico do diálogo. Exemplo: `Changed Router1 hostname to Router2`.
  O nome anterior identifica X e o novo nome identifica Y. Atualizações secundárias
  do label na mesma operação não ocultam a descrição. Outras propriedades mantêm
  suas descrições existentes; operações múltiplas continuam agrupadas.
- Entradas antigas já persistidas não são reescritas; a nova descrição vale para
  renomeações registradas a partir desta versão.

## Testes e evidências

`tests/history/test_link_notifications_and_rename.py`: sete testes cobrindo
notificações intermediárias, validação estrita, eventos completos e parciais,
prioridade sobre hint, persistência da descrição, propriedades comuns e undo/redo
com identidade preservada.

`scripts/check_link_construction_notifications.py --server http://127.0.0.1:3099`:
usa projeto descartável e HTTP/WebSocket reais; somente renderização da topologia é
simulada. Confirma evento com zero pontas, uma entrada final e histórico válido.
Não modifica projetos pessoais. Veja [log](server-integration.log).

Suíte completa em `codex/canvas-all-improvements`: **594 passed, 2 skipped**;
[log](all-improvements-tests.log). Os skips exigem Windows/macOS nativos.

## Branches

`codex/canvas-all-improvements` recebe o desenvolvimento. `codex/canvas-history`
foi solicitada neste trabalho e criada a partir de `codex/feature-history`
(`6073b656`), pois não existia localmente nem no origin. Os commits deste ajuste
são aplicados por cherry-pick, sem incorporar funcionalidades alheias à base de
histórico ou reescrever branches existentes. O push tem destino no fork
`https://github.com/redlintles/gns3-gui-fork.git`.
