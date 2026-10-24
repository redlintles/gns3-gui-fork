# Demonstrações do README

Os sete GIFs são compostos por capturas reais, com legendas adicionadas para orientar a leitura. Não são imagens geradas por IA.

| Arquivo | Origem e alcance |
| --- | --- |
| `containers.gif` | GraphicsView e containers reais; criação, translação conjunta e estilo acionados pela API da GUI. |
| `navigation.gif` | Zoom pela API da view e pan por eventos QTest no viewport. |
| `shapes.gif` | Press/move/release QTest na ferramenta retângulo; confirmação do diálogo automatizada. |
| `lines.gif` | Cliques e eventos reais Qt para a prévia de linha; confirmação do diálogo automatizada. |
| `typography.gif` | TextEditorDialog real, alteração dos controles e aplicação ao canvas. |
| `images.gif` | ImagePropertiesDialog real e sequência de dimensões pela API ImageItem; não grava um arraste manual. |
| `history.gif` | Sequência das capturas nativas `replay-before-undo.png`, `replay-after-undo.png` e `replay-after-redo.png` em `../history/visibility/`. |

As seis primeiras demonstrações usam Qt offscreen, com a janela principal e o transporte simulados. Mostram o comportamento visual local, sem executar appliances e sem comprovar persistência no servidor. O histórico usa evidências já versionadas dos testes com servidor; consulte a [investigação](../history/CONTAINER_REPLAY_GHOST_INVESTIGATION.md). Os GIFs são sequências de estados, não gravações contínuas de uma sessão de desktop.

Para regenerar a partir da raiz do repositório, instale as dependências da GUI e Pillow. Em Linux com DejaVu Sans disponível:

```bash
XDG_CONFIG_HOME=/tmp/gns3-readme-config QT_QPA_PLATFORM=offscreen python3 scripts/render_readme_demos.py
```

O script não conecta a um servidor. As capturas são obtidas dos widgets do projeto; o Pillow apenas adiciona legendas e codifica os GIFs.
