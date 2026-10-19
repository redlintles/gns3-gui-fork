# Topology containers

Base: `codex/fix-async-requests`, itself based on `c776d4ef`. Merge async first.
No dependency on zoom, geometry authoring, typography or image importing.

The first implementation commit groups the original container history through
`258e7c27`; its Original-commits trailer lists the source changes. The next commit
contains appearance, Apply/cancel, shape-aware fitting, nested editing and the
outer-corner resize fix. Original feature behavior and hierarchy serialization
are retained. See canvas-grouping.md and group-server-integration.md for details.

The container-only branch retains the original canvas selection bindings.
The hand-tool branch separately changes blank-canvas and right-button gestures.
When merging both, preserve the early beginResize check before blank-canvas
panning, resolve selection targets through CanvasGroups, suppress blank-canvas
panning while selection_pending, and retain the editing-container context target.
These integration requirements come from `b98eaf7b`, `709a8a9d` and `6ff5512f`.

The mixed stationary-right-click regression belongs to integration validation;
other nested-editing and outer-corner regressions run here without the hand tool.

Validation: `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`.
