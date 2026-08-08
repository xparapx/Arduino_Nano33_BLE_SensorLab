# -*- coding: utf-8 -*-
"""Nano 33 BLE Sense Rev2 — phyphox 실험 파일 세트 생성기 (v2)
v2 변경: 아이콘 영문 약자, 브랜드 색 #42EAFF, 환경 실험을 온습도/기압온도로 분리,
        제스처 화살표 전용 화면, 외장 센서 별도 카테고리(목록 최하단 고정)
"""
import struct, os, zipfile
import xml.etree.ElementTree as ET

OUT = "../docs/phyphox"  # 실행 위치: tools/ 디렉터리에서 python generate_experiments.py
os.makedirs(OUT, exist_ok=True)

DEV = "Nano"
DATA_CH = "cddf1002-30f7-4671-8b43-5e40ba53514a"
CONF_CH = "cddf1003-30f7-4671-8b43-5e40ba53514a"
CAT = "Nano 33 BLE Sense"
CAT_EXT = "Nano 33 BLE Sense (외장)"   # 뒤 카테고리 → 목록 최하단
BRAND = "42eaff"                        # 아이콘/카테고리 색 #42EAFF

# 그래프·값 팔레트
CX, CY, CZ, CM = "ff5252", "69f0ae", "40c4ff", "ffd740"
CR, CG, CB, CA = "ff5252", "66bb6a", "42a5f5", "ffd740"
CP, CT1, CT2, CH = "4fc3f7", "ff8a65", "ffab91", "81d4fa"
CPROX, CSND = "ce93d8", "4dd0e1"

def fhex(v):
    return struct.pack("<f", v).hex()

def bt_input(choice, outputs):
    """outputs: list of (buffer, byte_offset)"""
    rows = [f'        <config char="{CONF_CH}" conversion="hexadecimal">{fhex(choice)}</config>']
    for buf, off in outputs:
        rows.append(f'        <output char="{DATA_CH}" conversion="float32LittleEndian" offset="{off}">{buf}</output>')
    body = "\n".join(rows)
    return f'''    <input>
        <bluetooth name="{DEV}" mode="notification" subscribeOnStart="true">
{body}
        </bluetooth>
    </input>'''

def containers(names):
    inner = "\n".join(f'        <container size="0">{n}</container>' for n in names)
    return f"    <data-containers>\n{inner}\n    </data-containers>"

def graph(label, ylab, yunit, curves, style="lines", lw="1.5"):
    ins = []
    for xb, yb, c in curves:
        ins.append(f'            <input axis="x">{xb}</input>')
        col = f' color="{c}"' if c else ""
        ins.append(f'            <input axis="y"{col}>{yb}</input>')
    body = "\n".join(ins)
    return (f'        <graph label="{label}" labelX="시간" unitX="s" labelY="{ylab}" '
            f'unitY="{yunit}" partialUpdate="true" style="{style}" lineWidth="{lw}">\n{body}\n        </graph>')

def value(label, buf, unit="", color=None, size="2", precision="2", maps=None):
    col = f' color="{color}"' if color else ""
    u = f' unit="{unit}"' if unit else ""
    m = ""
    if maps:
        rows = []
        for lo, hi, txt in maps:
            a = f' min="{lo}"' if lo is not None else ""
            b = f' max="{hi}"' if hi is not None else ""
            rows.append(f'            <map{a}{b}>{txt}</map>')
        m = "\n" + "\n".join(rows)
    return (f'        <value label="{label}" size="{size}" precision="{precision}"{u}{col}>\n'
            f'            <input>{buf}</input>{m}\n        </value>')

def info(text, bold=False):
    b = ' bold="true"' if bold else ""
    return f'        <info label="{text}"{b}/>'

SEP = '        <separator height="0.3"/>'

def view(label, elements):
    body = "\n".join(elements)
    return f'    <view label="{label}">\n{body}\n    </view>'

GUIDE = [
    info("사용 방법", bold=True), SEP,
    info("1. Nano 33 보드의 전원을 켭니다 (연결되면 LED가 초록색)."),
    info("2. 재생(▶) 버튼을 누르면 자동으로 연결되어 측정이 시작됩니다."),
    info("3. 일시정지 후 다시 시작하면 이어서 기록됩니다. 휴지통 아이콘으로 초기화."),
    info("4. 데이터 저장: 우측 상단 메뉴 → '데이터 내보내기' (CSV / Excel)."),
]

def export(setname, pairs):
    rows = "\n".join(f'            <data name="{n}">{b}</data>' for n, b in pairs)
    return f'''    <export>
        <set name="{setname}">
{rows}
        </set>
    </export>'''

def doc(fname, title, icon, desc, conts, inp, views, exp, category=CAT):
    v = "\n".join(views)
    xml = f'''<phyphox xmlns="http://phyphox.org/xml" version="1.14">
    <title>{title}</title>
    <icon format="string">{icon}</icon>
    <color>{BRAND}</color>
    <category>{category}</category>
    <description>{desc}</description>

{containers(conts)}

{inp}

    <analysis sleep="0" onUserInput="false"></analysis>

    <views>
{v}
    </views>

{exp}
</phyphox>
'''
    path = os.path.join(OUT, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    ET.parse(path)
    return path

# ---------- 벡터형 ----------
def vector_exp(fname, choice, title, icon, desc, unit, comp_note):
    conts = ["t", "vx", "vy", "vz", "vm"]
    outs = [("t",0),("vx",4),("vy",8),("vz",12),("vm",16)]
    views = [
        view("그래프", [
            graph(f"{title} (x·y·z)", title, unit,
                  [("t","vx",CX),("t","vy",CY),("t","vz",CZ)]),
            graph("크기 |v|", "|v|", unit, [("t","vm",CM)], lw="2"),
        ]),
        view("성분별", [
            graph("x 성분", "x", unit, [("t","vx",CX)]),
            graph("y 성분", "y", unit, [("t","vy",CY)]),
            graph("z 성분", "z", unit, [("t","vz",CZ)]),
        ]),
        view("측정값", [
            info("실시간 측정값 (x=빨강, y=초록, z=파랑)", bold=True), SEP,
            value("x", "vx", unit, CX, precision="3"),
            value("y", "vy", unit, CY, precision="3"),
            value("z", "vz", unit, CZ, precision="3"), SEP,
            value("크기 |v|", "vm", unit, CM, size="3", precision="3"),
        ]),
        view("안내", GUIDE + [SEP, info(comp_note)]),
    ]
    exp = export(f"{title} 데이터", [("t (s)","t"),(f"x ({unit})","vx"),
                 (f"y ({unit})","vy"),(f"z ({unit})","vz"),(f"|v| ({unit})","vm")])
    return doc(fname, title, icon, desc, conts, bt_input(choice, outs), views, exp)

vector_exp("01_acceleration.phyphox", 1.0, "가속도", "ACC",
    "BMI270 IMU로 3축 가속도를 측정합니다. 정지 상태에서 |a| ≈ 1 g 입니다.",
    "g", "센서: BMI270, 중력 포함 가속도. 1 g = 9.81 m/s²")
vector_exp("02_gyroscope.phyphox", 2.0, "자이로스코프", "GYR",
    "BMI270 IMU로 3축 각속도를 측정합니다.",
    "°/s", "센서: BMI270, 각속도(회전 속도)")
vector_exp("03_magnetometer.phyphox", 3.0, "자기장", "MAG",
    "BMM150으로 3축 자기장을 측정합니다. 지구 자기장은 약 25~65 µT입니다.",
    "µT", "센서: BMM150. 주변 전자기기·철제 구조물의 영향에 주의")

# ---------- 온도·습도 (choice 11 스트림의 t2, rh만 사용) ----------
doc("04_temp_humidity.phyphox", "온도·습도", "T/H",
    "HS3003 센서로 온도와 상대 습도를 측정합니다.",
    ["t", "temp", "hum"],
    bt_input(11.0, [("t",0),("temp",12),("hum",16)]),
    [
        view("그래프", [
            graph("온도", "온도", "°C", [("t","temp",CT1)], lw="2"),
            graph("상대 습도", "습도", "%", [("t","hum",CH)], lw="2"),
        ]),
        view("측정값", [
            value("온도", "temp", "°C", CT1, size="3"),
            value("상대 습도", "hum", "%", CH, size="3", precision="1"),
        ]),
        view("안내", GUIDE + [SEP,
            info("보드 자체 발열로 실제 기온보다 약간 높게 측정될 수 있습니다."),
            info("입김을 불거나 손으로 감싸 온·습도 변화를 관찰해 보세요.")]),
    ],
    export("온습도 데이터", [("t (s)","t"),("온도 (°C)","temp"),("습도 (%)","hum")]))

# ---------- 기압·온도 (choice 11 스트림의 p, t1만 사용) ----------
doc("05_pressure_temp.phyphox", "기압·온도", "P/T",
    "LPS22HB 센서로 기압과 온도를 측정합니다. 고도 변화 관찰에 적합합니다.",
    ["t", "press", "temp"],
    bt_input(11.0, [("t",0),("press",4),("temp",8)]),
    [
        view("그래프", [
            graph("기압", "기압", "hPa", [("t","press",CP)], lw="2"),
            graph("온도", "온도", "°C", [("t","temp",CT1)], lw="2"),
        ]),
        view("측정값", [
            value("기압", "press", "hPa", CP, size="3", precision="1"),
            value("온도", "temp", "°C", CT1, size="3"),
        ]),
        view("안내", GUIDE + [SEP,
            info("고도가 1 m 높아지면 기압은 약 0.12 hPa 낮아집니다."),
            info("계단이나 엘리베이터에서 기압 변화로 층간 높이를 재어 보세요.")]),
    ],
    export("기압온도 데이터", [("t (s)","t"),("기압 (hPa)","press"),("온도 (°C)","temp")]))

# ---------- 색상 (RGB) ----------
doc("06_color.phyphox", "색상 (RGB)", "RGB",
    "APDS9960으로 빛의 R·G·B 성분을 측정합니다. 성분별 차트와 수치를 제공합니다.",
    ["t", "amb", "cr", "cg", "cb"],
    bt_input(6.0, [("t",0),("amb",4),("cr",8),("cg",12),("cb",16)]),
    [
        view("그래프", [
            graph("RGB 성분", "세기", "counts",
                  [("t","cr",CR),("t","cg",CG),("t","cb",CB)]),
        ]),
        view("성분별", [
            graph("Red", "R", "counts", [("t","cr",CR)]),
            graph("Green", "G", "counts", [("t","cg",CG)]),
            graph("Blue", "B", "counts", [("t","cb",CB)]),
        ]),
        view("측정값", [
            info("실시간 색상 성분", bold=True), SEP,
            value("Red", "cr", "counts", CR, precision="0"),
            value("Green", "cg", "counts", CG, precision="0"),
            value("Blue", "cb", "counts", CB, precision="0"), SEP,
            value("밝기 (Clear)", "amb", "counts", CA, precision="0"),
        ]),
        view("안내", GUIDE + [SEP,
            info("센서 위에 색이 있는 물체나 조명을 비추어 보세요."),
            info("값은 상대적 세기(counts)이며 조명 밝기에 따라 달라집니다.")]),
    ],
    export("색상 데이터", [("t (s)","t"),("R (counts)","cr"),("G (counts)","cg"),
        ("B (counts)","cb"),("Clear (counts)","amb")]))

# ---------- 조도 ----------
doc("07_illuminance.phyphox", "조도", "LUX",
    "APDS9960의 Clear 채널로 주변 밝기를 측정합니다.",
    ["t", "amb", "cr", "cg", "cb"],
    bt_input(6.0, [("t",0),("amb",4),("cr",8),("cg",12),("cb",16)]),
    [
        view("그래프", [graph("주변 밝기", "밝기", "counts", [("t","amb",CA)], lw="2")]),
        view("측정값", [value("밝기", "amb", "counts", CA, size="3", precision="0")]),
        view("안내", GUIDE + [SEP,
            info("상대적 밝기(counts)입니다. lux 환산이 필요하면 조도계와 비교 보정하세요.")]),
    ],
    export("조도 데이터", [("t (s)","t"),("밝기 (counts)","amb")]))

# ---------- 제스처 (화살표 전용 화면, 그래프 없음) ----------
arrow_maps = [(None, 0.5, "·"),
              (0.5, 1.5, "←"),
              (1.5, 2.5, "→"),
              (2.5, 3.5, "↑"),
              (3.5, None, "↓")]
text_maps  = [(None, 0.5, "손을 움직여 보세요"),
              (0.5, 1.5, "왼쪽으로"),
              (1.5, 2.5, "오른쪽으로"),
              (2.5, 3.5, "아래에서 위로"),
              (3.5, None, "위에서 아래로")]
doc("08_gesture.phyphox", "제스처", "GES",
    "APDS9960 위에서 손을 움직이면 방향(왼쪽/오른쪽/위/아래)을 인식합니다.",
    ["t", "gest"],
    bt_input(12.0, [("t",0),("gest",4)]),
    [
        view("제스처", [
            info("센서 위 3~10 cm에서 손을 한 방향으로 움직이세요.", bold=True),
            SEP,
            value("", "gest", "", BRAND, size="6", precision="0", maps=arrow_maps),
            value("", "gest", "", "ffffff", size="1.5", precision="0", maps=text_maps),
            SEP,
        ]),
        view("안내", GUIDE + [SEP,
            info("방향은 USB 커넥터를 아래로 두었을 때 기준입니다."),
            info("인식이 안 되면 손을 조금 더 천천히, 가까이에서 움직여 보세요."),
            info("동작 기록(시각·코드)은 데이터 내보내기로 저장할 수 있습니다.")]),
    ],
    export("제스처 데이터", [("t (s)","t"),("제스처 코드 (1왼쪽 2오른쪽 3위로 4아래로)","gest")]))

# ---------- 근접 ----------
pmaps = [(None, 30, "매우 가까움"), (30, 100, "가까움"),
         (100, 200, "중간"), (200, None, "멀음")]
doc("09_proximity.phyphox", "근접", "PRX",
    "APDS9960으로 물체와의 상대 거리를 측정합니다. 0(가까움)~255(멀음).",
    ["t", "prox"],
    bt_input(13.0, [("t",0),("prox",4)]),
    [
        view("그래프", [graph("근접값 (작을수록 가까움)", "근접", "", [("t","prox",CPROX)], lw="2")]),
        view("측정값", [
            value("근접값", "prox", "", CPROX, size="3", precision="0"), SEP,
            value("판정", "prox", "", CPROX, size="2", precision="0", maps=pmaps),
        ]),
        view("안내", GUIDE + [SEP,
            info("적외선 반사 방식이라 물체의 색/재질에 따라 값이 달라집니다."),
            info("정밀 거리 측정이 아닌 상대적 근접도 지표입니다.")]),
    ],
    export("근접 데이터", [("t (s)","t"),("근접값 (0-255)","prox")]))

# ---------- 음량 ----------
doc("10_sound.phyphox", "음량", "SND",
    "내장 마이크(MP34DT06)로 소리의 크기를 측정합니다. 0 dBFS가 최대이며 값은 음수입니다.",
    ["t", "db", "rms"],
    bt_input(14.0, [("t",0),("db",4),("rms",8)]),
    [
        view("그래프", [
            graph("음량 레벨", "레벨", "dBFS", [("t","db",CSND)], lw="2"),
            graph("RMS 진폭", "RMS", "", [("t","rms",CM)]),
        ]),
        view("측정값", [value("음량", "db", "dBFS", CSND, size="3", precision="1")]),
        view("안내", GUIDE + [SEP,
            info("BLE 대역폭 한계로 파형이 아닌 '크기(레벨)'를 전송합니다."),
            info("상대값(dBFS)이므로 절대 dB(SPL)와는 다릅니다. 큰 소리일수록 0에 가까워집니다.")]),
    ],
    export("음량 데이터", [("t (s)","t"),("레벨 (dBFS)","db"),("RMS","rms")]))

# ---------- 외장 아날로그 (별도 카테고리 → 목록 최하단) ----------
doc("11_analog_external.phyphox", "외장 센서 (아날로그)", "EXT",
    "A0·A1·A2 핀의 전압을 측정합니다. 외장 아날로그 센서를 연결해 사용하세요.",
    ["t", "v0", "v1", "v2"],
    bt_input(9.0, [("t",0),("v0",4),("v1",8),("v2",12)]),
    [
        view("그래프", [
            graph("아날로그 입력 (A0·A1·A2)", "전압", "V",
                  [("t","v0",CX),("t","v1",CY),("t","v2",CZ)]),
        ]),
        view("성분별", [
            graph("A0", "전압", "V", [("t","v0",CX)]),
            graph("A1", "전압", "V", [("t","v1",CY)]),
            graph("A2", "전압", "V", [("t","v2",CZ)]),
        ]),
        view("측정값", [
            info("실시간 전압 (A0=빨강, A1=초록, A2=파랑)", bold=True), SEP,
            value("A0", "v0", "V", CX, precision="3"),
            value("A1", "v1", "V", CY, precision="3"),
            value("A2", "v2", "V", CZ, precision="3"),
        ]),
        view("안내", GUIDE + [SEP,
            info("센서 출력을 A0~A2에, GND를 보드 GND에 연결하세요 (0~3.3 V 범위!)."),
            info("물리량 환산(예: 전압→온도)은 펌웨어의 choice 9 수식을 수정하세요.")]),
    ],
    export("아날로그 데이터", [("t (s)","t"),("A0 (V)","v0"),("A1 (V)","v1"),("A2 (V)","v2")]),
    category=CAT_EXT)

# ---------- zip ----------
files = sorted(f for f in os.listdir(OUT) if f.endswith(".phyphox"))
zip_path = os.path.join(OUT, "nano33_experiments.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(os.path.join(OUT, f), f)

print("생성 완료 (%d개):" % len(files))
for f in files:
    print(" -", f)
print("zip:", zip_path)
