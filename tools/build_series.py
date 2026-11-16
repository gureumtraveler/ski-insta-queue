"""Daily growth series: odd days = ski, even days = snowboard.
Outputs posts/sNN/*.jpg and series.json (separate from queue.json)."""
import json, math, os
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageEnhance, ImageFont

SRC = '/mnt/user-data/uploads/Claude WorkSpace/ski/'
REPO = '/home/claude/ski-insta-queue/'
OUT = REPO + 'posts/'
W, H = 1080, 1350
WHITE = (255, 255, 255); SUB = (214, 224, 236); MUTED = (160, 176, 194)
SKI_ACC = (126, 200, 255)     # blue for ski series
BRD_ACC = (255, 170, 90)      # orange for board series
HANDLE = '@gureumtraveler'

_fc = {}
def font(kind, size):
    key = (kind, size)
    if key not in _fc:
        path = '/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc' % {'B': 'Black', 'BD': 'Bold', 'R': 'Regular'}[kind]
        f = None
        for i in range(10):
            try:
                t = ImageFont.truetype(path, size, index=i)
            except Exception:
                break
            if 'KR' in t.getname()[0]:
                f = t; break
        _fc[key] = f or ImageFont.truetype(path, size)
    return _fc[key]

def cover_img(fn, fy=0.5):
    im = ImageOps.exif_transpose(Image.open(SRC + fn)).convert('RGB')
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x = (im.width - W) // 2; y = int((im.height - H) * fy)
    return im.crop((x, y, x + W, y + H))

def blurred(fn, fy=0.5, bright=0.34):
    im = cover_img(fn, fy).filter(ImageFilter.GaussianBlur(16))
    return ImageEnhance.Brightness(im).enhance(bright)

def gradient(im, top=0.5, bottom=0.9, start=0.3):
    g = Image.new('L', (1, H))
    for yy in range(H):
        t = yy / H
        a = top * (1 - t / start) if t < start else bottom * ((t - start) / (1 - start)) ** 1.15
        g.putpixel((0, yy), int(255 * max(0, min(a, 1))))
    return Image.composite(Image.new('RGB', (W, H), (8, 14, 24)), im, g.resize((W, H)))

def wrap(d, text, f, maxw):
    out = []
    for para in text.split('\n'):
        cur = ''
        for ch in para:
            if d.textlength(cur + ch, font=f) > maxw:
                sp = cur.rfind(' ')
                if sp > 0:
                    out.append(cur[:sp]); cur = cur[sp + 1:] + ch
                else:
                    out.append(cur); cur = ch
            else:
                cur += ch
        out.append(cur)
    return out

def header(d, s):
    d.text((60, 58), s['label'], font=font('BD', 30), fill=WHITE)
    d.text((W - 60, 58), HANDLE, font=font('R', 26), fill=(220, 230, 240), anchor='ra')

def page_no(d, i, n, acc):
    d.text((W - 60, H - 70), f'{i} / {n}', font=font('BD', 28), fill=acc, anchor='ra')

# ---------- slide types ----------
def s_cover(s, ep, title, sub, bg, fy=0.5):
    im = gradient(cover_img(bg, fy), top=0.55, bottom=0.92, start=0.32)
    d = ImageDraw.Draw(im); header(d, s)
    tl = wrap(d, title, font('B', 92), W - 120)
    sl = wrap(d, sub, font('R', 38), W - 120)
    y = H - 120 - len(tl) * 110 - len(sl) * 54 - 30
    d.text((60, y - 120), s['series'], font=font('BD', 34), fill=WHITE)
    d.text((60, y - 66), f'EP.{ep:02d}', font=font('B', 40), fill=s['acc'])
    for ln in tl:
        d.text((60, y), ln, font=font('B', 92), fill=WHITE); y += 110
    y += 30
    for ln in sl:
        d.text((60, y), ln, font=font('R', 38), fill=SUB); y += 54
    return im

def s_list(s, title, items, bg, note=None, fy=0.5, kicker=None):
    im = blurred(bg, fy); d = ImageDraw.Draw(im); header(d, s)
    if kicker:
        d.text((60, 160), kicker, font=font('BD', 32), fill=s['acc'])
    d.text((60, 205), title, font=font('B', 62), fill=WHITE)
    y = 330
    for num, head, body in items:
        d.text((60, y), num, font=font('B', 40), fill=s['acc'])
        d.text((150, y), head, font=font('BD', 40), fill=WHITE); y += 58
        for ln in wrap(d, body, font('R', 32), W - 210):
            d.text((150, y), ln, font=font('R', 32), fill=SUB); y += 46
        y += 30
    if note:
        yy = H - 150
        for ln in wrap(d, note, font('R', 27), W - 200):
            d.text((60, yy), ln, font=font('R', 27), fill=MUTED); yy += 38
    return im

def s_diagram(s, title, draw_fn, caption, bg, kicker=None):
    im = blurred(bg, bright=0.26); d = ImageDraw.Draw(im); header(d, s)
    if kicker:
        d.text((60, 160), kicker, font=font('BD', 32), fill=s['acc'])
    d.text((60, 205), title, font=font('B', 62), fill=WHITE)
    draw_fn(d, s['acc'])
    y = 1060
    for ln in wrap(d, caption, font('R', 34), W - 120):
        d.text((60, y), ln, font=font('R', 34), fill=SUB); y += 50
    return im

def s_next(s, done, nxt, bg):
    im = blurred(bg, bright=0.3); d = ImageDraw.Draw(im); header(d, s)
    d.text((60, 330), '오늘의 체크', font=font('BD', 36), fill=s['acc'])
    y = 390
    for t in done:
        d.rectangle((62, y + 12, 98, y + 48), outline=WHITE, width=4)
        for i, ln in enumerate(wrap(d, t, font('BD', 40), W - 200)):
            d.text((130, y), ln, font=font('BD', 40), fill=WHITE); y += 56
        y += 18
    y += 50
    d.line((60, y, W - 60, y), fill=(120, 135, 150), width=2); y += 50
    d.text((60, y), '다음 회', font=font('BD', 36), fill=s['acc']); y += 60
    for ln in wrap(d, nxt, font('B', 52), W - 120):
        d.text((60, y), ln, font=font('B', 52), fill=WHITE); y += 68
    d.text((60, H - 110), '저장해두고 슬로프에서 다시 보기', font=font('R', 32), fill=SUB)
    return im

# ---------- diagram primitives ----------
def rot(pts, cx, cy, deg):
    a = math.radians(deg); c, s_ = math.cos(a), math.sin(a)
    return [(cx + x * c - y * s_, cy + x * s_ + y * c) for x, y in pts]

def ski_shape(d, cx, cy, deg, L=520, w=46, fill=WHITE):
    # ski pointing "up" (tip at -L/2), tip rounded upturn
    h = L / 2
    pts = [(-w/2, h), (w/2, h), (w/2, -h + w), (w*0.35, -h + w*0.2), (0, -h), (-w*0.35, -h + w*0.2), (-w/2, -h + w)]
    d.polygon(rot(pts, cx, cy, deg), fill=fill)
    # binding
    b = [(-w/2 - 4, 40), (w/2 + 4, 40), (w/2 + 4, -60), (-w/2 - 4, -60)]
    d.polygon(rot(b, cx, cy, deg), fill=(60, 70, 85))

def arrow(d, x1, y1, x2, y2, col, w=6):
    d.line((x1, y1, x2, y2), fill=col, width=w)
    a = math.atan2(y2 - y1, x2 - x1)
    for s_ in (2.6, -2.6):
        d.line((x2, y2, x2 + 26 * math.cos(a + s_), y2 + 26 * math.sin(a + s_)), fill=col, width=w)

def diag_stance(d, acc):
    # ski stance side view-ish: simple stick figure with bent ankles
    cx, gy = 540, 960
    d.line((200, gy, 880, gy), fill=(200, 210, 220), width=8)       # ski
    # shins forward
    d.line((500, gy - 20, 560, gy - 230), fill=WHITE, width=16)      # shin
    d.line((560, gy - 230, 480, gy - 400), fill=WHITE, width=16)     # thigh
    d.line((480, gy - 400, 560, gy - 600), fill=WHITE, width=18)     # torso lean fwd
    d.ellipse((540, gy - 690, 620, gy - 610), fill=WHITE)            # head
    d.line((540, gy - 540, 680, gy - 430), fill=WHITE, width=12)     # arm forward
    d.rectangle((470, gy - 110, 590, gy - 10), outline=acc, width=6) # boot
    for (x, y, t) in [(620, gy - 200, '정강이 → 부츠 앞'), (700, gy - 470, '손은 앞, 허리 높이'),
                      (660, gy - 660, '시선은 멀리 앞으로'), (120, gy - 330, '엉덩이 뒤로 빼기 X')]:
        d.text((x, y), t, font=font('BD', 32), fill=acc)

def diag_wedge(d, acc):
    # left: parallel, right: wedge
    ski_shape(d, 210, 680, 0, L=480); ski_shape(d, 310, 680, 0, L=480)
    ski_shape(d, 690, 690, 18, L=480); ski_shape(d, 850, 690, -18, L=480)
    d.text((260, 980), '나란히 = 활주', font=font('BD', 34), fill=WHITE, anchor='ma')
    d.text((770, 980), '피자(웨지) = 감속', font=font('BD', 34), fill=acc, anchor='ma')
    arrow(d, 620, 900, 560, 920, acc); arrow(d, 920, 900, 980, 920, acc)
    d.text((770, 400), '앞코는 모으고', font=font('R', 30), fill=SUB, anchor='ma')

def diag_turn(d, acc):
    # S-curve path with outside-ski emphasis
    pts = []
    for i in range(0, 101):
        t = i / 100
        x = 540 + 260 * math.sin(t * math.pi * 2)
        y = 360 + 620 * t
        pts.append((x, y))
    d.line(pts, fill=(200, 210, 220), width=6, joint='curve')
    for t, side in [(0.25, 'L'), (0.75, 'R')]:
        x = 540 + 260 * math.sin(t * math.pi * 2); y = 360 + 620 * t
        # wedge icon at apex; outside ski highlighted
        ski_shape(d, x - 40, y, 18, L=200, w=26, fill=acc if side == 'L' else WHITE)
        ski_shape(d, x + 40, y, -18, L=200, w=26, fill=acc if side == 'R' else WHITE)
    d.text((140, 520), '오른쪽 턴\n= 왼발에 체중', font=font('BD', 32), fill=acc)
    d.text((700, 820), '왼쪽 턴\n= 오른발에 체중', font=font('BD', 32), fill=acc)

def board_shape(d, cx, cy, L=820, w=230, fill=(235, 240, 245)):
    r = w / 2
    d.rounded_rectangle((cx - L/2, cy - r, cx + L/2, cy + r), radius=r, fill=fill)

def binding(d, cx, cy, deg, col, hl=80):
    pts = [(-34, -hl), (34, -hl), (34, hl), (-34, hl)]
    d.polygon(rot(pts, cx, cy, deg), outline=col, width=6)
    tip = rot([(0, -hl - 26)], cx, cy, deg)[0]
    d.line((cx, cy, tip[0], tip[1]), fill=col, width=6)

def diag_stance_board(d, acc):
    board_shape(d, 540, 520, L=820, w=230)
    binding(d, 380, 520, -15, acc, hl=80); binding(d, 700, 520, 0, acc, hl=80)
    d.text((380, 360), '앞발 +15°', font=font('BD', 32), fill=acc, anchor='ma')
    d.text((700, 360), '뒷발 0°', font=font('BD', 32), fill=acc, anchor='ma')
    arrow(d, 330, 690, 150, 690, WHITE)
    d.text((360, 668), '진행 방향 (레귤러 = 왼발 앞)', font=font('BD', 30), fill=WHITE)
    board_shape(d, 540, 870, L=640, w=170, fill=(200, 208, 218))
    binding(d, 420, 870, -15, (40, 50, 62), hl=58); binding(d, 660, 870, 9, (40, 50, 62), hl=58)
    d.text((540, 975), '덕 스탠스 예: +15° / -9°', font=font('R', 28), fill=SUB, anchor='ma')

def diag_sideslip(d, acc):
    for i in range(6):
        d.line((120, 360 + i * 110, 960, 360 + i * 110), fill=(80, 95, 110), width=2)
    arrow(d, 960, 380, 960, 980, (120, 135, 150), w=4)
    d.text((940, 990), '경사 아래', font=font('R', 26), fill=MUTED, anchor='ra')
    d.text((520, 330), '앞발/뒷발 체중으로 좌우 이동 = 낙엽', font=font('R', 28), fill=SUB, anchor='ma')
    arrow(d, 360, 400, 200, 400, acc); arrow(d, 680, 400, 840, 400, acc)
    board_shape(d, 520, 560, L=600, w=150)
    d.line((240, 487, 800, 487), fill=acc, width=10)
    d.text((520, 660), '산 쪽 날 = 힐엣지(뒤꿈치)로 버티기', font=font('BD', 32), fill=acc, anchor='ma')
    d.text((520, 710), '몸은 경사 아래를 바라봄', font=font('R', 28), fill=SUB, anchor='ma')
    arrow(d, 520, 780, 520, 920, WHITE)
    d.text((560, 820), '발끝 살짝 들면 미끄러짐', font=font('R', 30), fill=SUB)
    d.text((560, 870), '뒤꿈치 누르면 멈춤', font=font('R', 30), fill=SUB)

# ---------- series definitions ----------
SKI = {'label': '구름여행자 · SKI LAB', 'series': '초보 스키어에서 스키 매니아로', 'acc': SKI_ACC}
BRD = {'label': '구름여행자 · BOARD LAB', 'series': '초보 보드, 하늘을 날다', 'acc': BRD_ACC}

SKI_TAGS = '#스키초보 #스키강습 #스키스타그램 #스키 #구름여행자'
BRD_TAGS = '#스노보드초보 #보드강습 #스노보드 #보드스타그램 #구름여행자'

EPISODES = []
def ep(date, s, num, slides, caption):
    EPISODES.append((date, s, num, slides, caption))

# SKI EP01 ----------------------------------------------------------
ep('2026-11-17', SKI, 1, [
    lambda: s_cover(SKI, 1, '첫날, 서는 법부터', '장비 맞추기와 기본 자세 — 여기서 시즌이 갈립니다', '20210226_070751.jpg'),
    lambda: s_list(SKI, '렌탈할 때 3가지만', [
        ('01', '스키 길이는 턱 높이 전후', '세웠을 때 턱 근처면 초보에게 다루기 쉽습니다. 길수록 안정적이지만 돌리기 어렵습니다.'),
        ('02', '부츠는 발가락이 살짝 닿게', '정강이를 앞으로 기울였을 때 뒤꿈치가 들뜨지 않아야 합니다. 헐거우면 스키가 말을 안 듣습니다.'),
        ('03', '폴은 겨드랑이 높이', '처음 며칠은 조금 짧아도 괜찮습니다.'),
    ], '20230123_083153.jpg', kicker='STEP 1 · 장비'),
    lambda: s_diagram(SKI, '기본 자세', diag_stance,
        '발목을 굽혀 정강이를 부츠 앞쪽에 기대고, 손은 운전대 잡듯 앞으로. 가장 흔한 실수는 무서워서 뒤로 앉는 것입니다.',
        '20210226_070801.jpg', kicker='STEP 2 · 자세'),
    lambda: s_list(SKI, '평지에서 5분 연습', [
        ('01', '스키 신고 제자리 뛰기', '앞뒤 중심을 느끼는 연습. 발 전체로 착지하면 OK.'),
        ('02', '한 발씩 들기', '한쪽 스키를 들고 3초 버티기. 반대쪽도.'),
        ('03', '폴로 밀어 미끄러지기', '두 스키를 나란히 두고 짧게 밀어서 자세 유지.'),
    ], '20210226_070714.jpg', kicker='STEP 3 · 감 잡기'),
    lambda: s_next(SKI, ['스키 길이·부츠 확인', '정강이로 부츠 누르기', '평지 한 발 들기'], 'EP.02 넘어지고, 일어나고, 걸어 올라가기', '20230120_103747.jpg'),
], '초보 스키어에서 스키 매니아로 EP.01 ⛷️\n첫날, 서는 법부터\n\n렌탈 장비 맞추기와 기본 자세만 제대로 잡아도 첫 시즌이 달라집니다.\n뒤로 앉지 말고, 정강이로 부츠 앞을 누르세요.\n\n홀수 날은 스키, 짝수 날은 보드 — 매일 한 단계씩 같이 올라가요.\n저장해두고 슬로프에서 다시 보기 📌\n\n' + SKI_TAGS)

# BOARD EP01 --------------------------------------------------------
ep('2026-11-17', BRD, 1, [
    lambda: s_cover(BRD, 1, '레귤러? 구피?\n내 스탠스 찾기', '어느 발이 앞인지부터 정해야 시작됩니다', 'DSCN1259-deviate.jpg'),
    lambda: s_list(BRD, '어느 발이 앞일까', [
        ('R', '레귤러 = 왼발 앞', '보드를 탈 때 왼발이 진행 방향 쪽.'),
        ('G', '구피 = 오른발 앞', '오른발이 진행 방향 쪽. 틀린 게 아니라 다른 것.'),
        ('?', '헷갈리면 이렇게', '양말 신고 복도에서 미끄러져 보세요. 자연스럽게 앞에 나오는 발이 앞발일 가능성이 큽니다. 첫날 타보고 바꿔도 됩니다.'),
    ], 'DSCN1251-deviate.jpg', kicker='STEP 1 · 방향'),
    lambda: s_diagram(BRD, '바인딩 각도', diag_stance_board,
        '초보는 앞발 +15° / 뒷발 0° 근처에서 많이 시작합니다. 양발을 바깥으로 벌린 덕 스탠스도 있어요. 렌탈샵에서 내 스탠스를 말하면 맞춰 줍니다.',
        'DSCN1264-deviate.jpg', kicker='STEP 2 · 세팅'),
    lambda: s_list(BRD, '렌탈할 때 체크', [
        ('01', '보드 길이', '세웠을 때 코와 턱 사이. 초보는 그 범위의 짧은 쪽이 다루기 쉽습니다.'),
        ('02', '부츠는 꽉', '발뒤꿈치가 들뜨면 엣지가 안 섭니다.'),
        ('03', '바인딩 순서', '발목 스트랩 먼저, 발가락 스트랩 나중.'),
    ], 'DSCN1260-deviate.jpg', kicker='STEP 3 · 장비'),
    lambda: s_next(BRD, ['레귤러/구피 정하기', '바인딩 각도 확인', '스트랩 순서 기억'], 'EP.02 한 발 스케이팅과 리프트 내리기', 'DSCN1176-deviate.jpg'),
], '초보 보드, 하늘을 날다 EP.01 🏂\n레귤러? 구피? 내 스탠스 찾기\n\n왼발이 앞이면 레귤러, 오른발이 앞이면 구피.\n초보 바인딩은 앞발 +15° / 뒷발 0° 근처에서 많이 시작합니다.\n\n짝수 날은 보드, 홀수 날은 스키 — 매일 한 단계씩.\n저장해두고 렌탈샵에서 꺼내 보세요 📌\n\n' + BRD_TAGS)

# SKI EP02 ----------------------------------------------------------
ep('2026-11-19', SKI, 2, [
    lambda: s_cover(SKI, 2, '잘 넘어지고,\n빨리 일어나기', '넘어지는 법을 아는 사람이 덜 다칩니다', '20230123_083158.jpg'),
    lambda: s_list(SKI, '안전하게 넘어지기', [
        ('01', '옆으로, 엉덩이부터', '앞으로 고꾸라지거나 손을 짚지 마세요. 손목·무릎 부상이 여기서 납니다.'),
        ('02', '버티지 말 것', '이미 균형을 잃었으면 낮게 앉듯이 옆으로.'),
    ], '20210226_070728.jpg', kicker='STEP 1 · 넘어지기'),
    lambda: s_list(SKI, '일어서기 3단계', [
        ('01', '스키를 경사에 가로로', '스키가 아래를 향하면 일어서는 순간 미끄러집니다. 경사를 가로지르게 놓기.'),
        ('02', '스키는 몸 아래쪽', '몸은 산 쪽(위), 스키는 계곡 쪽(아래)에.'),
        ('03', '산 쪽 손으로 밀고 일어나기', '폴을 모아 짚거나 손으로 눈을 밀어 무게를 스키 위로.'),
    ], '20230120_103745 (1).jpg', kicker='STEP 2 · 일어서기'),
    lambda: s_list(SKI, '걸어서 올라가기', [
        ('01', '사이드 스텝', '스키를 경사에 가로로 두고 게걸음으로 한 발씩. 산 쪽 날(엣지)을 눈에 박습니다.'),
        ('02', '헤링본', '앞코를 벌린 V자(피자 반대)로 오르기. 짧은 오르막에 좋습니다.'),
    ], 'DSCN1197-deviate.jpg', kicker='STEP 3 · 이동'),
    lambda: s_next(SKI, ['옆으로 넘어지기', '스키 가로로 놓고 일어서기', '사이드 스텝 10걸음'], 'EP.03 피자로 멈추기', '20210226_070751.jpg'),
], '초보 스키어에서 스키 매니아로 EP.02 ⛷️\n잘 넘어지고, 빨리 일어나기\n\n넘어질 땐 옆으로, 엉덩이부터.\n일어날 땐 스키를 경사에 가로로 놓고 산 쪽에서.\n오르막은 사이드 스텝이나 헤링본으로.\n\n같이 스키 시작한 친구에게 공유해 주세요 🙌\n\n' + SKI_TAGS)

# BOARD EP02 --------------------------------------------------------
ep('2026-11-18', BRD, 2, [
    lambda: s_cover(BRD, 2, '한 발로 밀고,\n리프트에서 내리기', '슬로프보다 리프트 하차가 먼저 무섭습니다', 'DSCN1195-deviate (1).jpg'),
    lambda: s_list(BRD, '스케이팅 (한 발 이동)', [
        ('01', '앞발만 바인딩', '뒷발은 풀고 앞발만 고정. 리프트 줄 설 때도 이 상태입니다.'),
        ('02', '뒷발로 짧게 밀기', '킥보드 타듯 보드 옆 눈을 짧게 밀어 이동.'),
        ('03', '미끄러질 땐 뒷발을 스톰프패드에', '바인딩 사이 패드에 뒷발을 올리고 무릎 굽혀 미끄러지기.'),
    ], 'DSCN1244-deviate.jpg', kicker='STEP 1 · 이동'),
    lambda: s_list(BRD, '리프트 내리기', [
        ('01', '하차 전 준비', '하차장 보이면 앞코를 정면으로, 뒷발은 스톰프패드 위.'),
        ('02', '일어서며 미끄러지기', '의자에서 밀려나듯 일어나 시선은 앞, 무릎은 굽혀서.'),
        ('03', '하차장에서 바로 비키기', '내린 뒤 그 자리에서 멈추면 다음 의자와 부딪힙니다. 옆으로 빠져서 바인딩 채우기.'),
    ], 'DSCN1268-deviate (1).jpg', kicker='STEP 2 · 리프트'),
    lambda: s_next(BRD, ['앞발만 채우고 10m 스케이팅', '스톰프패드 미끄러지기', '하차 후 옆으로 비키기'], 'EP.03 힐사이드 낙엽으로 내려오기', 'DSCN1296-deviate (1).jpg'),
], '초보 보드, 하늘을 날다 EP.02 🏂\n한 발로 밀고, 리프트에서 내리기\n\n앞발만 채우고 뒷발로 밀어 이동.\n하차할 땐 뒷발을 스톰프패드에 올리고, 내리면 바로 옆으로 비키기.\n이것만 되면 리프트가 무섭지 않아요.\n\n저장 📌 · 같이 보드 시작한 친구에게 공유\n\n' + BRD_TAGS)

# SKI EP03 ----------------------------------------------------------
ep('2026-11-21', SKI, 3, [
    lambda: s_cover(SKI, 3, '피자로 멈추기', '웨지(플루크) — 초보의 브레이크', 'DSCN1158-deviate (1).jpg'),
    lambda: s_diagram(SKI, '모양 만들기', diag_wedge,
        '앞코는 모으고 뒤꿈치를 밀어내 삼각형을 만듭니다. 앞코끼리 겹치지 않게 주먹 하나 간격.',
        '20230120_103747.jpg', kicker='STEP 1 · 웨지'),
    lambda: s_list(SKI, '속도는 폭으로 조절', [
        ('01', '좁은 피자 = 천천히', '폭을 조금만 벌리면 미끄러지면서 감속합니다.'),
        ('02', '넓은 피자 = 정지', '뒤꿈치를 더 밀어내면 멈춥니다. 양발을 똑같이 밀기.'),
        ('03', '연습 장소', '끝이 평평하게 이어지는 완만한 경사에서. 실패해도 저절로 멈추는 곳.'),
    ], '20210226_070728.jpg', kicker='STEP 2 · 조절'),
    lambda: s_list(SKI, '안 멈출 때 체크', [
        ('01', '뒤로 앉았다', '체중이 뒤로 가면 스키가 더 나갑니다. 정강이로 부츠 앞을 누르기.'),
        ('02', '무릎이 안으로 모였다', '무릎만 모으지 말고 발 전체로 뒤꿈치를 밀어내기.'),
        ('03', '아래만 본다', '시선은 멈출 지점 너머로.'),
    ], '20230120_103745 (1).jpg', kicker='STEP 3 · 문제 해결'),
    lambda: s_next(SKI, ['좁은 피자로 감속', '넓은 피자로 정지', '정지 지점 정해서 멈추기'], 'EP.04 피자로 방향 바꾸기 (플루크 턴)', 'DSCN1176-deviate.jpg'),
], '초보 스키어에서 스키 매니아로 EP.03 ⛷️\n피자로 멈추기\n\n앞코는 모으고 뒤꿈치를 밀어내 삼각형.\n좁게 벌리면 감속, 넓게 벌리면 정지.\n안 멈추면 십중팔구 뒤로 앉은 겁니다.\n\n저장해두고 첫 슬로프 전에 한 번 더 📌\n\n' + SKI_TAGS)

# BOARD EP03 --------------------------------------------------------
ep('2026-11-20', BRD, 3, [
    lambda: s_cover(BRD, 3, '힐사이드 낙엽', '보드 첫 번째 생존 기술 — 옆으로 미끄러져 내려오기', 'DSCN1296-deviate (1).jpg'),
    lambda: s_diagram(BRD, '사이드 슬립', diag_sideslip,
        '경사 아래를 바라보고, 보드는 경사에 가로로. 산 쪽에 있는 뒤꿈치 날로 버티면서 발끝을 살짝 들었다 놨다 하며 내려옵니다.',
        'DSCN1259-deviate.jpg', kicker='STEP 1 · 원리'),
    lambda: s_list(BRD, '자세 포인트', [
        ('01', '의자에 앉듯이', '무릎 굽히고 엉덩이는 낮게, 상체는 세우기. 허리만 숙이면 균형이 무너집니다.'),
        ('02', '시선은 진행 방향', '발밑 말고 내려갈 쪽을 보기.'),
        ('03', '낙엽으로 좌우 이동', '앞발에 체중을 조금 더 주면 그쪽으로, 뒷발로 옮기면 반대쪽으로.'),
    ], 'DSCN1264-deviate.jpg', kicker='STEP 2 · 자세'),
    lambda: s_list(BRD, '넘어질 때', [
        ('01', '뒤로 넘어지면', '엉덩이 먼저, 손 짚지 말고 팔은 가슴 앞으로.'),
        ('02', '앞으로 넘어지면', '무릎으로 먼저, 손목 대신 팔뚝으로.'),
        ('+', '손목 보호대', '초보 보더 부상은 손목에 몰립니다. 첫 시즌엔 꼭.'),
    ], 'DSCN1260-deviate.jpg', kicker='STEP 3 · 안전'),
    lambda: s_next(BRD, ['힐사이드로 서서 버티기', '발끝 들어 미끄러지기', '낙엽으로 좌우 이동'], 'EP.04 토사이드 낙엽 — 산을 보고 내려오기', 'DSCN1176-deviate.jpg'),
], '초보 보드, 하늘을 날다 EP.03 🏂\n힐사이드 낙엽\n\n경사 아래를 보고, 보드는 가로로.\n뒤꿈치 날로 버티면서 발끝을 살짝 들면 미끄러지고, 누르면 멈춥니다.\n앞발·뒷발 체중으로 좌우로 움직이면 낙엽.\n\n첫 시즌은 손목 보호대 꼭 🙏\n\n' + BRD_TAGS)

# SKI EP04 ----------------------------------------------------------
ep('2026-11-23', SKI, 4, [
    lambda: s_cover(SKI, 4, '피자로 방향 바꾸기', '플루크 턴 — 처음으로 원하는 곳으로 가는 날', '20230120_103745 (1).jpg', fy=0.4),
    lambda: s_diagram(SKI, '바깥발이 핸들', diag_turn,
        '피자 모양을 유지한 채 가고 싶은 쪽의 반대발(바깥발)에 체중을 더 실으면 그쪽으로 돕니다.',
        '20210226_070714.jpg', kicker='STEP 1 · 원리'),
    lambda: s_list(SKI, '순서', [
        ('01', '시선 먼저', '돌고 싶은 방향을 먼저 봅니다. 몸이 따라옵니다.'),
        ('02', '바깥발 누르기', '오른쪽으로 가려면 왼발, 왼쪽으로 가려면 오른발.'),
        ('03', '경사를 가로질러 멈추기', '턴을 끝까지 이어 경사를 가로지르면 속도가 줄고 멈출 수 있습니다.'),
    ], '20210226_070801.jpg', kicker='STEP 2 · 동작'),
    lambda: s_list(SKI, '자주 막히는 곳', [
        ('01', '상체로 비틀기', '어깨를 돌리면 스키는 안 돕니다. 발로 누르기.'),
        ('02', '피자가 무너짐', '턴 중에도 앞코 간격 유지. 무너지면 속도가 붙습니다.'),
        ('03', '한쪽만 잘 됨', '누구나 그렇습니다. 안 되는 쪽을 두 배로 연습.'),
    ], 'DSCN1197-deviate.jpg', kicker='STEP 3 · 문제 해결'),
    lambda: s_next(SKI, ['시선 → 바깥발 순서', '좌우 턴 각 5번', '턴으로 멈추기'], 'EP.05 연속 턴으로 초급 슬로프 내려오기', '20230120_103747.jpg'),
], '초보 스키어에서 스키 매니아로 EP.04 ⛷️\n피자로 방향 바꾸기 (플루크 턴)\n\n오른쪽으로 가려면 왼발, 왼쪽으로 가려면 오른발.\n시선 먼저, 그다음 바깥발.\n턴을 끝까지 이어 경사를 가로지르면 멈출 수도 있어요.\n\n저장해두고 다음 주 슬로프에서 📌\n\n' + SKI_TAGS)

# ---------- build ----------
POSTED = {('ski', 1): '17965422462252404', ('board', 1): '18118139267589166'}
series = []
for idx, (date, s, num, slides, caption) in enumerate(EPISODES, 1):
    folder = f's{idx:02d}'
    os.makedirs(OUT + folder, exist_ok=True)
    files = []
    n = len(slides)
    for i, fn in enumerate(slides, 1):
        im = fn(); d = ImageDraw.Draw(im)
        if i > 1:
            page_no(d, i, n, s['acc'])
        p = f'{folder}/{i}.jpg'; im.save(OUT + p, 'JPEG', quality=90); files.append(p)
    series.append({'date': date, 'series': 'ski' if s is SKI else 'board', 'ep': num,
                   'type': 'carousel', 'files': files, 'caption': caption})
    key = (series[-1]['series'], num)
    if key in POSTED:
        series[-1]['posted'] = True; series[-1]['media_id'] = POSTED[key]

json.dump({'account': 'gureumtraveler',
           'base_url': 'https://raw.githubusercontent.com/gureumtraveler/ski-insta-queue/main/posts/',
           'post_time_kst': '12:17', 'rule': 'odd day = ski, even day = snowboard',
           'posts': series}, open(REPO + 'series.json', 'w'), ensure_ascii=False, indent=1)
print(len(series), 'episodes')
