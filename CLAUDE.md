# Project notes

## Video preferences
- Make all new videos **16:9 landscape (1920x1080)** unless the user asks otherwise.
- `morocco_map_animation.mp4` is an older 9:16 (1080x1920) video. Keep it as it is.

## Video tools
`video-tools/` holds the scripts that made the Morocco map animation (documentary-style map with a ship following a dotted route):
- `make_map.py <workdir>`: builds the parchment map (`map.png`). It needs `<workdir>/geo/countries.geojson` (Natural Earth 50m countries) and fonts in `<workdir>/fonts/` (Cinzel, Amiri-Bold, IM Fell English).
- `animate.py <workdir> <out.mp4>`: renders the frames. The output size is set by `OW, OH`, so use 1920x1080 for new videos and adjust the title and caption positions to match.
- `audio.py <out.wav>`: makes the soundtrack (waves, oud-like plucks in hijaz, frame drum). It needs scipy.
- `documentary/`: the Netflix-style documentary edit used for `jack_the_ripper_documentary.mp4` (1920x1080). It uses black-and-white archive images, red hand-drawn circles and arrows, black headline boxes and film grain. Scenes are defined in `scenes.py`. Run it with `doc.py <workdir> <fontsdir> <out.mp4>`; images go in `<workdir>/img/`. Fonts: Anton, Cairo, Marhey, Special Elite. The archive images come from Wikimedia Commons (public domain, 1888).
