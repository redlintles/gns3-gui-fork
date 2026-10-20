# Auditoria e correções — 20 de outubro de 2026

Implementação em `codex/canvas-all-improvements`, a partir de `6073b656`.
Os relatórios [exploratório](REPORT.md) e [de bugs comuns](COMMON_BUGS_REPORT.md)
registram as reproduções anteriores às correções. A [auditoria de segurança](SECURITY_AUDIT.md)
completa o conjunto. Projetos reais do usuário não foram modificados nos testes.

| Achado confirmado | Correção | Regressão automatizada |
| --- | --- | --- |
| B01: resize de forma agrupada mistura coordenadas e gera dimensões negativas | Captura transformação inicial e calcula deslocamento no espaço local; normaliza dimensões | Matriz de bordas e agrupamento; servidor, undo/redo e reabertura |
| B02: formas bloqueadas aceitam resize | Respeita bloqueio antes de iniciar o gesto | Arraste após ação Lock |
| B03: alternar ferramentas conserva modos de criação anteriores | Cancela modos incompatíveis ao ativar a ferramenta | Alternância e tipo efetivamente criado |
| B04: transparência do contorno se perde no SVG | Serializa e lê RGB e opacidade separadamente | Roundtrip de cores |
| B05: transparência baixa corrompe RGB | Usa representação RGB explícita, sem cortar hexadecimal RGBA | Cores com alfa baixo |
| B06: mínimo numérico quebra proporção de imagens | Limita ambos os campos conjuntamente | Limites e proporções |
| B07: restaurar link modifica UUID escrito em notas e invalida histórico persistido | Remapeia somente chaves de recursos e campos link_id | Texto literal, servidor e reabertura com cursor preservado |
| B08: reconexões WebSocket multiplicam handlers | Conecta sinais uma vez; reagenda com timer de 1 segundo, cancelável | Oito reconexões, um despacho, cancelamento |
| B09: espessura SVG fracionária interrompe carregamento | Lê float finito; fallback para SVG não editável quando necessário | Carregamento e propriedades |
| B10: alça da linha é pintada maior que área clicável no zoom | Pinta alça em pixels lógicos do viewport | Zoom 0,2 / 1 / 5 |
| SEC01: extração de update escapa do destino | Valida todos os membros antes de escrever e rejeita links | Arquivos temporários, traversal, links e ausência de escrita parcial na validação |
| SEC02: título de console vira argumentos adicionais | Analisa template confiável antes de inserir valores; valida endpoint | Popen simulado, Unicode, aspas e metacaracteres |

## Validação

- Qt runtime 6.4.2: **587 aprovados, 2 ignorados** ([log](validation/gns3-fixed-full.log)).
- Qt runtime 6.10.2: **587 aprovados, 2 ignorados** ([log](validation/gns3-fixed-full-qt610.log)).
- Os skips cobrem a migração de configurações antigas exclusiva do macOS e o parser nativo de argumentos Windows; ambos exigem o respectivo sistema operacional.
- [Integração completa com servidor](validation/gns3-fixed-server.log): CRUD, associações, histórico, falhas, reabertura, exportação/importação e imagens grandes.
- [Geometria com servidor](validation/gns3-fixed-geometry-server.log): 80×30 após resize, 80×40 após undo e 80×30 após redo/reabrir.
- [Remapeamento com servidor](validation/gns3-fixed-rebinding-server.log): nota literal preservada; cursor 5 antes/depois de reabrir; nenhuma recuperação necessária.
- Simulação nativa com PyAutoGUI e screenshots em [X11](validation/native) e [Wayland](validation/wayland): oito dispositivos, saídas de container, coleta de objetos, seis ciclos Ctrl+Z/Ctrl+Y e reabertura. Ambos passaram.

Os scripts reproduzíveis estão em `scripts/check_history.py`,
`scripts/check_container_visibility.py`, `scripts/check_audit_geometry.py` e
`scripts/check_audit_rebinding.py`. Exigem servidor descartável e, para input nativo,
um display isolado. As provas de segurança não executam comandos externos.

## Limites e decisões

Não foi reproduzida uma sequência nativa conclusiva para a suspeita de callbacks
fora de ordem (R01) ou interrupção de resize por foco (S01). Permanecem suspeitas,
sem correção especulativa. Não houve execução nativa em Windows/macOS; testes de
argumentos e estrutura AppleScript não substituem essa validação. Não se afirma
compatibilidade universal a partir de duas versões de Qt no Linux.

A varredura não constitui prova de ausência de vulnerabilidades. Templates de
interpretadores personalizados e ferramentas externas têm limitações detalhadas
no relatório de segurança. Nenhum esquema de projeto ou requisito de servidor foi
alterado. Os commits são locais; publicação remota não foi solicitada nesta etapa.
