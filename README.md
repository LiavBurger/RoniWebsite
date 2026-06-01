# RoniWebsite — "האתר המתחרה של המלווים" 🍍🔍

The groomsmen's prank "evil twin" of Roni & Ofri's wedding site. Detective evidence-board theme.
**Surprise — do not share any link in a chat Roni is in.**

## How it deploys
Every push to `main` triggers `.github/workflows/deploy.yml`, which publishes the **`site/`** folder to GitHub Pages.
Live at: https://liavburger.github.io/RoniWebsite/  (≈1 min after a push)

## Edit the content
- All Hebrew copy, the beer roast notes, the chat, and the counter live in **`build_html.py`**.
- After editing, regenerate:  `python3 build_html.py`  → then `git add -A && git commit -m "..." && git push`.

## Photos
- `site/assets/gallery/gNN.jpg` — the embarrassing-photo gallery. Delete any file to remove it.
- `site/assets/beer-roni.jpg` — the beer-card image (tap cycles `beer-worse-*.jpg`).
- Original full-res media lives in `media/` locally and is **git-ignored** (kept out of the public repo).

## Rebuild everything from raw media (optional)
Needs a venv with `pillow pillow-heif imageio-ffmpeg`:
```
/tmp/mediaenv/bin/python build_media.py   # media/ -> site/assets (compress, EXIF-rotate, HEIC/MP4 convert)
python3 build_html.py                      # site/manifest.json -> site/index.html
```
