# Yomitan renderer snapshot for LinguaLive

- Upstream: https://github.com/yomidevs/yomitan
- Pinned commit: `ee81f8dcf13e985bb4d7961009fb49a764b4d924`
- License: **GPL-3.0-or-later**, per upstream package metadata and source headers; full license in `LICENSE`.
- Fetched with `git clone --depth 1 https://github.com/yomidevs/yomitan.git` on 2026-11-11. The development checkout is `/private/tmp/lingualive-yomitan-upstream`; the app only depends on this checked-in source snapshot, not that temporary checkout or a browser extension installation.

## Included source

23 JavaScript modules comprising `DisplayGenerator` and its transitive local imports, plus the original `templates-display.html` and `css/display.css`. `upstream.json` records upstream SHA-256 hashes. Original copyright/license notices are retained. No extension build, package installation, background process, dictionary database or browser permissions are bundled.

The upstream CSS file is retained as source/reference. The app uses selected rules with selectors scoped to `.yomitan-entry-root` in `src/components/YomitanEntry.css`, followed by LinguaLive theme/layout overrides; it does not load global extension CSS.

## One upstream modification

In `js/display/display-generator.js`, `prepare(templatesHtml)` optionally loads bundled HTML into `HtmlTemplateCollection`. If no HTML is supplied it retains the original extension loading path. This allows the web app to import templates with Vite `?raw` instead of calling `chrome.runtime.getURL`. The modification is marked in the source. All other copied upstream files match the recorded hashes.

`display-generator.d.ts` is a local declaration exposing only the methods used by the web adapter; it is not copied from upstream.

## Integration-owned changes

`src/components/YomitanEntry.tsx` maps LinguaLive's curated demo vocabulary into Yomitan term entries, calls the actual `DisplayGenerator.createTermEntry`, and connects native term-entry audio/save controls to the existing app callbacks. Glossary input is restricted to plain text. Optional dictionary media is not enabled. Extension-only navigation/menu/Anki controls, empty pronunciation/frequency sections and nonfunctional Kanji links are removed from rendered nodes; no pitch accent, frequency rank or dictionary content is fabricated.

The adapter and CSS excerpts are marked GPL-3.0-or-later. This is a partial web adaptation of Yomitan, not the full extension or a standalone dictionary engine. The source of current meanings remains LinguaLive's demo data; Yomitan supplies display generation and Japanese furigana distribution.

## License and distribution

Keep upstream notices and the GPL license with this copied/modified code. The app exposes the license at `/licenses/yomitan-GPL-3.0.txt` and links to the upstream source from the popup. The license text and original source are part of this repository. The GPL's terms for conveying a combined frontend and its corresponding source must be followed when distributing it; an upstream URL by itself is not a substitute for the source of local modifications. No license change to the separate OCR server is made here.

See `docs/TICH-HOP-YOMITAN.md` for usage, limits, file mapping and verification.
