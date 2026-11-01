---
name: therion-drawing
description: Conventions for drawing or editing Therion scraps (.th2) in this survey, and the checks to run afterwards. Use when converting sketches, editing walls, water, labels, cross-sections or other symbols, or reviewing a drawing.
---

# Drawing Therion scraps in this survey

The conventions live in one place, `tools/sketch2therion/Style.md`
(the shared Therion-Sketching rules): read it before drawing or editing
a `.th2`, and add to it what the work teaches. Do not copy its rules
here.

- Workflow (SexyTopo to a finished plan, and `review`): `tools/sketch2therion/README.md`, with this cave's names in `tools/README.md`.
- Cave settings (names, scale, licence): `tools/project.toml`.
- Checks: `python3 -m tools.sketch2therion.th2lint FILE.th2`,
  `python3 -m tools.sketch2therion review check FILE.th2`, and
  `python3 -m tools.sketch2therion fillcheck --build --projection plan`.

## The older drawings

The rest of this file is what was learnt converting Footleg's
PocketTopo sketches (2012 to 2019) with the earlier converter, from a
Therion expert's review of the drawings (Andrew Atkinson). It still
describes those drawings and how to edit them. For new drawings,
`Style.md` wins where the two differ (brown, for example, is the floor
there, not another level). Cross sections on the Swildons sheets are
placed by `python3 -m tools.sketch2therion sections --write`. The
general rules the review taught (walls, symbols, passages over
passages, cross sections, the pitfalls and how to review with someone
who knows the cave) are in `Style.md`.

## .thconfig layouts

These are set in `gb_layout.thc` and `altitude-colours.th`, with the
shared ones in `Style.md` ("Layouts"):

- The altitude colours (`lookup altitude:warm`, used as
  `color map-fg altitude:warm`) run from dark red at the bottom of the
  cave through orange and yellow to green at the entrance.
- Water is hatched only in the black-and-white layout.
- The title carries the licence: GPL v3 or later (`map-comment`).
- Labels use 4 text sizes, in descending order (`-scale`):
  - `xl`: area names (Long Dry Way, Short Dry Way, Wet Way, Barnes Loop,
    New Grottoes);
  - `l`: main passages and chambers (Double Pots, Tratman's Temple,
    Sump 1, Water Chamber);
  - `m`: minor passages (Upper Oxbow, Rolling Thunder, the digs);
  - `s`: features (`C2`, Dig, The Well, Folded Strata).

## Checking

Build with the `swildons*.thconfig` files (see `README.md`), then check
as `Style.md` says ("Checking").

## How Footleg's sketches read (answers from the review)

- Footleg's walls have the passage on their right, with `-reverse on`,
  and about one point a metre.
- Brown outlines are other passages at another level or grottoes off
  the passage: each its own scrap, meeting the main passage along one
  shared wall (the same points), not overlapping it.
- Green: in the 2017 sketches, a shelf (draw its edge as a floor step,
  low side to the water); in the 2019 one, arcs across the passage are
  gour pools on flowstone (`line rimstone-dam`), and green "c" marks
  are flowstone.
- A dashed black circle, or orange ticks round a station, is an aven
  (`line chimney`, unclipped where it is wider than the passage); the
  surveyors drew the ticks on the wrong side, so don't copy them.
- Blue hatching: keep separate pools separate and round, as sketched;
  one hatched patch is one pool.
- Thin triangles are slope arrows (`point gradient`, wide end to tip),
  not boulders.
