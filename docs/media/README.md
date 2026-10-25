# README demonstrations

The seven GIFs combine real screenshots with explanatory captions.

| File | Source and scope |
| --- | --- |
| `containers.gif` | Real GraphicsView and containers; creation, movement together and styling through the GUI API. |
| `navigation.gif` | Zoom through the view API and panning through QTest viewport events. |
| `shapes.gif` | QTest press/move/release events in the rectangle tool, with automated dialog confirmation. |
| `lines.gif` | Clicks and real Qt events for the line preview, with automated dialog confirmation. |
| `typography.gif` | Real TextEditorDialog, changes to its controls and application to the canvas. |
| `images.gif` | Real ImagePropertiesDialog and a sequence of dimensions through the ImageItem API, rather than a recorded manual drag. |
| `history.gif` | A sequence of native screenshots: `replay-before-undo.png`, `replay-after-undo.png` and `replay-after-redo.png` in `../history/visibility/`. |

The first six demonstrations use Qt offscreen with a mocked main window and transport. They show local visual behavior without running appliances or verifying server persistence. The history demo uses existing committed evidence from server tests; see the [investigation](../history/CONTAINER_REPLAY_GHOST_INVESTIGATION.md). The GIFs are sequences of states rather than continuous desktop recordings.

To regenerate them from the repository root, install the GUI dependencies and Pillow. On Linux with DejaVu Sans available:

```bash
QT_QPA_PLATFORM=offscreen python3 scripts/render_readme_demos.py
```

The script uses a temporary configuration directory and does not connect to a server. Screenshots come from the project's widgets; Pillow adds captions and encodes the GIFs.
