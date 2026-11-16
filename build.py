import json, os, textwrap
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageEnhance, ImageFont

SRC = '/mnt/user-data/uploads/Claude WorkSpace/ski/'
OUT = '/home/claude/ski-insta-queue/posts/'
W, H = 1080, 1350
KR_B = ('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc', 1)   # KR index
KR_R = ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 1)
KR_BD = ('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 1)
ACC = (126, 200, 255)

def font(spec, size):
    path, _ = spec
    # find KR face index inside the ttc
    for i in range(10):
        try:
            f = ImageFont.truetype(path, size, index=i)
        except Exception:
            break
        if 'KR' in f.getname()[0]:
            return f
    return ImageFont.truetype(path, size)

def cover(fn, w=W, h=H, fy=0.5):
    im = ImageOps.exif_transpose(Image.open(SRC + fn)).convert('RGB')
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) * fy)
    im = im.crop((x, y, x + w, y + h))
    if r > 1.3:
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    return im

def gradient(im, top=0.0, bottom=0.82, start=0.35):
    g = Image.new('L', (1, H))
    for yy in range(H):
        t = yy / H
        a = top * (1 - t / start) if t < start else 0
        if t > start:
            a = max(a, bottom * ((t - start) / (1 - start)) ** 1.2)
        g.putpixel((0, yy), int(255 * min(a, 1)))
    g = g.resize((W, H))
    black = Image.new('RGB', (W, H), (8, 14, 24))
    return Image.composite(black, im, g)

def header(d):
    d.text((60, 58), '구름여행자 · SKI LOG', font=font(KR_BD, 30), fill=(255, 255, 255))
    d.text((W - 60, 58), '@seokwoo.cloudtraveler', font=font(KR_R, 26), fill=(220, 230, 240), anchor='ra')

def wrap(d, text, f, maxw):
    lines = []
    for para in text.split('\n'):
        cur = ''
        for ch in para:
            if d.textlength(cur + ch, font=f) > maxw:
                # break at last space if possible
                sp = cur.rfind(' ')
                if sp > 0:
                    lines.append(cur[:sp]); cur = cur[sp + 1:] + ch
                else:
                    lines.append(cur); cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines

def photo_slide(fn, out, fy=0.5, label=None):
    im = cover(fn, fy=fy)
    if label:
        im = gradient(im, top=0.0, bottom=0.6, start=0.7)
        d = ImageDraw.Draw(im)
        d.text((60, H - 90), label, font=font(KR_BD, 40), fill=(255, 255, 255), anchor='ls')
    im.save(out, 'JPEG', quality=90)

def title_card(bg, out, kicker, title, sub=None, fy=0.5):
    im = gradient(cover(bg, fy=fy), top=0.55, bottom=0.88, start=0.3)
    d = ImageDraw.Draw(im)
    header(d)
    y = H - 120
    lines = wrap(d, title, font(KR_B, 86), W - 120)
    sublines = wrap(d, sub, font(KR_R, 38), W - 120) if sub else []
    total = len(lines) * 104 + (len(sublines) * 54 + 30 if sublines else 0)
    y = H - 110 - total
    d.text((60, y - 60), kicker, font=font(KR_BD, 36), fill=ACC)
    for ln in lines:
        d.text((60, y), ln, font=font(KR_B, 86), fill=(255, 255, 255)); y += 104
    if sublines:
        y += 30
        for ln in sublines:
            d.text((60, y), ln, font=font(KR_R, 38), fill=(225, 233, 242)); y += 54
    im.save(out, 'JPEG', quality=90)

def list_card(bg, out, title, items, note=None, fy=0.5):
    im = cover(bg, fy=fy).filter(ImageFilter.GaussianBlur(14))
    im = ImageEnhance.Brightness(im).enhance(0.38)
    d = ImageDraw.Draw(im)
    header(d)
    d.text((60, 170), title, font=font(KR_B, 64), fill=(255, 255, 255))
    y = 290
    fN, fT, fB = font(KR_B, 40), font(KR_BD, 40), font(KR_R, 33)
    for num, head, body in items:
        d.text((60, y), num, font=fN, fill=ACC)
        d.text((150, y), head, font=fT, fill=(255, 255, 255)); y += 56
        for ln in wrap(d, body, fB, W - 210):
            d.text((150, y), ln, font=fB, fill=(214, 224, 236)); y += 46
        y += 30
    if note:
        for ln in wrap(d, note, font(KR_R, 28), W - 120):
            d.text((60, H - 120 + 0), ln, font=font(KR_R, 28), fill=(170, 185, 200));
    im.save(out, 'JPEG', quality=90)
    return y

TAGS = '#스키 #스키장 #스키스타그램 #겨울여행 #스키어 #구름여행자'

posts = []
def add(date, kind, files, caption):
    posts.append({'date': date, 'type': kind, 'files': files, 'caption': caption})

def P(n):
    d = os.path.join(OUT, n); os.makedirs(d, exist_ok=True); return d

# 1 photo: morning slopes
d = P('01')
for i, (f, fy) in enumerate([('20210226_070728.jpg', .5), ('20210226_070714.jpg', .6), ('20210226_070751.jpg', .5), ('20210226_070801.jpg', .5)]):
    photo_slide(f, f'{d}/{i+1}.jpg', fy)
add('2026-11-18', 'carousel', ['01/1.jpg', '01/2.jpg', '01/3.jpg', '01/4.jpg'],
 '첫 리프트가 돌기 전, 아침 7시의 슬로프 🎿\n\n아무도 지나가지 않은 정설 라인.\n이 장면 하나 보려고 일찍 움직입니다.\n\n올 시즌도 곧 시작이네요. 여러분은 첫 출격 언제인가요?\n\n' + TAGS + ' #정설 #아침스키 #스키시즌')

# 2 info: season opening
d = P('02')
title_card('20230120_103745 (1).jpg', f'{d}/1.jpg', '26/27 SEASON', '스키장 개장,\n이제 곧입니다', '평창권부터 11월 말 순차 개장 목표', fy=.4)
list_card('20230120_103747.jpg', f'{d}/2.jpg', '개장 전 알아둘 것', [
 ('01', '평창권이 가장 먼저', '모나용평은 10월 22일 첫 제설을 시작하고 11월 말 개장을 목표로 준비 중입니다.'),
 ('02', '날짜는 날씨가 정합니다', '개장일과 첫 운영 슬로프는 기온·제설 여건에 따라 바뀝니다. 출발 전 공식 홈페이지·SNS 공지를 꼭 확인하세요.'),
 ('03', '수도권은 그다음', '예년에는 강원권이 먼저 열고, 수도권·남부권 리조트가 12월 중순까지 순차 개장했습니다.'),
 ('04', '숙소는 확정 후 결제', '개장일이 확정되기 전에는 취소 가능한 조건으로 예약해 두세요.'),
], note='※ 각 리조트 공식 공지 기준으로 다시 확인하세요.')
add('2026-11-19', 'carousel', ['02/1.jpg', '02/2.jpg'],
 '26/27 시즌, 스키장 개장 체크 ⛷️\n\n평창권 리조트들이 11월 말 개장을 목표로 제설에 들어갔습니다.\n정확한 개장일과 운영 슬로프는 날씨에 따라 바뀌니\n출발 전에 공식 공지 한 번 더 확인하세요.\n\n저장해두고 개장 소식 뜨면 바로 출발 🚗\n\n' + TAGS + ' #스키장개장 #시즌오픈 #평창 #모나용평 #휘닉스파크')

# 3 photo: night skiing
d = P('03')
photo_slide('20161210_200400_HDR.jpg', f'{d}/1.jpg')
photo_slide('20161210_200313_HDR.jpg', f'{d}/2.jpg')
photo_slide('20161210_200313_HDR-EFFECTS.jpg', f'{d}/3.jpg')
add('2026-11-20', 'carousel', ['03/1.jpg', '03/2.jpg', '03/3.jpg'],
 '조명 아래 야간 스키 🌙\n\n해가 지면 슬로프 분위기가 완전히 달라집니다.\n제설기 안개 사이로 조명이 번지는 밤 슬로프.\n\n야간파 vs 주간파, 여러분은?\n\n' + TAGS + ' #야간스키 #나이트스키 #퇴근후스키')

# 4 info: FIS rules
d = P('04')
title_card('20210226_070751.jpg', f'{d}/1.jpg', 'SAFETY FIRST', '슬로프 위의\n교통법규 10가지', '국제스키연맹(FIS)이 정한 스키어·보더 행동 규칙', fy=.5)
list_card('20210226_070801.jpg', f'{d}/2.jpg', 'FIS 규칙 1 – 5', [
 ('01', '다른 사람을 배려', '남을 위험하게 하거나 피해를 주지 않게 탄다.'),
 ('02', '속도와 방식 조절', '실력·지형·설질·날씨·혼잡도에 맞춰 멈출 수 있는 속도로.'),
 ('03', '진로 선택', '뒤에서 오는 사람이 앞사람을 피해 라인을 고른다.'),
 ('04', '추월', '앞사람이 어느 쪽으로 움직여도 될 만큼 여유를 두고.'),
 ('05', '진입·출발', '합류하거나 출발할 때는 위아래를 먼저 확인.'),
])
list_card('20210226_070714.jpg', f'{d}/3.jpg', 'FIS 규칙 6 – 10', [
 ('06', '멈추는 위치', '좁거나 시야가 가려지는 곳에서는 서지 않기. 넘어지면 빨리 비키기.'),
 ('07', '걸어서 오르내릴 때', '슬로프 가장자리로.'),
 ('08', '표지판 준수', '모든 표지와 안내 표시를 따른다.'),
 ('09', '사고 시 구조', '사고를 보면 누구든 도울 의무가 있다.'),
 ('10', '신원 확인', '사고 관련자와 목격자는 이름·연락처를 교환한다.'),
], note='출처: FIS Rules for the Conduct of Skiers and Snowboarders (요약 번역)')
add('2026-11-21', 'carousel', ['04/1.jpg', '04/2.jpg', '04/3.jpg'],
 '슬로프에도 교통법규가 있습니다 🚦\n\n국제스키연맹(FIS)이 정한 스키어·스노보더 행동 규칙 10가지.\n특히 2번(속도 조절)과 3번(뒤에서 오는 사람이 피한다)만 지켜도\n충돌 사고 대부분을 줄일 수 있어요.\n\n같이 타는 친구에게 공유해 주세요 🙏\n\n' + TAGS + ' #스키안전 #FIS #슬로프매너 #스키초보')

# 5 photo: Zao night
d = P('05')
for i, f in enumerate(['DSCN1123-deviate (1).jpg', 'DSCN1122-deviate.jpg', 'DSCN1124-deviate (1).jpg', 'DSCN1114-deviate (1).jpg', 'DSCN1115-deviate (1).jpg']):
    photo_slide(f, f'{d}/{i+1}.jpg')
add('2026-11-22', 'carousel', [f'05/{i}.jpg' for i in range(1, 6)],
 '야마가타 자오 온천 스키장의 밤 🏮\n\n눈 덮인 침엽수 사이로 리프트 불빛이 이어지고,\n발밑은 정설된 코듀로이.\n타고 내려와서 바로 온천에 들어가는 게 자오의 정석입니다.\n\n' + TAGS + ' #자오온천 #자오온천스키장 #일본스키 #야마가타 #야간스키 #蔵王温泉')

# 6 info: Zao juhyo
d = P('06')
title_card('DSCN1168-deviate (1).jpg', f'{d}/1.jpg', 'ZAO · YAMAGATA', '스노 몬스터,\n언제 가야 볼까', '자오 수빙(樹氷) 보러 가기 전 체크', fy=.35)
list_card('DSCN1158-deviate (1).jpg', f'{d}/2.jpg', '자오 수빙 핵심 정리', [
 ('01', '수빙이란', '전나무가 상고대와 눈에 통째로 덮여 괴물처럼 변한 모습. 현지에선 주효(樹氷)라고 부릅니다.'),
 ('02', '시기', '1월에 커지고 2월에 절정, 3월부터 무너지기 시작합니다.'),
 ('03', '가는 길', '자오 로프웨이를 타고 주효고원을 지나 지조산초(해발 1,661m)까지 올라갑니다.'),
 ('04', '라이트업', '12월 말~2월 말 중 지정된 밤에만 열립니다. 일정은 매년 공식 사이트에서 확인하세요.'),
], note='날씨가 나쁘면 로프웨이가 멈추거나 시야가 없을 수 있어요. 일정에 하루 여유를 두세요.')
add('2026-11-23', 'carousel', ['06/1.jpg', '06/2.jpg'],
 '자오의 스노 몬스터(수빙)를 보려면 언제 가야 할까? 👾❄️\n\n1월에 자라고 2월에 절정, 3월부터는 무너지기 시작합니다.\n로프웨이로 정상 지조산초까지 올라가면 사방이 수빙 숲.\n야간 라이트업은 지정된 날에만 하니 공식 일정 꼭 확인하세요.\n\n저장해두고 2월 일본 스키 계획에 넣어보세요 📌\n\n' + TAGS + ' #자오 #자오온천 #수빙 #스노우몬스터 #일본여행 #야마가타 #樹氷')

# 7 photo: Zao day
d = P('07')
for i, (f, fy) in enumerate([('DSCN1176-deviate.jpg', .5), ('DSCN1251-deviate.jpg', .4), ('DSCN1156-deviate (1).jpg', .5), ('DSCN1259-deviate.jpg', .5), ('DSCN1264-deviate.jpg', .5), ('DSCN1168-deviate (1).jpg', .35)]):
    photo_slide(f, f'{d}/{i+1}.jpg', fy)
add('2026-11-24', 'carousel', [f'07/{i}.jpg' for i in range(1, 7)],
 '자오 온천 스키장, 낮의 얼굴 ☀️\n\n긴 슬로프를 따라 내려가다 보면 아래로 온천 마을이 보입니다.\n마지막 장은 수빙 앞에서 한 컷.\n\n' + TAGS + ' #자오온천스키장 #일본스키 #야마가타 #스키여행 #파우더')

# 8 info: Carv 2
d = P('08')
title_card('20161210_200400_HDR.jpg', f'{d}/1.jpg', 'SKI TECH', '내 스키를\n숫자로 본다', '디지털 스키 코치 Carv 2 써보기 전 알아둘 것', fy=.5)
list_card('20210226_070728.jpg', f'{d}/2.jpg', 'Carv 2는 이렇게 작동합니다', [
 ('01', '부츠에 클립 2개', '좌우 부츠 스트랩에 센서를 끼우면 끝. 부츠 안 깔창이 필요 없습니다.'),
 ('02', '6축 모션 센서', '자이로스코프와 가속도계로 부츠 움직임을 읽습니다.'),
 ('03', 'Ski:IQ', '10가지 기술 지표를 종합한 점수로 매 런을 평가합니다.'),
 ('04', '오프라인 OK', '슬로프에서 데이터 연결 없이도 동작하고, 이어폰으로 실시간 코칭을 들을 수 있어요.'),
 ('05', '스키 전용', '스노보드는 지원하지 않습니다.'),
], note='출처: getcarv.com 및 제품 리뷰 기준')
add('2026-11-25', 'carousel', ['08/1.jpg', '08/2.jpg'],
 '감으로 타던 스키, 숫자로 보면 달라집니다 📊\n\n제가 쓰는 디지털 스키 코치 Carv 2.\n부츠에 센서 두 개 끼우고 타면 턴마다 엣지·밸런스를 분석해서\nSki:IQ 점수와 코칭을 줍니다.\n\n여러분이라면 어떤 지표가 제일 궁금하세요?\n\n' + TAGS + ' #Carv #카브 #디지털스키코치 #스키레슨 #스키기술')

# 9 photo: gear day
d = P('09')
for i, (f, fy) in enumerate([('20251103_135043.jpg', .5), ('20251103_135032.jpg', .5), ('20251205_203237.jpg', .5), ('20251205_202740.jpg', .5), ('20251205_203207.jpg', .5)]):
    photo_slide(f, f'{d}/{i+1}.jpg', fy)
add('2026-11-26', 'carousel', [f'09/{i}.jpg' for i in range(1, 6)],
 '시즌 전 장비 점검 🛠️\n\n스키샵 구경하고, 부츠 꺼내 버클·라이너 상태부터 확인.\n빨간 부츠들이 줄 서 있으니 겨울이 왔다는 실감이 납니다.\n\n여러분 장비는 준비 끝났나요?\n\n' + TAGS + ' #스키부츠 #스키장비 #시즌준비 #스키샵')

# 10 info: checklist
d = P('10')
title_card('20230123_083153.jpg', f'{d}/1.jpg', 'CHECKLIST', '첫 출격 전\n장비 체크 5', '창고에서 꺼낸 장비, 그대로 타면 안 됩니다', fy=.45)
list_card('20230123_083158.jpg', f'{d}/2.jpg', '시즌 전 체크리스트', [
 ('01', '바인딩', '해제값(DIN)과 부츠 맞춤 상태는 전문 샵에서 점검받기.'),
 ('02', '엣지·베이스', '녹·버(burr) 확인, 시즌 시작 전 왁싱.'),
 ('03', '부츠', '버클·스트랩 파손 확인, 라이너는 완전히 말려서.'),
 ('04', '헬멧·고글', '헬멧 충격 흔적, 고글 렌즈 스크래치·김서림 확인.'),
 ('05', '리프트권·보험', '시즌권·할인권 사용 조건과 여행자·레저 보험 확인.'),
])
add('2026-11-27', 'carousel', ['10/1.jpg', '10/2.jpg'],
 '창고에서 꺼낸 장비, 그대로 타면 안 됩니다 ✅\n\n첫 출격 전 5가지만 체크하세요.\n특히 바인딩은 직접 만지지 말고 샵에서 점검받는 게 안전합니다.\n\n저장해두고 출발 전날 한 번 더 확인 📌\n\n' + TAGS + ' #스키장비 #스키왁싱 #바인딩 #시즌준비 #스키초보')

# 11 photo: bluebird vs snow
d = P('11')
photo_slide('20230120_103745 (1).jpg', f'{d}/1.jpg', .4)
photo_slide('20230120_103747.jpg', f'{d}/2.jpg', .4)
photo_slide('P_20160130_094344.jpg', f'{d}/3.jpg', .5)
add('2026-11-28', 'carousel', ['11/1.jpg', '11/2.jpg', '11/3.jpg'],
 '맑은 날의 슬로프 vs 눈 오는 날의 숲 🌤️🌨️\n\n파란 하늘 아래 쭉 뻗은 슬로프도 좋고,\n안개 낀 상고대 숲 사이를 천천히 내려오는 날도 좋습니다.\n\n여러분은 어느 쪽?\n\n' + TAGS + ' #블루버드 #상고대 #설경 #겨울풍경')

# 12 info: layering
d = P('12')
title_card('DSCN1260-deviate.jpg', f'{d}/1.jpg', 'WHAT TO WEAR', '스키복은\n3겹이면 충분', '덥지도 춥지도 않게, 레이어링 기본', fy=.5)
list_card('DSCN1264-deviate.jpg', f'{d}/2.jpg', '레이어링 3단계', [
 ('01', '베이스 레이어', '땀을 밖으로 빼주는 기능성 내의. 면 소재는 젖으면 마르지 않아 피하세요.'),
 ('02', '미드 레이어', '플리스나 얇은 패딩으로 보온. 기온에 따라 두께만 조절.'),
 ('03', '아우터', '방수·방풍 재킷과 팬츠. 겨드랑이 벤틸레이션이 있으면 편합니다.'),
 ('+', '작은 것들', '스키 양말은 한 켤레만 두껍지 않게, 넥워머와 여분 장갑 챙기기.'),
])
add('2026-11-29', 'carousel', ['12/1.jpg', '12/2.jpg'],
 '스키장에서 뭐 입지? 3겹이면 충분합니다 🧥\n\n베이스(땀 배출) + 미드(보온) + 아우터(방수·방풍).\n제일 흔한 실수는 면 티셔츠 — 땀에 젖으면 리프트 위에서 바로 추워져요.\n\n처음 가는 친구에게 공유해 주세요 🙌\n\n' + TAGS + ' #스키복 #레이어링 #스키초보 #스키장코디')

# 13 photo: lifts
d = P('13')
for i, f in enumerate(['DSCN1197-deviate.jpg', 'DSCN1195-deviate (1).jpg', 'DSCN1244-deviate.jpg', 'DSCN1268-deviate (1).jpg', 'DSCN1296-deviate (1).jpg']):
    photo_slide(f, f'{d}/{i+1}.jpg')
add('2026-11-30', 'carousel', [f'13/{i}.jpg' for i in range(1, 6)],
 '리프트 위에서 보는 풍경 🚡\n\n올라가는 5분이 내려오는 1분만큼 좋은 이유.\n눈 쌓인 침엽수, 줄지어 올라가는 체어, 해 질 녘 마을 불빛까지.\n\n' + TAGS + ' #리프트 #곤돌라 #자오온천 #일본스키 #설경')

# 14 engagement
d = P('14')
title_card('DSCN1176-deviate.jpg', f'{d}/1.jpg', 'DECEMBER', '올겨울, 어디서\n첫 턴을 그릴까요?', '가장 가고 싶은 스키장을 댓글로 알려주세요', fy=.45)
add('2026-12-01', 'image', ['14/1.jpg'],
 '12월, 진짜 시즌 시작입니다 ❄️\n\n올겨울 가장 가고 싶은 스키장은 어디인가요?\n국내든 해외든 댓글로 알려주시면\n다녀온 곳은 제가 아는 만큼 팁 정리해 드릴게요.\n\n' + TAGS + ' #스키시즌 #12월 #스키여행 #스키장추천')

json.dump({'account': 'seokwoo.cloudtraveler', 'base_url': 'https://raw.githubusercontent.com/gureumtraveler/ski-insta-queue/main/posts/',
           'post_time_kst': '19:00', 'posts': posts}, open('/home/claude/ski-insta-queue/queue.json', 'w'), ensure_ascii=False, indent=1)
print(len(posts))
