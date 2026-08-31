# Interactive viewers

Self-contained HTML, no server and no dependencies. Open any of them directly,
or browse them at **https://alexerm.github.io/haystack6-322/**.

| page | what it is |
|---|---|
| [`route-guide.html`](route-guide.html) | the 321 as a drivable route sheet: 223 teleports, each row saying where the gate is relative to your car |
| [`spire-3d.html`](spire-3d.html) | the endgame conveyor in 3D, orbitable |
| [`endgame-graph.html`](endgame-graph.html) | the conveyor as a layered graph rooted at the Finish; loads a route file to draw it |
| [`map-graph.html`](map-graph.html) | the whole map graph, 6,396 nodes |

`endgame-graph.html` and `map-graph.html` take a route file through **Load path
JSON** — anything from [`../routes/`](../routes) or your own.
