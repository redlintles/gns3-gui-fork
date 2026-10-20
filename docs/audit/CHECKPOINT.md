# Correções da auditoria — checkpoint

Branch: codex/canvas-all-improvements; base 6073b656. Produção preservada no
checkout principal. Implementação no worktree /tmp/gns3-audit-fixes.

Pendentes: B01 resize, B02 lock, B03 ferramentas, B04/B05 alpha, B06 proporção,
B07 remapeamento, B08 reconexão, B09 SVG fracionário, B10 alças.
Segurança: testes inertes reproduziram escrita fora do diretório de update e
injeção de argumentos via título de console; subprocessos não foram executados.
Riscos ainda não comprovados (R01/S01/macOS shell) não serão chamados de corrigidos.

Ao concluir cada componente, atualizar este arquivo, executar regressões e
commitar por assunto. Não publicar no remoto sem solicitação nesta etapa.

## Etapa 1 concluída

B01/B02: geometria usa transform original e coordenadas locais; dimensões positivas,
bloqueio respeitado. B03: troca limpa modos anteriores. B04/B05: RGB/alpha separados
no SVG, leitura de espessura fracionária. B06: dois campos limitados em conjunto.
B09: fallback de SVG não editável. B10: alça pintada em pixels do viewport.
Testes existentes de itens: 311 aprovados; regressões reduzidas: 30 aprovadas
(incluindo uma regressão de rebind, que será commitada na etapa 2).
