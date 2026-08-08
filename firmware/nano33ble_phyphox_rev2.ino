/*
 * Nano 33 BLE Sense Rev2 + phyphox — 전체 내장 센서 펌웨어
 * 대응 실험 파일(01~10 .phyphox)과 세트로 사용.
 *
 * choice 매핑 (실험 파일의 <config>가 연결 시 자동 전송):
 *   1  가속도       write(t, ax, ay, az, |a|)      [g]
 *   2  자이로       write(t, gx, gy, gz, |g|)      [°/s]
 *   3  자기장       write(t, mx, my, mz, |m|)      [uT]
 *   6  색상/조도    write(t, ambient, r, g, b)     [counts]
 *   9  외장 아날로그 write(t, V_A0, V_A1, V_A2)     [V]
 *   11 환경 통합    write(t, P[hPa], T기압계, T습도계, RH[%])
 *   12 제스처       write(t, code)  1=왼쪽 2=오른쪽 3=아래→위 4=위→아래
 *   13 근접         write(t, prox)  0(가까움)~255(멀음)
 *   14 음량         write(t, dBFS, rms)  (상대 음량, 파형 아님)
 *
 * 이전 버전과의 호환: choice 1~6, 9, 11 동일. 4(기압), 5(온습도)도 유지.
 */

#include <phyphoxBle.h>
#include <Arduino_BMI270_BMM150.h>   // IMU
#include <Arduino_LPS22HB.h>         // 기압/온도
#include <Arduino_HS300x.h>          // 온도/습도
#include <Arduino_APDS9960.h>        // 근접/조도/색상/제스처
#include <PDM.h>                     // 내장 마이크

char board_name[] = "Nano";

float choice = 0.0;
unsigned long t0 = 0;                // 측정 시작 기준 시각
unsigned long lastSend = 0;
const unsigned int PERIOD_ENV  = 100; // 환경(기압/온습도) 전송 주기 ms
const unsigned int PERIOD_SLOW = 50;  // 근접/조도 등 주기 ms

const int ledR = 22, ledG = 23, ledB = 24;

// ---- 마이크 ----
static const char PDM_CHANNELS = 1;
static const int  PDM_FREQ = 16000;
short sampleBuffer[512];
volatile int samplesRead = 0;

void onPDMdata() {
  int bytesAvailable = PDM.available();
  PDM.read(sampleBuffer, bytesAvailable);
  samplesRead = bytesAvailable / 2;
}

void receivedData() {
  if (PhyphoxBLE::currentConnections >= 1) {
    PhyphoxBLE::read(choice);
    t0 = millis();
  }
}

float nowSec() { return (millis() - t0) / 1000.0f; }

void setup() {
  PhyphoxBLE::minConInterval = 6;   // 7.5 ms
  PhyphoxBLE::maxConInterval = 6;
  PhyphoxBLE::slaveLatency = 0;
  PhyphoxBLE::timeout = 10;

  pinMode(ledR, OUTPUT); pinMode(ledG, OUTPUT); pinMode(ledB, OUTPUT);
  digitalWrite(ledR, LOW); digitalWrite(ledG, HIGH); digitalWrite(ledB, HIGH);

  if (!IMU.begin())    while (1);
  if (!BARO.begin())   while (1);
  if (!HS300x.begin()) while (1);
  if (!APDS.begin())   while (1);

  PDM.onReceive(onPDMdata);
  PDM.begin(PDM_CHANNELS, PDM_FREQ);   // 실패해도 다른 센서는 동작하도록 중단하지 않음

  PhyphoxBLE::start(board_name);
  PhyphoxBLE::configHandler = &receivedData;
}

void loop() {
  PhyphoxBLE::poll();

  bool connected = (PhyphoxBLE::currentConnections > 0);
  digitalWrite(ledR, connected ? HIGH : LOW);
  digitalWrite(ledG, connected ? LOW  : HIGH);

  float t = nowSec();
  float x, y, z, m;

  if (choice == 1.0f) {                       // 가속도 [g]
    if (IMU.accelerationAvailable()) {
      IMU.readAcceleration(x, y, z);
      m = sqrtf(x * x + y * y + z * z);
      PhyphoxBLE::write(t, x, y, z, m);
    }

  } else if (choice == 2.0f) {                // 자이로 [°/s]
    if (IMU.gyroscopeAvailable()) {
      IMU.readGyroscope(x, y, z);
      m = sqrtf(x * x + y * y + z * z);
      PhyphoxBLE::write(t, x, y, z, m);
    }

  } else if (choice == 3.0f) {                // 자기장 [uT]
    if (IMU.magneticFieldAvailable()) {
      IMU.readMagneticField(x, y, z);
      m = sqrtf(x * x + y * y + z * z);
      PhyphoxBLE::write(t, x, y, z, m);
    }

  } else if (choice == 4.0f) {                // (구버전 호환) 기압 [hPa]
    if (millis() - lastSend > PERIOD_ENV) {
      lastSend = millis();
      float p = BARO.readPressure() * 10.0f;  // kPa → hPa
      PhyphoxBLE::write(t, p);
    }

  } else if (choice == 5.0f) {                // (구버전 호환) 온습도
    if (millis() - lastSend > PERIOD_ENV) {
      lastSend = millis();
      float temp = HS300x.readTemperature();
      float hum  = HS300x.readHumidity();
      PhyphoxBLE::write(t, temp, hum);
    }

  } else if (choice == 6.0f) {                // 색상/조도 [counts]
    if (APDS.colorAvailable()) {
      int r, g, b, a;
      APDS.readColor(r, g, b, a);
      float rf = r, gf = g, bf = b, af = a;
      PhyphoxBLE::write(t, af, rf, gf, bf);
    }

  } else if (choice == 9.0f) {                // 외장 아날로그 [V]
    float v0 = analogRead(A0) * 3.3f / 1023.0f;
    float v1 = analogRead(A1) * 3.3f / 1023.0f;
    float v2 = analogRead(A2) * 3.3f / 1023.0f;
    PhyphoxBLE::write(t, v0, v1, v2);
    delay(2);

  } else if (choice == 11.0f) {               // 환경 통합: 기압+온도2종+습도
    if (millis() - lastSend > PERIOD_ENV) {
      lastSend = millis();
      float p     = BARO.readPressure() * 10.0f;  // hPa
      float tBaro = BARO.readTemperature();       // 기압계 내장 온도
      float tHum  = HS300x.readTemperature();     // 습도계 내장 온도
      float rh    = HS300x.readHumidity();        // %
      PhyphoxBLE::write(t, p, tBaro, tHum, rh);
    }

  } else if (choice == 12.0f) {               // 제스처 (이벤트 발생 시만 전송)
    if (APDS.gestureAvailable()) {
      int g = APDS.readGesture();
      float code = 0.0f;
      if      (g == GESTURE_LEFT)  code = 1.0f;  // 왼쪽
      else if (g == GESTURE_RIGHT) code = 2.0f;  // 오른쪽
      else if (g == GESTURE_UP)    code = 3.0f;  // 아래→위
      else if (g == GESTURE_DOWN)  code = 4.0f;  // 위→아래
      if (code > 0.0f) PhyphoxBLE::write(t, code);
    }

  } else if (choice == 13.0f) {               // 근접 0(가까움)~255(멀음)
    if (millis() - lastSend > PERIOD_SLOW && APDS.proximityAvailable()) {
      lastSend = millis();
      int p = APDS.readProximity();
      if (p >= 0) { float pf = p; PhyphoxBLE::write(t, pf); }
    }

  } else if (choice == 14.0f) {               // 음량 (상대 dBFS)
    if (samplesRead > 0) {
      float sum = 0.0f;
      int n = samplesRead;
      for (int i = 0; i < n; i++) {
        float s = sampleBuffer[i];
        sum += s * s;
      }
      samplesRead = 0;
      float rms = sqrtf(sum / n);
      if (rms > 0.5f) {
        float db = 20.0f * log10f(rms / 32768.0f);  // 0 dBFS = 최대
        PhyphoxBLE::write(t, db, rms);
      }
    }
  }
}
