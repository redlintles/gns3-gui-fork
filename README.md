# GNS3 GUI Fork — a richer canvas for your network labs

Organize topologies in **nested containers**, draw and annotate with more control, and revisit your changes with **persistent Undo, History and Redo**.

This community fork of [GNS3/gns3-gui](https://github.com/GNS3/gns3-gui) is based on GNS3 GUI **2.2.61** and focuses on the visual creation and organization of network labs. GNS3 lets you build topologies with virtual devices; this fork extends its graphical editing experience.

> **Developed with assistance from OpenAI Codex.** This fork used Codex to help investigate the codebase, implement features, create tests, analyze regressions and write documentation. The original project and its authors remain the foundation of this work. This fork is independent of GNS3 and OpenAI.

[Try the fork](#try-the-fork) · [Features in action](#features-in-action) · [Technical documentation](#documentation-and-validation) · [Contribute](#contribute-and-share)

## What's new in this fork

| Feature | What you can do |
| --- | --- |
| Persistent containers | Organize devices and drawings into hierarchies, move sets together and customize their frames. |
| Hand navigation and rectangle selection | Pan by dragging the canvas and select areas with the right mouse button. |
| Cursor-centered zoom | Zoom into the region you point at, with smaller steps. |
| Drag-to-draw rectangles and ellipses | Define the area before confirming colors, dimensions and borders. |
| Two-click lines | Choose both endpoints, preview the line and edit its endpoints afterward. |
| Note typography | Choose the font, size, color and styles before creating an annotation. |
| Resizable images | Set dimensions and aspect ratio, resize from edges and import large images. |
| Persistent history | Undo and redo actions, and recover history when reopening a project. |

These features are available together on **`codex/canvas-all-improvements`**. This repository's `master` branch retains the upstream base and does not contain this feature set. The examples below refer to the complete feature branch.

## Features in action

The GIFs are short demonstrations. Containers, navigation, shapes, lines, notes and images were captured from real Qt widgets running offscreen with mocked transport, without running appliances. The history GIF is a sequence of native screenshots from tests with a real server. [Demo sources and reproduction instructions](docs/media/README.md).

### Containers: organize your topology by context

![Container contents moving together and a change in container appearance](docs/media/containers.gif)

1. Select devices, notes, images or drawings at the same hierarchy level and press **Ctrl+G**, or use **Container elements** on the toolbar.
2. Name the set and adjust its dimensions. Group existing containers with other elements to build a hierarchy.
3. Drag a closed container to move its children together. **Double-click its body** or use **Enter container** to edit its contents; **Esc** leaves editing mode.
4. Use the properties dialog and its **Style** tab to choose a rectangle, triangle or ellipse, along with fill, color and border settings. **Apply** previews changes; **OK** confirms them and **Cancel** restores the previous state.
5. Resize from any of the four corners. Drag devices in or out to change membership. **Ctrl+Shift+G** unpacks the container while preserving its children.

The **Topology Summary** tree follows the hierarchy. Duplicating a container copies its tree and recreates internal links; links to external devices remain attached only to the original. Names, styles and membership are preserved in saved projects and portable exports.

Containers have fixed dimensions: moving children does not automatically expand the frame. Rectangles can clip content outside their bounds; changing the shape fits children inside and may enlarge the frame. [Full guide, in Portuguese](docs/canvas-grouping.md) · [Appearance and editing, in Portuguese](docs/canvas-authoring.md).

### Navigation: hand, selection and cursor-centered zoom

![Canvas zoom and navigation by dragging](docs/media/navigation.gif)

- **Hand** is the initial mode: drag an empty area with the left mouse button to pan. Dragging an element still moves that element.
- **Right-click and drag** selects an area and opens selection actions, including **Create container**. Hold **Ctrl** to add another area to the selection. A right-click without dragging opens the context menu.
- **Ctrl + mouse wheel** zooms around the cursor's current position. Each conventional wheel step zooms in by about 9%, within the 10% to 1000% limits.

Navigation does not change device coordinates. [Zoom details, in Portuguese](docs/cursor-zoom.md) · [Navigation gestures, in Portuguese](docs/canvas-authoring.md#navegação-e-seleção-com-o-mouse).

### Shapes: draw at the size you need

![Rectangle preview growing during a drag, followed by the confirmed shape](docs/media/shapes.gif)

Activate **Rectangle** or **Ellipse**, press on the canvas and drag. On release, the editor lets you confirm dimensions, fill, color, border width and border style. A border width of zero creates a borderless shape. **Esc** cancels the draft; canceling the editor discards the new shape. [How it works, in Portuguese](docs/canvas-authoring.md#formas-por-arraste).

### Lines: two clicks and editable endpoints

![Line preview between the first and second points](docs/media/lines.gif)

Activate **Drawn line**, click to set the origin, move the cursor to see the preview and click again to set the other endpoint. In **Line properties**, choose color, opacity, thickness and a solid, dashed or dotted stroke. **Apply** previews the style before confirmation.

After creation, drag the line body to move it, or select it and drag either endpoint. **Esc** cancels an unfinished line. These are visual drawings; connections between devices still use the link tool. [Line guide](docs/feature-line.md).

### Notes: choose typography before confirming

![Note editor with changes to text, font size and underline](docs/media/typography.gif)

Activate note creation and click the canvas. The editor provides text, font family, size, bold, italic, underline and color controls, with a preview. Fonts already used in the project appear first. **OK** creates a nonempty note; canceling discards the draft.

Fonts are not embedded in the project: another computer may substitute a font if the original family is not installed. [Note details, in Portuguese](docs/canvas-authoring.md#notas-com-tipografia-na-criação).

### Images: control size and aspect ratio

![Image dimensions dialog and an image shown at different sizes on the canvas](docs/media/images.gif)

When importing, adjust width and height in **Image properties**. **Keep aspect ratio** synchronizes the dimensions; uncheck it to set them independently. Afterward, select the image and drag an edge or corner to resize it; drag its interior to move it. The GIF shows the dialog and a sequence of dimensions applied to the canvas.

Dimensions and the aspect-ratio preference are stored in the SVG. Resizing reuses the decoded image during the gesture to reduce stuttering. Images whose SVG exceeds the JSON request limit are uploaded as project resources, without lossy compression or requiring a higher server limit. [Image and upload guide, in Portuguese](docs/canvas-authoring.md#imagens-dimensões-iniciais-e-redimensionamento).

### History: undo, redo and continue after reopening

![Screenshots before Undo, after Undo and after Redo](docs/media/history.gif)

Use **Undo**, **History** and **Redo** on the toolbar, or **Ctrl+Z** and **Ctrl+Y** with canvas focus. In the **History** dialog, select an entry to move through states. Text fields and notes being edited retain their native shortcuts.

History groups changes to devices, links, drawings and containers into logical operations and keeps up to **100 operations per project**. It is stored in project files, allowing you to continue after reopening and carry history through portable export when identities can be remapped safely. A new edit after Undo discards the future operations available for Redo.

**Important limitation:** Undo restores topology definitions and connections, but does not recover disks, internal configurations or appliance files removed by the compute. Use snapshots and backups for that data. Console commands, power operations and snapshots are not recorded in this history. Incompatible external changes can block history navigation; on reopening, incompatible records are preserved before a new sequence begins. [Usage, persistence and recovery, in Portuguese](docs/history/README.md).

## Try the fork

Example for Linux with Python **3.9 or later**, `git` and virtual environment support:

```bash
git clone --branch codex/canvas-all-improvements https://github.com/redlintles/gns3-gui-fork.git
cd gns3-gui-fork
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install PyQt6 -e .
.venv/bin/python -m gns3.main --profile canvas-fork
```

The `canvas-fork` profile separates GUI preferences; projects belong to the selected server. Try the features in a test project or a copy of a lab.

You also need a **separately installed and configured GNS3 Server**. This fork's integrations were verified with server **2.2.61**, without requiring server modifications. Use the setup wizard or GUI preferences to configure the connection. Installing `gns3-gui` from PyPI does not install this fork's changes.

Depending on your lab, install a terminal and Telnet client, a VNC or SPICE client, and Wireshark for packet captures. System images and appliances are obtained separately. For general setup and other operating systems, see the [GNS3 documentation](https://docs.gns3.com/).

An upstream GUI can open devices and drawings at their absolute positions, but does not provide this fork's container semantics. Make a project copy before switching clients while editing hierarchies.

## Documentation and validation

The guides above describe usage and limitations. To explore the implementation, see these technical documents, currently written in Portuguese:

- [History: architecture, persistence and server tests](docs/history/README.md)
- [Containers: SVG representation, hierarchy and integration](docs/canvas-grouping.md)
- [Visual authoring: shapes, notes, images and navigation](docs/canvas-authoring.md)
- [Audit: fixes and validation evidence](docs/audit/FINDINGS_AND_FIXES.md)
- [Item visibility and lifetime investigation](docs/history/CONTAINER_VISIBILITY_INVESTIGATION.md)
- [Undo/Redo repaint artifact investigation](docs/history/CONTAINER_REPLAY_GHOST_INVESTIGATION.md)

To run the automated suite:

```bash
.venv/bin/python -m pip install -r dev-requirements.txt
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
```

Validation for the initial documentation update completed with **594 tests passed and 2 skipped**, using Qt offscreen. The reports record the environment, results and limitations of each validation. Integration checks in `scripts/check_*.py` have their own requirements; consult the guides and use a disposable server.

To change Qt Designer interfaces, edit the `.ui` files and regenerate the bindings:

```bash
cd scripts
python3 build_pyqt.py
```

Start the GUI with `--debug` for detailed logs; the internal shell also accepts `debug 2`.

## Contribute and share

Try the features, share the GIFs and tell others how the fork helped you organize your lab. Starring the repository helps others discover the project.

To report problems, [open an issue in this fork](https://github.com/redlintles/gns3-gui-fork/issues) with the branch/commit, operating system, GUI and server versions, reproduction steps and, where possible, a minimal project without sensitive data. To propose changes, see [CONTRIBUTING.md](CONTRIBUTING.md) and open a PR in this fork; upstream contributions follow the GNS3 maintainers' process.

## Credits and license

GNS3 GUI is the work of its [original authors](AUTHORS) and the [GNS3 community](https://github.com/GNS3/gns3-gui). This fork's extensions were developed with assistance from **OpenAI Codex**, including implementation, testing and documentation.

The code retains the [GNU GPL v3 or later](LICENSE) license. For vulnerabilities, see the [security policy](SECURITY.md).
