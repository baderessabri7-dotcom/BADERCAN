import random
random.seed(7)
W,H=1280,720
o=[]
a=o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
a('''<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#070a30"/><stop offset="0.62" stop-color="#2a1d6e"/><stop offset="0.85" stop-color="#5a2a86"/><stop offset="1" stop-color="#2a1d6e"/></linearGradient>
<radialGradient id="horizon" cx="0.5" cy="1" r="0.7"><stop offset="0" stop-color="#ff5fa8" stop-opacity="0.55"/><stop offset="0.5" stop-color="#ff5fa8" stop-opacity="0.12"/><stop offset="1" stop-color="#ff5fa8" stop-opacity="0"/></radialGradient>
<radialGradient id="moonglow"><stop offset="0" stop-color="#ffe9a8" stop-opacity="0.55"/><stop offset="1" stop-color="#ffe9a8" stop-opacity="0"/></radialGradient>
<radialGradient id="aura"><stop offset="0" stop-color="#b44dff" stop-opacity="0.85"/><stop offset="0.55" stop-color="#8a2be2" stop-opacity="0.35"/><stop offset="1" stop-color="#6a1bb0" stop-opacity="0"/></radialGradient>
<radialGradient id="faceglow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#9fe8ff" stop-opacity="0.5"/><stop offset="1" stop-color="#9fe8ff" stop-opacity="0"/></radialGradient>
<linearGradient id="cone" x1="0" y1="1" x2="0.4" y2="0"><stop offset="0" stop-color="#bff3ff" stop-opacity="0.55"/><stop offset="1" stop-color="#bff3ff" stop-opacity="0"/></linearGradient>
<linearGradient id="screen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8fbff"/><stop offset="1" stop-color="#7fd8ff"/></linearGradient>
<linearGradient id="lampcone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd27a" stop-opacity="0.55"/><stop offset="1" stop-color="#ffd27a" stop-opacity="0"/></linearGradient>
<filter id="blur8" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="blur20" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="20"/></filter>
<filter id="blur4" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
<filter id="blur2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2"/></filter>
<clipPath id="headclip"><path id="headp" d="M860,118 C1045,118 1095,285 1085,395 C1075,550 985,655 860,655 C735,655 645,550 635,395 C625,285 675,118 860,118 Z"/></clipPath>
</defs>''')
a(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
a(f'<rect width="{W}" height="{H}" fill="url(#horizon)"/>')
# moon (crescent), top right
a('<circle cx="1170" cy="105" r="110" fill="url(#moonglow)"/>')
a('<mask id="mm"><rect width="1280" height="720" fill="#fff"/><circle cx="1192" cy="88" r="44" fill="#000"/></mask>')
a('<circle cx="1170" cy="105" r="48" fill="#ffe08a" mask="url(#mm)"/>')
a('<path d="M1124,96 A48,48 0 0 0 1205,140" fill="none" stroke="#fff6cf" stroke-width="3" stroke-linecap="round" opacity="0.9"/>')
# far buildings
def building(x,w,h,col,win,base=720,shade=None,rim=None,density=0.45):
    y=base-h
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{col}"/>')
    if shade: a(f'<rect x="{x+w*0.68:.0f}" y="{y}" width="{w*0.32:.0f}" height="{h}" rx="10" fill="{shade}"/>')
    if rim: a(f'<rect x="{x+3}" y="{y+4}" width="4" height="{h-8}" rx="2" fill="{rim}" opacity="0.6"/>')
    ww,wh=win
    cols=max(1,int((w-16)//(ww+10)))
    rows=int((h-20)//(wh+12))
    for r in range(rows):
        for c in range(cols):
            if random.random()<density:
                wx=x+12+c*(ww+10); wy=y+16+r*(wh+12)
                colw=random.choice(['#ffd36b','#ffb84d','#ffe59a','#ff9f6b'])
                a(f'<rect x="{wx-4}" y="{wy-4}" width="{ww+8}" height="{wh+8}" rx="4" fill="{colw}" opacity="0.35" filter="url(#blur4)"/>')
                a(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="3" fill="{colw}"/>')
x=-20
while x<1300:
    w=random.randint(70,130); h=random.randint(170,290)
    building(x,w,h,'#2b2370',(10,13),shade='#231c5e',density=0.3)
    x+=w+random.randint(4,18)
# fog
a('<ellipse cx="640" cy="560" rx="760" ry="70" fill="#b78cff" opacity="0.18" filter="url(#blur20)"/>')
x=-30
while x<1300:
    w=random.randint(100,170); h=random.randint(100,190)
    building(x,w,h,'#1a1550',(14,18),shade='#130f40',rim='#ff8fd0',density=0.4)
    x+=w+random.randint(10,40)
# string lights across top-left
pts=[]
import math
for i in range(0,15):
    t=i/14; px=-10+t*720; py=40+math.sin(t*math.pi)*70
    pts.append((px,py))
a('<path d="M-10,40 Q350,180 710,40" fill="none" stroke="#3b2f80" stroke-width="3"/>')
for i,(px,py) in enumerate(pts[1:-1]):
    py=40+ (1-( (2*(px+10)/720-1)**2))*70
    c=['#ff6bb5','#ffd23f','#6be4ff','#9bff8a'][i%4]
    a(f'<circle cx="{px:.0f}" cy="{py+9:.0f}" r="14" fill="{c}" opacity="0.45" filter="url(#blur4)"/>')
    a(f'<ellipse cx="{px:.0f}" cy="{py+9:.0f}" rx="6" ry="8" fill="{c}"/>')
    a(f'<circle cx="{px-2:.0f}" cy="{py+6:.0f}" r="2" fill="#fff" opacity="0.8"/>')
# street lamp far left with cone
a('<path d="M95,520 L40,720 L240,720 L135,520 Z" fill="url(#lampcone)"/>')
a('<rect x="108" y="500" width="10" height="220" rx="5" fill="#120e3a"/>')
a('<circle cx="115" cy="505" r="30" fill="#ffd27a" opacity="0.5" filter="url(#blur8)"/>')
a('<ellipse cx="115" cy="510" rx="22" ry="12" fill="#ffd27a"/>')
a('<path d="M93,505 Q115,478 137,505 Z" fill="#120e3a"/>')
# particles (no stars) - floating glowing dust
for i in range(16):
    px=random.uniform(0,1280); py=random.uniform(420,700); r=random.uniform(3,6)
    c=random.choice(['#ffd36b','#ff8fd0','#9fe8ff'])
    a(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{r*2.5:.1f}" fill="{c}" opacity="0.35" filter="url(#blur4)"/>')
    a(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{r:.1f}" fill="{c}" opacity="0.55" filter="url(#blur2)"/>')

# ===== CHARACTER =====
# backlight behind head
a('<ellipse cx="860" cy="400" rx="330" ry="330" fill="#ff5fa8" opacity="0.25" filter="url(#blur20)"/>')
# shadow under character
a('<ellipse cx="860" cy="715" rx="380" ry="40" fill="#05051c" opacity="0.6" filter="url(#blur8)"/>')
# shirt/shoulders
a('<path d="M520,760 C530,690 600,640 700,628 L1020,628 C1120,640 1190,690 1200,760 Z" fill="#14b8a6"/>')
a('<path d="M1010,628 C1110,640 1190,690 1200,760 L1050,760 C1060,700 1050,660 1010,628 Z" fill="#0d8a7d"/>')
a('<path d="M560,700 C590,665 640,642 700,632" fill="none" stroke="#8ff5e6" stroke-width="5" stroke-linecap="round" opacity="0.8"/>')
# neck
a('<path d="M800,590 L800,650 Q860,690 920,650 L920,590 Z" fill="#d98a68"/>')
a('<path d="M770,628 Q860,700 950,628 Q860,672 770,628 Z" fill="#0d8a7d"/>')
# ears
for ex,flip in ((640,-1),(1080,1)):
    a(f'<ellipse cx="{ex}" cy="410" rx="34" ry="50" fill="#e9a07a"/>')
    a(f'<ellipse cx="{ex+flip*4}" cy="412" rx="16" ry="28" fill="#c97a5a"/>')
# head
a('<use href="#headp" fill="#f4b88f"/>')
a('<g clip-path="url(#headclip)">')
a('<ellipse cx="1150" cy="420" rx="170" ry="330" fill="#d98a68"/>')  # dark crescent right
a('<ellipse cx="560" cy="430" rx="80" ry="300" fill="#bff3ff" opacity="0.55" filter="url(#blur8)"/>')  # cool rim from phone
a('<ellipse cx="760" cy="640" rx="200" ry="90" fill="url(#faceglow)"/>')
a('</g>')
a('<path d="M655,330 C640,420 660,520 730,600" fill="none" stroke="#e9fbff" stroke-width="5" stroke-linecap="round" opacity="0.85"/>')
# hair (messy)
a('<path d="M640,330 C620,200 700,95 860,92 C1020,95 1105,200 1085,330 C1070,280 1040,250 1010,240 C1000,262 985,270 960,262 C955,230 930,215 905,225 C890,250 860,250 840,232 C820,250 790,252 770,236 C745,256 715,258 700,240 C670,262 655,290 640,330 Z" fill="#3a2350"/>')
a('<path d="M1085,330 C1105,200 1020,95 900,92 C1000,120 1050,200 1040,250 C1060,270 1075,300 1085,330 Z" fill="#26163a"/>')
# spikes
for d in ['M760,110 L730,48 L800,100 Z','M840,96 L850,30 L890,96 Z','M930,100 L985,50 L970,118 Z','M1000,130 L1060,105 L1035,160 Z','M700,140 L650,110 L690,180 Z']:
    a(f'<path d="{d}" fill="#3a2350"/>')
a('<path d="M700,160 C740,115 800,100 850,100" fill="none" stroke="#8a6bd1" stroke-width="7" stroke-linecap="round" opacity="0.7"/>')

# under-eye dark bags (big, layered)
for cx in (765,955):
    a(f'<path d="M{cx-78},400 C{cx-60},478 {cx+60},478 {cx+78},400 C{cx+55},448 {cx-55},448 {cx-78},400 Z" fill="#6a3a7a" opacity="0.75"/>')
    a(f'<path d="M{cx-70},420 C{cx-50},500 {cx+50},500 {cx+70},420 C{cx+45},470 {cx-45},470 {cx-70},420 Z" fill="#7d4a8c" opacity="0.55"/>')
    a(f'<path d="M{cx-60},445 C{cx-35},512 {cx+35},512 {cx+60},445" fill="none" stroke="#5a2d6a" stroke-width="5" stroke-linecap="round" opacity="0.6"/>')
# eyes
for cx in (765,955):
    cy=385
    a(f'<ellipse cx="{cx}" cy="{cy}" rx="62" ry="46" fill="#fff6f4"/>')
    # bloodshot veins
    for dx,dy in ((-50,10),(-46,-6),(48,8),(44,-8)):
        sx=cx+dx; sy=cy+dy
        a(f'<path d="M{sx},{sy} q{-dx*0.25:.0f},{-4} {-dx*0.45:.0f},{2} m{dx*0.2:.0f},{-1} q{-dx*0.1:.0f},6 {-dx*0.15:.0f},10" fill="none" stroke="#ff4d6d" stroke-width="2.5" stroke-linecap="round" opacity="0.8"/>')
    a(f'<circle cx="{cx}" cy="{cy+12}" r="27" fill="#5a3418"/>')
    a(f'<circle cx="{cx}" cy="{cy+12}" r="15" fill="#140a08"/>')
    a(f'<circle cx="{cx-9}" cy="{cy+2}" r="9" fill="#ffffff"/>')
    a(f'<circle cx="{cx+10}" cy="{cy+22}" r="4" fill="#ffffff" opacity="0.8"/>')
    # heavy drooping eyelid
    a(f'<path d="M{cx-66},{cy+2} C{cx-60},{cy-58} {cx+60},{cy-58} {cx+66},{cy+2} C{cx+40},{cy-8} {cx-40},{cy-8} {cx-66},{cy+2} Z" fill="#e7a07c"/>')
    a(f'<path d="M{cx-66},{cy+2} C{cx-40},{cy-8} {cx+40},{cy-8} {cx+66},{cy+2}" fill="none" stroke="#7a3f30" stroke-width="6" stroke-linecap="round"/>')
    a(f'<path d="M{cx-48},{cy-30} C{cx-20},{cy-44} {cx+20},{cy-44} {cx+48},{cy-30}" fill="none" stroke="#c97a5a" stroke-width="4" stroke-linecap="round" opacity="0.7"/>')
# eyebrows (tired / worried: inner raised)
a('<path d="M680,300 C710,282 760,262 820,252 C826,266 822,276 812,278 C760,286 718,304 690,318 C678,322 672,308 680,300 Z" fill="#3a2350"/>')
a('<path d="M1040,300 C1010,282 960,262 900,252 C894,266 898,276 908,278 C960,286 1002,304 1030,318 C1042,322 1048,308 1040,300 Z" fill="#26163a"/>')
# nose
a('<path d="M865,425 C885,455 895,480 880,495 C868,505 845,502 838,492" fill="none" stroke="#c97a5a" stroke-width="7" stroke-linecap="round"/>')
a('<ellipse cx="878" cy="498" rx="20" ry="9" fill="#c97a5a" opacity="0.6"/>')
# blush
a('<ellipse cx="715" cy="510" rx="42" ry="20" fill="#ff7a9a" opacity="0.4" filter="url(#blur4)"/>')
a('<ellipse cx="1005" cy="510" rx="42" ry="20" fill="#ff7a9a" opacity="0.35" filter="url(#blur4)"/>')
# mouth: exhausted wavy open frown
a('<path d="M800,570 C820,548 845,556 862,550 C880,544 905,552 922,572 C900,592 830,594 800,570 Z" fill="#4a1426"/>')
a('<path d="M825,582 C845,570 880,570 900,582 C880,592 845,592 825,582 Z" fill="#ff6f8a"/>')
a('<path d="M806,566 C826,548 846,556 862,550 C880,544 903,552 918,568" fill="none" stroke="#a54a3c" stroke-width="5" stroke-linecap="round"/>')
# sweat drop
a('<path d="M1060,280 C1072,300 1082,318 1070,330 C1058,340 1044,328 1050,312 C1053,302 1056,292 1060,280 Z" fill="#9fe8ff"/>')
a('<path d="M1056,312 C1056,305 1058,300 1060,296" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>')
# Zzz-like broken sleep: drooping wiggles near head? skip

# ===== VILLAIN PHONE =====
a('<path d="M640,560 L760,480 L900,520 L820,640 Z" fill="url(#cone)" opacity="0.6" filter="url(#blur8)"/>')
a('<circle cx="600" cy="560" r="170" fill="url(#aura)"/>')
a('<g transform="rotate(-12 600 565)">')
a('<rect x="520" y="420" width="160" height="290" rx="30" fill="#05051c" opacity="0.5" transform="translate(10,12)" filter="url(#blur8)"/>')
a('<rect x="520" y="420" width="160" height="290" rx="30" fill="#2a1f5c"/>')
a('<rect x="640" y="420" width="40" height="290" rx="20" fill="#1c1446"/>')
a('<rect x="523" y="430" width="5" height="250" rx="2" fill="#c49bff" opacity="0.8"/>')
a('<rect x="534" y="440" width="132" height="250" rx="20" fill="url(#screen)"/>')
a('<rect x="580" y="448" width="40" height="8" rx="4" fill="#2a1f5c"/>')
# evil face on screen
a('<path d="M548,505 L595,528" stroke="#2a0f3a" stroke-width="11" stroke-linecap="round"/>')
a('<path d="M652,505 L605,528" stroke="#2a0f3a" stroke-width="11" stroke-linecap="round"/>')
for ex in (572,628):
    a(f'<ellipse cx="{ex}" cy="545" rx="20" ry="14" fill="#ff1f3d" opacity="0.7" filter="url(#blur4)"/>')
    a(f'<path d="M{ex-16},540 Q{ex},562 {ex+16},540 Z" fill="#ff1f3d"/>')
    a(f'<circle cx="{ex+3}" cy="546" r="4" fill="#ffe0e5"/>')
a('<path d="M550,590 Q600,660 650,590 Q600,612 550,590 Z" fill="#2a0f3a"/>')
teeth=''
for i in range(6):
    tx=556+i*16
    teeth+=f'<path d="M{tx},{594+abs(2.5-i)*-1.5:.0f} l8,16 l8,-16 Z" fill="#ffffff"/>'
a(teeth)
a('<path d="M574,628 l8,-12 l8,12 Z M598,632 l8,-12 l8,12 Z M622,628 l8,-12 l8,12 Z" fill="#ffffff"/>')
a('</g>')
a('<g transform="translate(10,50)">')
# hand holding phone
a('<path d="M490,720 C480,650 500,600 545,600 C575,600 585,630 580,660 L620,640 C650,630 670,660 650,680 L600,720 Z" fill="#f4b88f"/>')
a('<path d="M560,640 C600,622 640,618 668,628 C680,640 672,656 655,655 C625,652 600,660 580,668 Z" fill="#e9a07a"/>')
a('<path d="M545,610 C560,600 575,602 580,618" fill="none" stroke="#e9fbff" stroke-width="4" stroke-linecap="round" opacity="0.8"/>')
a('</g>')
# small sparkle glints around phone (4-point sparkles OK as glints, not stars)
for sx,sy,s in ():
    a(f'<path d="M{sx},{sy-s} Q{sx+2},{sy-2} {sx+s},{sy} Q{sx+2},{sy+2} {sx},{sy+s} Q{sx-2},{sy+2} {sx-s},{sy} Q{sx-2},{sy-2} {sx},{sy-s} Z" fill="#e6c4ff"/>')
a('</svg>')
open('/home/user/BADERCAN/thumbnails/sleep-thumbnail.svg','w').write('\n'.join(o))
