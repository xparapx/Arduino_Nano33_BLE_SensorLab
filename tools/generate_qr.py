# -*- coding: utf-8 -*-
# tools/generate_qr.py  — 실행: 저장소 루트에서 python tools/generate_qr.py
# 의존성: pip install "qrcode[pil]"
import qrcode, os

BASE = "https://xparapx.github.io/Arduino_Nano33_BLE_WebUI_Demo/phyphox"
SRC, QR = "docs/phyphox", "docs/phyphox/qr"
os.makedirs(QR, exist_ok=True)

targets = sorted(f for f in os.listdir(SRC) if f.endswith(".phyphox"))
targets.append("nano33_experiments.zip")

for f in targets:
    name = "all_experiments" if f.endswith(".zip") else f.replace(".phyphox", "")
    qrcode.make(f"{BASE}/{f}", box_size=8, border=2).save(f"{QR}/{name}.png")
    print("QR:", name)
