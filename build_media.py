#!/usr/bin/env python3
"""Process the media/ dump + docx images into web-ready assets for the troll site.
Run with the venv python that has pillow + pillow_heif + imageio_ffmpeg:
    /tmp/mediaenv/bin/python build_media.py
Re-runnable: drop new files in media/ (e.g. the real mock-beer photo named beer-*.jpg) and re-run.
"""
import os, glob, json, subprocess, shutil
from PIL import Image, ImageOps
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except Exception as e:
    print("WARN no heif:", e)

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
DOCX  = "/tmp/docx_extract/word/media"
OUT   = os.path.join(ROOT, "site", "assets")
GAL   = os.path.join(OUT, "gallery")
for d in (OUT, GAL): os.makedirs(d, exist_ok=True)

MAXEDGE = 1280
Q = 80

def save_jpg(src, dst, maxedge=MAXEDGE, q=Q, bg=(255, 255, 255)):
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)          # honor phone rotation
    if im.mode in ("RGBA", "LA", "P"):        # flatten transparency onto a solid bg (PNG labels)
        im = im.convert("RGBA")
        canvas = Image.new("RGB", im.size, bg)
        canvas.paste(im, mask=im.split()[-1])
        im = canvas
    else:
        im = im.convert("RGB")
    im.thumbnail((maxedge, maxedge*3), Image.LANCZOS)  # long edge cap, allow tall portraits
    if max(im.size) > maxedge:
        # cap the longest edge precisely
        s = maxedge/max(im.size); im = im.resize((int(im.width*s), int(im.height*s)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
    return os.path.getsize(dst)

# ---- 1. Named hero / story / beer picks (from docx extract + media) ----
PICKS = {
    "kiss.jpg":          f"{DOCX}/image2.jpg",                              # the Funjoya kiss = evidence
    "evidence-chat.jpg": f"{DOCX}/image1.jpg",                              # whatsapp "זה ניצחון"
    "beer-roni.jpg":     f"{MEDIA}/beers/Gemini_Generated_Image_7czjkf7czjkf7czj.png",  # new "רוני 0%" label
    "chat-group.jpg":    f"{MEDIA}/Screenshot_20200121-170524_WhatsApp.jpg",
    "chat-insta.jpg":    f"{MEDIA}/Screenshot_20220421-205815_Instagram.jpg",
    # real chat screenshot (replaces the generated WhatsApp block in the story)
    "chat-real.jpg":     f"{MEDIA}/whatsapp_chat/WhatsApp Image 2026-06-02 at 22.27.13.jpeg",
    # "MasterPlan" proof-of-plan screenshot (new section before the closing story box)
    "proof.jpg":         f"{MEDIA}/proof_of_plan/WhatsApp Image 2026-06-01 at 10.01.22.jpeg",
    # Funjoya trip collage (inside the פאנג׳ויה story box)
    "funjoya.jpg":       f"{MEDIA}/funjoya/20260531_234541-COLLAGE.jpg",
    # 3 extra beer labels (Roni+Niv, Roni+Ofri, Roni solo)
    "beer-niv.jpg":      f"{MEDIA}/beers/Gemini_Generated_Image_qovezbqovezbqove.png",
    "beer-ofri.jpg":     f"{MEDIA}/beers/Gemini_Generated_Image_d4c99ed4c99ed4c9.png",
    "beer-solo.jpg":     f"{MEDIA}/beers/Gemini_Generated_Image_6pt01q6pt01q6pt0.png",
}
for name, src in PICKS.items():
    if os.path.exists(src):
        sz = save_jpg(src, os.path.join(OUT, name))
        print(f"  pick {name:18} <- {os.path.basename(src):40} {sz//1024}KB")
    else:
        print(f"  MISS {name:18} (src not found: {src})")

# beer tap-to-cycle: worst faces (fallbacks if missing are skipped)
BEER_CYCLE = [
    "beer-roni.jpg",  # default already created above
]
WORST = [
    f"{MEDIA}/2013-10-24 22.46.58.jpg",
    f"{MEDIA}/Screenshot_2016-04-04-20-27-35.png",
    f"{MEDIA}/IMG-20161005-WA0027.jpg",
    f"{MEDIA}/IMG-20190119-WA0029.jpg",
    f"{MEDIA}/IMG-20190128-WA0005.jpg",
]
for i, src in enumerate(WORST, 1):
    if os.path.exists(src):
        n = f"beer-worse-{i}.jpg"; save_jpg(src, os.path.join(OUT, n)); BEER_CYCLE.append(n)
print("  beer cycle:", BEER_CYCLE)

# ---- 2. HEIC convert ----
for h in glob.glob(f"{MEDIA}/*.HEIC") + glob.glob(f"{MEDIA}/*.heic"):
    try:
        n = "heic-" + os.path.splitext(os.path.basename(h))[0] + ".jpg"
        save_jpg(h, os.path.join(MEDIA, n))   # drop converted back into media/ so it joins the gallery sweep
        print("  HEIC ->", n)
    except Exception as e:
        print("  HEIC FAIL", h, e)

# ---- 3. Videos: extract poster frame (for vetting) + transcode small web mp4 ----
try:
    import imageio_ffmpeg; FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception as e:
    FF = None; print("WARN no ffmpeg:", e)
VIDS = []
if FF:
    for v in sorted(glob.glob(f"{MEDIA}/*.mp4")):
        base = os.path.splitext(os.path.basename(v))[0][:8]
        poster = os.path.join(OUT, f"vid-{base}-poster.jpg")
        webm   = os.path.join(OUT, f"vid-{base}.mp4")
        subprocess.run([FF,"-y","-i",v,"-frames:v","1","-vf","scale=640:-2",poster],
                       capture_output=True)
        subprocess.run([FF,"-y","-i",v,"-vf","scale=720:-2","-c:v","libx264","-crf","30",
                        "-preset","veryfast","-an","-movflags","+faststart",webm],
                       capture_output=True)
        if os.path.exists(webm):
            VIDS.append({"src": f"assets/{os.path.basename(webm)}",
                         "poster": f"assets/{os.path.basename(poster)}"})
            print(f"  VIDEO {base}: poster+mp4 ({os.path.getsize(webm)//1024}KB)")

# ---- 4. Gallery sweep ----
# Preferred model: drop the embarrassing photos in media/gallery/ -> ONLY those become the gallery.
# Fallback (legacy): if media/gallery/ is missing/empty, sweep top-level media/ minus the named picks.
used_sources = set(os.path.basename(s) for s in PICKS.values()) | set(os.path.basename(s) for s in WORST)
exts = (".jpg",".jpeg",".png",".JPG",".JPEG",".PNG")
GAL_SRC = os.path.join(MEDIA, "gallery")
gallery_srcs = sorted(f for f in glob.glob(f"{GAL_SRC}/*") if f.endswith(exts))
if gallery_srcs:
    print(f"  gallery source: media/gallery/  ({len(gallery_srcs)} files)")
else:
    gallery_srcs = [f for f in sorted(glob.glob(f"{MEDIA}/*"))
                    if f.endswith(exts) and os.path.basename(f) not in used_sources]
    print(f"  gallery source: media/ top-level (legacy, {len(gallery_srcs)} files)")
# wipe old gNN.jpg so the gallery is a clean replacement, not an append
for old in glob.glob(os.path.join(GAL, "g*.jpg")): os.remove(old)
gal_files = []
idx = 0
for f in gallery_srcs:
    idx += 1
    n = f"g{idx:02d}.jpg"
    try:
        save_jpg(f, os.path.join(GAL, n)); gal_files.append(f"assets/gallery/{n}")
    except Exception as e:
        print("  gal FAIL", f, e); idx -= 1

manifest = {"gallery": gal_files, "beer_cycle": [f"assets/{b}" for b in BEER_CYCLE], "videos": VIDS}
json.dump(manifest, open(os.path.join(ROOT,"site","manifest.json"),"w"), ensure_ascii=False, indent=2)
print(f"\nGALLERY: {len(gal_files)} imgs | BEER cycle: {len(BEER_CYCLE)} | VIDEOS: {len(VIDS)}")
# total weight
tot = sum(os.path.getsize(os.path.join(dp,f)) for dp,_,fs in os.walk(OUT) for f in fs)
print(f"TOTAL assets weight: {tot//1024//1024} MB")
