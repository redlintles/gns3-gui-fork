# Image importing and resizing

Base: `codex/fix-async-requests`, itself based on `c776d4ef`. Merge the async
branch first. No containers, geometry, typography, zoom or hand-tool dependency.
Split from `f2f2d3e5`, `227be1d0` (image numeric controls), `8574cc41`
(image/resource transport only) and `d89af8b9`.

Import confirms dimensions and aspect ratio before creation. Edges and corners
resize using a lightweight transform, decoding the SVG once on release. Rotation
and generic Qt parent coordinates are respected without importing GroupItem.
The standalone view persists selected drawing changes on release; containers
use their hierarchy-aware persistence when integrated.

Oversized SVGs are streamed as lossless project resources using the existing
server endpoint; compact requests refer to the uploaded asset. Direct raster
children are wrapped to preserve custom dimensions on GNS3 2.2 servers.

Validation: `QT_QPA_PLATFORM=offscreen python3 -m pytest -q`.
The disposable-server script is retained, but was not rerun during this split.
