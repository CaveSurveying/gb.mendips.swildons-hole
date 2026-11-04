# The 3D view

The cave in 3D beneath the ground, in the browser: the survey under
the Environment Agency's LIDAR terrain, draped with satellite imagery,
with its passage walls, routes through the cave, AR on an iPhone or iPad,
and it works offline once opened.

```bash
python3 -m tools.model3d      # after the main build; writes output/3d/
```

![The 3D view](../../docs/swildons-3d.jpg)

The page and its build are [cave-viewer](https://github.com/CaveSurveying/cave-viewer),
shared with other caves' repos, at the release pinned in
`requirements.txt` (`pip install -r tools/model3d/requirements.txt`).
`caves.json` at the top of the repo configures it for Swildons; its
options are cave-viewer's (`caveviewer/schema.json` there). A new
cave-viewer release is taken up by changing the pin.

## What goes in

- **The centreline** from `output/Swildons.3d`, Stanton's survey
  included. Legs flagged `duplicate` (Stanton's legs that the resurvey
  has replaced) are drawn but not routed along (`routing.duplicates`).
- **Passage walls** from `output/Swildons-walls.lox`: the 3D passages
  Therion builds from the drawings, exported for this page with
  `-wall-source maps` (Therion's default also builds walls from every
  splay, which come out as spikes). Only the resurvey has walls.
- **Names** of passages and places: this step reads the labels in the plan
  drawings (the same ones the route cards use, from `tools.routes.survey`),
  puts each at the nearest station on a leg, and writes them for
  cave-viewer as `output/cave-viewer/names.json`, with the entrance. They
  are the places routes go between.
- **The ground**: the Environment Agency's 1 m LIDAR composite (DTM),
  averaged to 2 m, the cave plus 250 m round it, fetched once and kept in
  `surface/lidar/` (if the cave grows past the edge, the next build fetches
  a bigger area: commit the new file).
- **The drawn survey** for the 2D plan: the colour plan sheet, drawn again
  by `swildons.thconfig` for this (layout `plan-web`: on grid north, with
  the grid's coordinates, which place it) as `output/cave-viewer/plan.svg`.
  It covers what the sheet covers, the resurvey from the Entrance to Sump 1.
- **Lining up the imagery**: the entrance's lat/long from
  `output/Swildons-centreline.kml` (Therion, with the exact OSTN15 grid)
  nudges cave-viewer's own conversion, leaving well under a metre of error.

The LIDAR (or cave-viewer) failing is only a warning: the 3D view is an
extra, and the rest of the site still publishes.

`tools.webmap` uses this step's grid helpers (`grid_to_ll`, `fit_affine`,
`kml_entrance`, `crop_png`) and the ground it saves in `output/3d/`.
