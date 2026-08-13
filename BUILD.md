# How this repo is built

Two deliverables, built differently on purpose.

## `README.md` — plain markdown

Real, selectable, searchable text. Headings, a fenced code block, a table, and
ordinary linked `<img>` tags for the icons and trimmings. **Nothing is a
screenshot.** Edit it like any other README.

GitHub strips CSS from markdown, so a README cannot have a page background or
webfonts. That is fine — it is a document and should read like one.

## `index.html` + `css/style.css` — the real page

This is where the old-web look lives, because here CSS actually runs. Every
asset is its own file and the stylesheet does the layering:

| Element | Asset | Handled by |
|---|---|---|
| sky and trees plate | `assets/img/sky.gif` | `body` background layer |
| tiled texture | `assets/img/texture.bmp` | `body` background layer |
| tree mass, bottom-left | `assets/img/trees.png` | `.trees` |
| the statue | `assets/img/statue.png` | `.statue` |
| the girl on the swing | `assets/img/girl.png` | `.girl` + `@keyframes swing` |
| rococo garland | `assets/img/divider.png` | `.divider` |
| Win98 chrome, panels, tiles | — | pure CSS |

Nothing is pre-composited. Move a figure by changing one rule.

The swing is real CSS: `transform-origin: 68% -55%` puts the pivot above the
frame so she travels on a pendulum arc instead of spinning in place. It honours
`prefers-reduced-motion`.

To publish it: **Settings → Pages → Source: deploy from branch `main`, folder
`/ (root)`**. It then serves at `https://elattar-ayoub.github.io/ELATTAR-Ayoub/`.

## Where the figures came from

`swing.png` on [howsoonisnow.org](https://howsoonisnow.org/) is a
36%-transparent foreground cut-out sitting over a separate `swing2.gif`
background plate. The cut-out was segmented with `scipy.ndimage.label` over its
alpha channel — the statue falls out as its own connected component, the girl is
separated from the trees by an x-cut.

The girl was cropped at the legs, so the figure was completed with Gemini
(`banana` skill): the crop was placed on a chroma-green canvas with room to
grow, the model painted in the skirts, kicking legs, flying slipper, seat and
ropes, and the result was keyed to transparency with `build/chromakey.py`.
Gemini cannot emit alpha, so the green-screen round trip is required.

## Fonts

`assets/fonts/` is mirrored from howsoonisnow.org and is what makes the page
look right — `blue.ttf` for the display title, `wobble.otf` for the nav,
`AdorableLady.ttf` for section headings, `DepartureMono` for body text,
`ms_sans_serif` for the Win98 chrome.

## Stats

The numbers in the README and on the page are from the GitHub API at build time.
Refresh them with:

```bash
gh api users/ELATTAR-Ayoub --jq '"followers=\(.followers) repos=\(.public_repos)"'
```

## Credits

Fonts, textures, icons, buttons and layout mirrored from
[howsoonisnow.org](https://howsoonisnow.org/). Backdrop: *The Swing*
(Jean-Honoré Fragonard, 1767), public domain.
