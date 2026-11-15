# Project notes

## Video preferences
- Make every video **16:9 landscape (1920x1080)**. Never use 9:16 or any vertical format.

## Working style
- **Speed matters more than perfect images.** Use whatever images are on hand, and don't spend long searching for perfect ones.
- Look in `image-library/` first. Download new images only when nothing there fits, keep it to a few, and fetch them all at the start, before editing. Wikimedia rate-limits this server (HTTP 429) heavily.
- Color is fine. Keep color images in color instead of always converting to black and white. Black and white is optional, mainly for photos that are already old monochrome.
- Add every image you download to `image-library/<topic>/` (resized to at most 1920px) so later videos can reuse it.

## Video tools
`video-tools/` holds the scripts that made the Morocco map animation (documentary-style map with a ship following a dotted route):
- `make_map.py <workdir>`: builds the parchment map (`map.png`). It needs `<workdir>/geo/countries.geojson` (Natural Earth 50m countries) and fonts in `<workdir>/fonts/` (Cinzel, Amiri-Bold, IM Fell English).
- `animate.py <workdir> <out.mp4>`: renders the frames. The output size is set by `OW, OH`, so use 1920x1080 for new videos and adjust the title and caption positions to match.
- `audio.py <out.wav>`: makes the soundtrack (waves, oud-like plucks in hijaz, frame drum). It needs scipy.
- `documentary/`: the Netflix-style documentary edit used for `jack_the_ripper_documentary.mp4` (1920x1080). It uses black-and-white archive images, red hand-drawn circles and arrows, black headline boxes and film grain. Scenes are defined in `scenes.py`. Run it with `doc.py <workdir> <fontsdir> <out.mp4>`; images go in `<workdir>/img/`. Fonts: Anton, Cairo, Marhey, Special Elite. The archive images come from Wikimedia Commons (public domain, 1888).
- `morocco-intro/`: a 5s fast-cut archive montage intro (`intro.py <workdir> <fontsdir> <out.mp4>`). Shots are defined in `shots.py`, and image sources and licenses are in `meta.json` (all public domain: Gallica BnF and ETH-Bibliothek). The final shot shows the MOROCCO / المغرب title.
- `history-of-smoking/`: the same documentary style, extended for `history_of_smoking.mp4` (60s, 1920x1080). It adds smoke title cards with animated number counters and Arabic narration subtitles (`SUBS` in `scenes.py`), plus `fit="width"` for wide images. Sources: Wikimedia Commons, Internet Archive and Google Patents (all public domain).

## Saved videos (the user approved all of them)
- `morocco_map_animation.mp4`: vintage map animation of Morocco.
- `jack_the_ripper_documentary.mp4`: Netflix-style documentary, 20s.
- `history_of_smoking.mp4`: Netflix-style documentary, 60s, with Arabic subtitles. The repo copy is compressed to stay under GitHub's 100MB limit.
- `morocco_intro.mp4`: a 5s documentary-style intro (archive photos of Marrakech, Rabat and Fes).
- The user likes this documentary style. Reuse it for new history videos.
