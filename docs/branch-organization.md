# Canvas branch organization

Reorganized on 2026-10-19. The complete branch was renamed from
`codex/canvas-device-grouping` to `codex/canvas-all-improvements`.
Its commit (`125c8771855c14e19d28c24e00280bf4a425b13b`), tree and entire history
are unchanged. The target fork is `https://github.com/redlintles/gns3-gui-fork`.
No history of its `master`, `canvas-improvements` or upstream master was rewritten. The pre-existing untracked `docs/pr-canvas-improvements.md` was
left untouched and is not part of this reorganization.

## Branches and review bases

| Branch (all prefixed with `codex/`) | Review/merge base | Implementation tip before this documentation | Full-suite passed |
| --- | --- | --- | ---: |
| `fix-async-requests` | `c776d4ef` | `b4bba108` | 191 |
| `feature-zoom` | `c776d4ef` | `97cb7601` | 206 |
| `feature-geometry` | `c776d4ef` | `613089e6` | 199 |
| `feature-typography` | `c776d4ef` | `747c1b67` | 191 |
| `feature-hand-tool` | `c776d4ef` | `b74aa0a3` | 192 |
| `feature-image-importing` | `fix-async-requests` | `47ce1bb4` | 204 |
| `feature-container` | `fix-async-requests` | `ee49ccb6` | 301 |

`c776d4ef` is the original common upstream base and the fork's `master` at
publication. For focused PRs, compare against the review base shown above.
`canvas-improvements` already includes most of the combined implementation;
it is not the base for reviewing the separate feature additions.

Containers and images share the exact async branch ancestry. Merge async first;
review their feature-only changes against `codex/fix-async-requests`. Geometry
and typography share commit `162c879e`, a small draft lifecycle/Qt-fixture
prerequisite; neither inherits the other feature. The same canvas fixture is
present where needed so independent gesture tests do not import container tests.

## How history was separated

Zoom's six original commits and the HTTP-reply lifetime commit were cherry-picked
with `-x`. Mixed commits were split by responsibility and regrouped into scoped
implementation commits, with Original-commits trailers. The combined branch
retains every original commit and intermediate revision for provenance.

The extraction changes only the glue needed for independent execution:

- Standalone geometry and typography do not call the container save coordinator.
- Standalone hand navigation does not import or query CanvasGroups. Container
  selection normalization and pending-creation gestures remain integration work.
- Standalone image resizing applies generic parent-to-scene coordinate conversion
  in a private ImageItem helper, equivalent to the original container helper;
  it does not import GroupItem. Its view persists drawings on release without
  depending on container persistence.
- Main-window test fixtures cancel deferred startup callbacks and dispose timers,
  as in the preserved implementation. This prevents a modal startup callback
  from interrupting later gesture tests in the isolated image suite.

## Validation and merge conflicts

Each row reports a fresh full automated suite run on that isolated branch:

```
QT_QPA_PLATFORM=offscreen python3 -m pytest -q
```

Each suite additionally reported 1 skip and the pre-existing tarfile deprecation
warning. The unchanged complete branch passed 349 tests. A temporary combined
checkout passed 378 tests, including restored original mixed-feature regressions
and the independent branch tests. This is offscreen Qt validation; no new
interactive desktop or disposable-server validation was performed.

The branches are independently reviewable, but they are not conflict-free when
combined: several edit the same GraphicsView methods. A temporary detached HEAD
merged them in this order: async, geometry, typography, zoom, images, hand tool,
containers. Conflicts were resolved against the preserved complete implementation
in shared files. This temporary merge history is not a feature branch and is not
published. The conflict inventory is in `branch-integration-conflicts.json`.

For a merge involving only a subset of features, combine only the relevant
handlers; do not replace the entire GraphicsView with the combined branch's file,
which would import absent features. For the exact complete combination,
`125c8771` is the known-good reference for shared handlers. Check these rules:

1. Claim selected container corner handles before blank-canvas hand panning.
2. Disable blank-canvas panning while a container-creation selection is pending.
3. Normalize rectangle-selected children through CanvasGroups.target, collapse
   parent/child selection and preserve the active editing-container context target.
4. Keep stationary right-click context handling separate from rectangle selection,
   and consume the menu event once. Keep Edit first in an editing container menu.
5. Retain hierarchy-aware save-on-release for containers; do not also invoke the
   standalone image view's save loop. Preserve shape/note draft save integration.
6. On focus loss, clean up selection, hand panning, shape previews and container
   resize state for whichever features are present.
7. Register both the navigation and container actions when merging both features.
8. Preserve drawing POST-before-PUT ordering together with large-image transport.

After the temporary combined merge, all production files match the preserved
complete implementation except an extra blank line in DrawingItem and the
semantically equivalent private ImageItem position helper described above.
Original combined authoring tests verify nested image resize as well as the
container/hand interaction. The complete source was not modified to create this
validation result or to add these notes.

## Original commit ownership

Documentation commits follow the feature they describe. Mixed ownership means
individual portions were split; it does not mean the entire commit is duplicated
into every named feature.

| Original commit | Feature destination | Original subject |
| --- | --- | --- |
| `ba6055dd` | feature-container | Add session-local device grouping to topology canvas |
| `81915650` | feature-container | Document canvas architecture and device grouping test workflow |
| `6e891f52` | feature-container | Replace selection groups with persistent named topology containers |
| `bd3c4b45` | feature-container | Document persistent group format, container editing and server validation |
| `3b59dacd` | feature-container | Add fixed group frames, resize handles and parent-center alignment guides |
| `bca666c9` | feature-container | Document fixed group dimensions, clipping and summary panel actions |
| `132c5137` | feature-container + fix-async-requests | Support template drops into groups and defer updates until drawing creation |
| `31863e45` | feature-container | Document group persistence tradeoffs and propose native server support |
| `48927b31` | fix-async-requests | Keep background HTTP replies alive until completion |
| `f56cb122` | feature-container | Distinguish copied group names and validate asynchronous tree duplication |
| `7a0032c0` | feature-container | Document group duplication failure, reply lifetime fix and validation |
| `a3f9f07a` | feature-container | Detach devices dragged outside group frames and use solid drop highlights |
| `2c3f458d` | feature-container | Document solid group highlights and drag-out membership rules |
| `543ca105` | feature-container | Preview group exits and accept existing devices on group drops |
| `bb770c99` | feature-container | Document live group exit previews and existing-device insertion |
| `929cca04` | feature-container | Create groups after toolbar-initiated selection and use solid frames |
| `258e7c27` | feature-container | Document toolbar selection completion and solid group borders |
| `1ecd4b85` | feature-zoom | Anchor Ctrl-wheel zoom to the event cursor position |
| `30c8069b` | feature-zoom | Document cursor-directed zoom and view-only navigation padding |
| `267b0de9` | feature-zoom | Center wheel zoom on the chosen region and preserve navigation on project echoes |
| `7f9c7eaa` | feature-zoom | Document centered zoom workflow and project-update navigation regression |
| `d8c7713b` | feature-zoom | Zoom gently around the current cursor without recentering or retained focus |
| `b434393a` | feature-zoom | Document current-cursor magnification and gentler wheel steps |
| `f7198544` | feature-geometry; shared draft lifecycle also used by feature-typography | Draw rectangle and ellipse drafts by dragging before confirming their style |
| `56f53566` | feature-container | Add persistent container appearance tabs and exclusive shape choices |
| `77e6e2e6` | feature-typography | Configure note typography before creating the drawing |
| `f2f2d3e5` | feature-image-importing | Configure imported image dimensions and resize images from edges and corners |
| `a8a1c916` | feature-container + feature-geometry | Polish authoring dialog contrast and cancel abandoned shape previews |
| `227be1d0` | feature-container + feature-geometry + feature-image-importing | Make size inputs readable and interpret zero border width as no stroke |
| `09b2a767` | feature-container | Expose Edit container during editing and preview properties with Apply |
| `8574cc41` | feature-image-importing; container Apply regression in feature-container | Stream oversized image drawings as lossless project SVG resources |
| `a2569ef4` | feature-container | Match container interaction to its shape and fit children on shape changes |
| `d89af8b9` | feature-image-importing | Resize images with a lightweight transform preview instead of decoding each move |
| `b98eaf7b` | feature-hand-tool + feature-container (container-specific portions) | Add hand navigation and right-button rectangle selection with container creation |
| `8f7d2b4d` | feature-container | Keep container border width readable in dark themes |
| `709a8a9d` | feature-hand-tool + feature-container (container-specific portions) | Restore right-click context menus and target nested containers on double click |
| `ccc294c4` | feature-container | Keep only the active nested container in editing mode |
| `6ff5512f` | feature-container (early resize claim); cross-feature validation with feature-hand-tool | Fix container resize handles taking precedence over canvas panning |
| `125c8771` | feature-container | Document container resize navigation conflict and validation |
