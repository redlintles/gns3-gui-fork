# Draft: Improve canvas navigation and editing, with nested topology containers

## Why I worked on this

This started with frustrations I had while organizing larger GNS3 topologies. My concern is with the graphical editing workflow, rather than the simulation itself: moving around a large canvas, keeping related elements together, drawing backgrounds, and sizing imported images took more effort than I expected.

I am a developer and a GNS3 user, but I am not familiar with this project's Python/Qt stack. I used **OpenAI Codex as an experiment to investigate the code and implement these changes**, iterating on the results through actual use, screenshots, and recordings of problems I encountered. Codex generated the implementation, tests, and much of the technical documentation. I supplied the requirements, tested the interactions, and asked for revisions as issues appeared. I want to make that process explicit: this is not a claim that I independently audited every Qt or networking detail.

I am now using this fork in place of the installed official GUI because, for my own topology editing workflow, I find it more comfortable to use. That is personal experience, not evidence that the implementation is ready to merge unchanged. I would appreciate maintainers and other users trying it, particularly on larger projects and different desktop environments.

This is a draft for feedback on both the interaction and the implementation. It grew into several related features, and I am happy to split it into smaller PRs or change the approach to match the project's direction.

## Changes

### Named, nested containers

Containers organize devices, notes, shapes, images, and other containers into a hierarchy. They are actual parent/child graphics items, rather than a saved multi-selection.

- Create from a selection with **Ctrl+G**, the toolbar action, or **Create container** in the selection's context menu. The toolbar can also wait for a left-button selection and open the dialog when the gesture finishes.
- Give the container a name and fixed dimensions. The initial frame adds 30% to the selected content's bounds, split between both sides, plus space for the title.
- Move the contents together; duplicate or delete the hierarchy; unpack it with **Ctrl+Shift+G**.
- Browse the hierarchy in **Topology Summary**, which also offers container operations.
- Rename through the title and edit existing properties through the context menu. During editing, **Edit** is the first canvas menu action. **Apply** previews changes; Cancel restores the original properties and affected child positions.
- Resize from the corners without scaling the children. Moving a child does not automatically resize the container.
- Choose rectangle, triangle, or ellipse, with border and background controls. Defaults remain a transparent background and solid blue rectangular outline. Zero border width means no stroke.
- Use temporary horizontal/vertical center guides and snapping relative to the direct parent.
- Drop new or existing devices into a container. A thicker blue border identifies the destination. Dragging a device's center outside its current container marks the source red and detaches or reparents the device on release. A foreground preview keeps an exiting device visible beyond clipping boundaries.

Double-clicking a nested container targets the deepest visible container at that position and consumes the event before an ancestor can intercept it. Only the active container displays `[editing]`; its ancestors merely allow events to reach it.

`GroupItem` implements geometry, appearance, and serialization. `CanvasGroups` coordinates membership, editing, alignment, restoration, and recursive operations. `GraphicsView` handles interaction, and `TopologySummaryView` reflects the same hierarchy. Existing internal `group` names remain for compatibility; the user-facing feature is called Container.

There are some deliberate limits. Rectangular containers clip overflowing children; triangle and ellipse containers keep overflow visible so elements remain accessible. Changing shape moves overflowing children inside and can enlarge the frame if needed, but it is not an overlap-free layout algorithm. Corner handles remain at the bounding rectangle's corners even for nonrectangular shapes.

### Container persistence: the SVG workaround

**This is the main architectural compromise I would like reviewed.** The implementation targets the existing GNS3 2.2.61 API. That API persists nodes, links, and drawings, but does not provide a native container resource or parent relationship.

The hierarchy itself uses Qt parenting (`setParentItem`). SVG is used as a transport workaround, not because Qt cannot represent containers. Each container is stored through the drawing API with versioned JSON inside an SVG `<metadata>` element. It records identity, parent-local child positions, dimensions, appearance, and child references. Devices remain ordinary devices; they are not flattened into an image.

Normal node/drawing requests still use scene coordinates, while container metadata stores local coordinates. The GUI converts between them when receiving server updates and saving changes. This makes the interaction testable with an unmodified server, but it leaves the GUI responsible for maintaining both representations.

Consequences and limitations:

- The server does not validate or understand the hierarchy. Older clients cannot provide equivalent container operations and may not preserve the metadata when editing drawings.
- Recursive duplication and deletion are coordinated through individual requests. Duplication waits for new IDs, reconstructs membership, and recreates links whose endpoints were both copied. Links to devices outside the copied hierarchy are not duplicated. These operations are not server transactions; failures can leave partial results.
- Portable import regenerates IDs without rewriting references hidden in SVG metadata. The GUI attempts recovery using persistent identities for drawings/containers and a node-name fallback. This is a workaround with ambiguity risks, not the desired permanent import contract.
- Local revision checks help reject stale acknowledgments, but this is not a complete multi-client concurrency model.

The intended follow-up would be a native server layout resource with a parent ID per element, hierarchy validation, import/export ID remapping, coordinated recursive operations, and consistent notifications. The Qt interaction could remain while the SVG persistence adapter is replaced. No such server API is implemented here.

### Cursor-centered zoom

**Ctrl + wheel** now zooms around the current cursor position. The scene point underneath it stays at the same viewport location, rather than jumping toward the center of the window. Moving the cursor changes the reference for the next wheel event.

The view records the scene coordinate under the event position, temporarily disables automatic Qt anchoring, applies the scale, and compensates the displacement. A view-only navigation margin allows this near scene boundaries without changing saved topology dimensions. Wheel steps are smaller, using `2 ** (delta_y / 960)`; existing zoom limits remain.

An additional fix avoids resetting navigation when server acknowledgments reapply unchanged scene dimensions. That reset was undoing the cursor compensation and contributing to scrollbar/border flicker. Quantized Qt scrollbars still impose a small positioning tolerance; this is not an animated zoom implementation.

### Hand tool and selection

Two exclusive toolbar actions provide **Hand** and **Selection**, including status-bar help. Hand is the default: left-dragging empty canvas pans the view, with open/closed hand cursors. Left-dragging an element still moves that element.

Right-dragging draws a selection rectangle and opens the selected items' context menu on release. A stationary right-click opens the traditional item menu instead. Ctrl preserves the previous selection when adding a rectangle. The container toolbar's pending creation gesture retains left-button rectangle selection.

The selection rectangle is a viewport `QRubberBand`, mapped into scene coordinates for item selection. Mouse context events are consumed separately to avoid opening a second menu. Panning changes view scrollbars, not topology coordinates.

This changes an established mouse interaction, so I would especially like feedback on whether it should be optional or use different bindings upstream.

### Shapes drawn by dragging

Rectangle and ellipse tools now let the user drag out the desired area, with a temporary preview. Releasing opens the style dialog before the drawing is created on the server. Cancel discards the draft; Escape cancels the gesture.

The preview uses scene coordinates and normalized bounds, so all drag directions work under zoom. Dimension controls now allow up to 1,000,000 units instead of the previous 1,000-unit limit. This increases the editing limit; it does not guarantee practical rendering performance at every size.

Border style, color, thickness, no-border, and fill controls reuse the existing editor. Zero thickness explicitly selects `NoPen`, avoiding Qt's zero-width cosmetic stroke behavior. Relevant numeric fields have scoped white backgrounds and black text for readability.

### Notes and imported images

Creating a note opens typography controls before committing it: family, size, color, bold, italic, and underline, with the existing defaults. The font selector prioritizes families used in the project and common installed fonts. Fonts are not embedded or installed; another system may substitute a missing family.

Image import now offers width, height, and aspect-ratio controls before creation. Selected images can be resized from edges and corners. During dragging, a temporary transform reuses the decoded renderer; dimensions are written back into the SVG once on release. This avoids repeatedly parsing SVG and decoding embedded image data on every mouse event. The gesture accounts for item transforms and parent coordinates while preserving the opposite corner.

Two server compatibility workarounds are involved:

- A serialized image drawing can exceed the server's 1 MiB JSON request limit. Changing its displayed dimensions does not reduce embedded bitmap data. Large SVGs are therefore streamed through the existing project-file upload endpoint and referenced by filename in a small drawing request. This preserves image data without raising the server limit. In an empty project, a temporary transparent drawing initializes native image storage and is removed afterward.
- The embedded image is wrapped in an SVG `g` element so the server's simple-image optimization does not extract the bitmap and discard custom drawing dimensions/metadata. This depends on the existing 2.2 server behavior and deserves compatibility review.

### Supporting asynchronous fixes

Drawing updates now wait for creation acknowledgment before sending PUT requests. Edits made while POST is pending are retained; deleting a pending creation schedules cleanup after acknowledgment. This addresses a reproducible ordering race that can produce a drawing 404, although the screenshot originally reported during development was not enough to establish that specific session's cause.

The HTTP client also retains in-flight Qt reply wrappers until completion. Without that reference, some requests could lose Python callbacks to garbage collection, leaving duplicated devices without their reconstructed hierarchy or internal links.

These changes affect shared request handling beyond containers and warrant review on their own.

## Validation and remaining review

The latest full automated run completed with **312 passed and 1 skipped**, with an existing `tarfile` deprecation warning:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest -q
```

Tests include Qt mouse/wheel events, nested editing, selection and context menus, cursor anchoring, geometry, resizing, cancellation, serialization, and asynchronous callbacks. Earlier disposable-server checks against GNS3 2.2.61 exercised Ethernet-switch nodes, links, duplication, export/import, delayed drawing creation, and large-image resource uploads. Those checks do not validate every emulator, every API branch, or concurrent clients, and they should not be read as a fresh end-to-end run of every change in this branch.

I would appreciate testing on real projects, particularly nested containers, duplication and portable export/import, rotated or large images, high-DPI desktops, and different server setups. I would also like guidance on the target branch, whether the mouse bindings fit GNS3, and whether to separate the independent canvas improvements from the container/server-model discussion.

The implementation notes are under `docs/`, particularly `canvas-authoring.md`, `cursor-zoom.md`, and `group-server-integration.md`. Some notes describe intermediate revisions; the test count above is the latest full-suite result.

I was unsure which channel would be best for getting feedback, so I am starting with this draft rather than contacting individual developers privately. The goal is to make complex topologies easier to organize while keeping GNS3's existing simulation workflow intact.
