# How this README is built

GitHub markdown strips CSS, JS and webfonts, and there is no way to give a
README a page background. So the **entire page is rendered in a browser and
sliced into images** — background, panels, typography and all. The only live
element left is the closing banner GIF.

## Layout

```
README.md
build/
  page.html          the WHOLE page — edit this, not the images
  stack.html         (legacy tile grid, no longer used by the build)
  chromakey.py       green-screen -> transparent PNG
assets/
  parts/             figures cut out of the painting (transparent, full res)
    statue.png         the cherub + pedestal
    girl.png           the girl on the swing
    trees_left.png     soft-masked foliage mass for the bottom-left
  readme/            the 32 sliced bands and cells the README references
  site/              mirrored from howsoonisnow.org (fonts, textures, trimmings)
  stack/             the 19 upstream tech logos (SVG)
```

## Why the page is 720px wide

This is the single most important constraint, and getting it wrong breaks the
layout silently.

GitHub applies `max-width: 100%` to images. A **full-width band** wider than the
column gets scaled down; a **small cell** (an icon tile) does not, because it
never exceeds the column. So the moment a band scales, the row of cells beneath
it no longer sums to the same width — the row overflows and **wraps**, leaving a
white gash across the page.

The fix is to make the page narrower than the column so **nothing ever scales**:
bands render at 720, cells sum to exactly 720, and the arithmetic holds at every
viewport. A fixed-width centred page is also the honest web-1.0 idiom.

Verified identical at container widths **890 / 800 / 740** — same painted extent,
same interior pixels, no wrapping.

The design is authored at 880px and scaled with `html { zoom: 0.8181818 }`, so
the CSS keeps round numbers while output lands on 720.

## Band map

| Image | Width | Links to |
|---|---|---|
| `p1-title.jpg` | 720 | — |
| `nav-*.jpg` ×5 | 144 each | about / stack / projects / elattar.dev / contact |
| `hero-a.jpg` | 720 | — |
| `hero-bL.jpg` + `hero-swing.gif` | 320 + 400 | — (the animated row) |
| `hero-c.jpg` | 720 | — |
| `ico-*.jpg` ×10 | 72 each | frontend tech docs |
| `p3-backhead.jpg` | 720 | — |
| `bk-edgeL` + 9 × `ico-*` + `bk-edgeR` | 36 / 72 / 36 | backend tech docs |
| `p4-body.jpg` | 720 | — |
| `p5-credit.jpg` | 720 | howsoonisnow.org |

The backend row has only 9 tiles, so it needs the two 36px edge images to still
total 720. Without them the row would be 648 wide and GitHub's background would
show down both sides.

## Slicing is measured, never guessed

`page.html` contains eight 2px magenta `<div class="mark">` rules — before and
after each sliceable row. After rendering, they're located by colour and the cut
coordinates come from them:

```bash
python -c "
from PIL import Image; import numpy as np
a=np.asarray(Image.open('build/full2x.png').convert('RGB')).astype(int)
mag=(a[:,:,0]>190)&(a[:,:,1]<90)&(a[:,:,2]>190)
rows=np.where(mag.mean(axis=1)>0.5)[0]
g=[]
for r in rows:
    if g and r-g[-1][-1]<=1: g[-1].append(r)
    else: g.append([r])
print([(x[0],x[-1]) for x in g])
"
```

This exists because a DOM measurement lied: the preview pane reported the page
at 1555px while headless rendered it 1775px tall (the badge SVGs lay out
differently), and the pinned height silently **clipped the whole footer**. The
markers are cut out by the slice, so they never appear in the output.

Render command:

```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu \
  --hide-scrollbars --allow-file-access-from-files --force-device-scale-factor=2 \
  --virtual-time-budget=9000 --window-size=720,1700 \
  --screenshot="D:\DESIGN\brainstorm\README\build\full2x.png" \
  "file:///D:/DESIGN/brainstorm/README/build/page.html"
```

Render at **2x** and display at 720 so the small type stays crisp.
`subsampling=0` (4:4:4) keeps the code text from ringing.

## The figures are separate elements

`swing.png` on their site is **not** the painting — it's a 36%-transparent
foreground cut-out; `swing2.gif` is the background plate. The cut-out was
segmented with `scipy.ndimage.label` over its alpha channel: the statue falls out
as its own connected component, the girl is separated from the trees by an x-cut
at 1230px. They're placed as ordinary `<img>` elements so their size and position
are **independent of the backdrop** — composited in, they shrink to whatever the
background crop dictates and the statue vanishes into the mist.

| Layer | z-index |
|---|---|
| `body` background: painting, fading into `germ.bmp` texture | — |
| `.trees` bottom-left | 4 |
| `.girl` | 5 |
| `.statue` | 6 |
| all content (`.up`, `section`) | 30 |

The statue carries `drop-shadow` + `contrast(1.14)`; pale stone on pale mist
reads as a smudge without it.

## The swing animation

`page.html` really does animate — `.girl` carries a CSS `@keyframes swing`
(±2.4°, 4.8s, `transform-origin: 68% -55%`, i.e. a pivot above the frame so she
travels on an arc like a pendulum). But **CSS does nothing in a README**, so the
motion is baked out as a GIF.

`page.html` reads a `#a=<deg>` hash, kills the animation and pins the rotation,
so frames can be rendered deterministically:

```bash
for A in $(python -c "import math;print(' '.join(f'{2.4*math.sin(2*math.pi*i/12):.3f}' for i in range(12)))"); do
  chrome --headless=new ... --screenshot=build/frames/f$i.png \
    "file:///.../build/page.html#a=$A"
done
```

Only the girl moves, and content is drawn *over* her (z-index 5 vs 30), so the
changed pixels are a small rectangle. Measured: **14.4% of the hero band,
x 645–1439, y 73–815**. The hero is therefore cut into three rows, and only the
right half of the middle row is a GIF:

```
hero-a.jpg                       720 wide, static
hero-bL.jpg | hero-swing.gif     320 + 400, side by side
hero-c.jpg                       720 wide, static
```

The split sits at x=640, safely left of the first changing column (645), so no
moving pixel is stranded in the static half. Verified: the mean column-to-column
delta at the seam is 13.06 against 11.8–15.4 for its neighbours — statistically
invisible.

**Never dither the GIF.** Floyd–Steinberg error diffusion propagates across the
whole frame, so a change in one corner alters every pixel downstream and GIF's
inter-frame delta compression collapses. Undithered at 160 colours is visually
indistinguishable here and roughly halves the file:

| Build | Size |
|---|---|
| 12 frames, 256c, dithered, whole band | 3558 KB |
| 12 frames, 256c, dithered, cropped | 2810 KB |
| 12 frames, 128c, undithered, cropped | 1715 KB |
| **8 frames, 160c, undithered, cropped** | **1280 KB** |

## The girl was completed by Gemini

The cut-out lifted from their site is cropped — no legs, no swing seat, ropes
severed. `assets/parts/girl_full.png` is the completed figure: the crop was
placed on a 1024×1024 chroma-green canvas with room to grow, sent through
`banana/scripts/edit.py` with an instruction to extend the skirts, paint in the
kicking legs and flying slipper, add the seat and both ropes, and keep everything
else flat green — then keyed with `chromakey.py`. Gemini cannot emit alpha, so
the green-screen round trip is mandatory.

## What is now frozen

Everything except the closing banner. In particular the **stats panel is baked**
from real API data captured at build time (37 repos, 65 stars, 13 followers,
TypeScript 67.8% …). Re-run these and re-render to refresh:

```bash
gh api users/ELATTAR-Ayoub --jq '"followers=\(.followers) repos=\(.public_repos)"'
```

This replaced `github-readme-stats.vercel.app`, which was returning 503 on every
attempt — its public instance is chronically rate-limited.

## Preview it the way GitHub will render it

```bash
python -c "import json,io; io.open('build/md.json','w',encoding='utf-8').write(json.dumps({'text':io.open('README.md',encoding='utf-8').read(),'mode':'gfm'}))"
MSYS_NO_PATHCONV=1 gh api markdown --input build/md.json > build/body.html
```

Then wrap `body.html` at several container widths and screenshot — that is how
the wrapping bug above was caught.

## Gotchas

- **GitHub strips `style`.** It substitutes `style="max-width: 100%;"`. No
  `display:block`, no overrides.
- **No whitespace between `</a>` and `<a>`** in a cell row — one space becomes a
  visible vertical slot.
- **No blank lines inside `<div align="center">`**, or the content is parsed as
  markdown and every image gets its own `<br>`.
- **Bare `<img>` gets auto-linked** to the image file; images already inside an
  `<a>` keep their href.
- **Inline `<span>` ignores `width`.** The language bars needed
  `display: block` on `.fill`, or they render empty.
- **Gemini can't output alpha.** Render on flat chroma green, then
  `python build/chromakey.py <src> <dst> <width>`.

## Credits

Fonts, textures, icons, buttons and layout mirrored from
[howsoonisnow.org](https://howsoonisnow.org/). Backdrop: *The Swing*
(Jean-Honoré Fragonard, 1767), public domain.

## Re-mirroring the source assets

`assets/site/` (their fonts, CSS, GIFs and textures) is **gitignored** — nothing
in `README.md` references it, and re-hosting the whole library here would be a
further redistribution than the rendered page needs. `build/page.html` does need
it. To restore it, refetch from the site with a browser user-agent (it 403s bots):

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0.0.0"
mkdir -p assets/site/{fonts,css,img}
for f in blue.ttf wobble.otf AdorableLady.ttf pixelplay.otf DepartureMono-Regular.woff \
         ms_sans_serif.woff2 ms_sans_serif_bold.woff2; do
  curl -sS -A "$UA" -H "Referer: https://howsoonisnow.org/" \
    -o "assets/site/fonts/$f" "https://howsoonisnow.org/fonts/$f"
done
for f in swing.png swing2.gif germ.bmp Pattern_5.gif paint72.ico editman.ico js.ico cmd.ico \
         heart1.ico star.gif newy.gif linkback.png buttonnow.gif butt.gif butt2.gif butt3.gif \
         caffeine.png jam.png hopelessromantic.gif angelclique.png frodolives.gif; do
  curl -sS -A "$UA" -H "Referer: https://howsoonisnow.org/" \
    -o "assets/site/img/$f" "https://howsoonisnow.org/img/$f"
done
```
