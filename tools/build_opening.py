import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont

REPO = '/home/claude/ski-insta-queue/posts/'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/out/opening'
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1350
ACC = (126, 200, 255)
WHITE = (255, 255, 255)
SUB = (214, 224, 236)
MUTED = (160, 176, 194)
GREEN = (120, 220, 160)
AMBER = (255, 196, 110)
GRAY = (150, 160, 172)

_fc = {}
def font(kind, size):
    key = (kind, size)
    if key in _fc:
        return _fc[key]
    path = {'B': 'Black', 'BD': 'Bold', 'R': 'Regular', 'M': 'Medium'}[kind]
    path = f'/usr/share/fonts/opentype/noto/NotoSansCJK-{path}.ttc'
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

def bg(src, blur=14, bright=0.36):
    im = Image.open(REPO + src).convert('RGB').resize((W, H))
    im = im.filter(ImageFilter.GaussianBlur(blur))
    return ImageEnhance.Brightness(im).enhance(bright)

def header(d, page=None):
    d.text((60, 58), '구름여행자 · SKI LOG', font=font('BD', 30), fill=WHITE)
    d.text((W - 60, 58), '@gureumtraveler', font=font('R', 26), fill=(220, 230, 240), anchor='ra')

def footer(d, text):
    d.text((60, H - 70), text, font=font('R', 26), fill=MUTED)

def chip(d, x, y, text, color, anchor='la'):
    f = font('BD', 26)
    w = d.textlength(text, font=f)
    if anchor == 'ra':
        x = x - w - 32
    d.rounded_rectangle((x, y, x + w + 32, y + 44), radius=22, outline=color, width=3)
    d.text((x + 16, y + 22), text, font=f, fill=color, anchor='lm')

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

# ---------- 1. cover ----------
def cover():
    im = Image.open(REPO + '11/1.jpg').convert('RGB').resize((W, H))
    # gradient bottom
    g = Image.new('L', (1, H))
    for y in range(H):
        t = y / H
        a = 0.5 * (1 - t / 0.25) if t < 0.25 else 0.9 * ((t - 0.25) / 0.75) ** 1.1
        g.putpixel((0, y), int(255 * max(0, min(a, 1))))
    im = Image.composite(Image.new('RGB', (W, H), (8, 14, 24)), im, g.resize((W, H)))
    d = ImageDraw.Draw(im)
    header(d)
    d.text((60, 820), '26/27 SEASON · 11.17 기준', font=font('BD', 36), fill=ACC)
    d.text((60, 880), '스키장 개장일', font=font('B', 96), fill=WHITE)
    d.text((60, 995), '+ 지금 살 수 있는 특가', font=font('B', 70), fill=WHITE)
    d.text((60, 1110), '휘닉스·모나용평·하이원부터 수도권까지', font=font('R', 38), fill=SUB)
    d.text((60, 1162), '저장해두고 출발 전에 꺼내 보세요', font=font('R', 38), fill=SUB)
    d.text((W - 60, H - 70), '넘겨보기 →', font=font('BD', 30), fill=WHITE, anchor='ra')
    im.save(f'{OUT}/1.jpg', 'JPEG', quality=90)

# ---------- 2/3. opening tables ----------
def table(fn, src, kicker, title, rows, note, compact=False):
    im = bg(src)
    d = ImageDraw.Draw(im)
    header(d)
    d.text((60, 160), kicker, font=font('BD', 32), fill=ACC)
    d.text((60, 205), title, font=font('B', 64), fill=WHITE)
    y = 340
    for name, region, date, status, color, memo in rows:
        d.line((60, y, W - 60, y), fill=(255, 255, 255, 60), width=1)
        y += 28
        d.text((60, y), name, font=font('BD', 46), fill=WHITE)
        sub = region + (' · ' + memo if (compact and memo) else '')
        d.text((60, y + 64), sub, font=font('R', 30), fill=MUTED if not compact else SUB)
        d.text((W - 60, y + 2), date, font=font('B', 46), fill=WHITE, anchor='ra')
        chip(d, W - 60, y + 66, status, color, anchor='ra')
        y += 124 if not compact else 112
        if memo and not compact:
            for ln in wrap(d, memo, font('R', 29), W - 120):
                d.text((60, y), ln, font=font('R', 29), fill=SUB); y += 40
        y += 22
    footer(d, note)
    im.save(f'{OUT}/{fn}', 'JPEG', quality=90)

# ---------- 4. deals ----------
def deals():
    im = bg('13/1.jpg')
    d = ImageDraw.Draw(im)
    header(d)
    d.text((60, 160), 'DEALS · 지금 판매 중', font=font('BD', 32), fill=ACC)
    d.text((60, 205), '놓치기 아까운 특가 3', font=font('B', 64), fill=WHITE)
    items = [
        ('곤지암 얼리버드 리프트권', '~12/6', 'NOL 단독',
         '리프트권 최대 36%, 렌탈 패키지 최대 47%. 주중 2시간 44,000원~ / 주말 54,000원~. 수량 소진 시 조기 종료.'),
        ('X6+ 시즌패스 2차', '판매 중', 'NOL 단독',
         '모나용평·하이원·지산·웰리힐리·엘리시안강촌·알펜시아 6곳 무제한. 성인권 사면 19세 이하 자녀 1매 무료.'),
        ('휘닉스 시즌패스 2차', '~11/30', '공식 홈페이지',
         '19세 미만 자녀 최대 2명 등록, 등록 자녀 장비 무료 대여. 권종별 혜택이 달라 약관 확인 필수.'),
    ]
    y = 340
    for title, until, where, body in items:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).rounded_rectangle((60, y, W - 60, y + 250), radius=28, fill=(255, 255, 255, 28), outline=(255, 255, 255, 140), width=2)
        im.paste(Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB'))
        d = ImageDraw.Draw(im)
        d.text((96, y + 30), title, font=font('BD', 42), fill=WHITE)
        d.text((W - 96, y + 34), until, font=font('B', 38), fill=AMBER, anchor='ra')
        d.text((96, y + 88), where, font=font('BD', 26), fill=ACC)
        yy = y + 130
        for ln in wrap(d, body, font('R', 29), W - 200):
            d.text((96, yy), ln, font=font('R', 29), fill=SUB); yy += 38
        y += 280
    footer(d, '가격·조건은 판매처 기준(11.17 확인), 구매 전 상품 페이지 재확인')
    im.save(f'{OUT}/4.jpg', 'JPEG', quality=90)

# ---------- 5. tips ----------
def tips():
    im = bg('01/1.jpg')
    d = ImageDraw.Draw(im)
    header(d)
    d.text((60, 160), 'TIP · 시즌 초반 공략', font=font('BD', 32), fill=ACC)
    d.text((60, 205), '개장 직후 가기 전에', font=font('B', 64), fill=WHITE)
    items = [
        ('01', '첫날은 일부 슬로프만', '개장 초에는 초·중급 위주로 몇 면만 엽니다. 운영 슬로프 표를 보고 가세요.'),
        ('02', '개장일 이벤트는 SNS에', '작년 휘닉스는 개장일 현장 리프트권을 3만 원 균일가로 팔았습니다. 올해 혜택은 개장 공지를 확인하세요.'),
        ('03', '숙소는 취소 가능하게', '개장일은 기온·제설에 따라 밀립니다. 날짜 확정 전엔 환불 가능한 조건으로 예약.'),
        ('04', '얼리버드는 기간·수량 한정', '판매 마감일과 사용 가능 기간(개장~폐장)이 다릅니다. 둘 다 확인.'),
    ]
    y = 345
    fN, fT, fB = font('B', 40), font('BD', 40), font('R', 32)
    for num, head, body in items:
        d.text((60, y), num, font=fN, fill=ACC)
        d.text((150, y), head, font=fT, fill=WHITE); y += 58
        for ln in wrap(d, body, fB, W - 210):
            d.text((150, y), ln, font=fB, fill=SUB); y += 46
        y += 34
    footer(d, '저장해두고, 같이 갈 친구에게 공유하세요')
    im.save(f'{OUT}/5.jpg', 'JPEG', quality=90)

cover()
table('2.jpg', '11/2.jpg', 'OPENING · 11월 개장 그룹', '강원 고지대가 먼저',
      [('휘닉스 스노우파크', '강원 평창', '11.27(금)', '개장 계획', GREEN, '기상 여건이 허락하면 11/27 개장, 2027.3.14까지 운영 계획'),
       ('모나용평', '강원 평창', '11월 말', '목표', AMBER, '10/22 레드 슬로프 첫 제설. 정확한 날짜는 제설 여건 보고 결정'),
       ('하이원리조트', '강원 정선', '11월 말', '예정', AMBER, '10/28 첫 제설 시작')],
      '출처: 리조트 발표 보도(연합뉴스·강원일보 등), 11.17 기준')
table('3.jpg', '03/1.jpg', 'OPENING · 12월 개장 그룹', '수도권·영서는 아직',
      [('비발디파크', '강원 홍천', '12월 초?', '미발표', GRAY, '작년 25/26 시즌 12/5 개장'),
       ('웰리힐리파크', '강원 횡성', '12월 초?', '미발표', GRAY, '작년 12/5 개장'),
       ('엘리시안 강촌', '강원 춘천', '12월 초?', '미발표', GRAY, '작년 12/5 개장, 전철로 가는 스키장'),
       ('지산리조트', '경기 이천', '12월 중순?', '미발표', GRAY, '작년 12/12 개장'),
       ('곤지암리조트', '경기 광주', '미정', '미발표', GRAY, None)],
      '"?" 표시는 작년 개장일 기준 추정입니다', compact=True)
deals()
tips()
print('ok', sorted(os.listdir(OUT)))
