"""
라즈베리파이 피코 USB HID 볼륨 컨트롤러
- 로터리 엔코더(KY-040)로 볼륨 조절
- 네오픽셀 LED로 볼륨 레벨 표시
- USB HID를 통한 컴퓨터 볼륨 제어
"""
# 필요한 라이브러리들을 가져옵니다.
import time
import usb_hid
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
import board
import digitalio
import neopixel

# --- 1. 설정 (Constants) ---
# 이 부분의 값만 수정하면 프로젝트의 동작을 쉽게 변경할 수 있습니다.

# [하드웨어 핀 설정]
CLK_PIN = board.GP12  # 로터리 엔코더 CLK 핀
DT_PIN = board.GP11   # 로터리 엔코더 DT 핀
SW_PIN = board.GP10   # 로터리 엔코더 스위치 핀
LED_PIN = board.GP6   # 네오픽셀 LED 데이터 핀

# [네오픽셀 LED 설정]
NUM_PIXELS = 12        # 연결된 네오픽셀 LED의 개수
RAINBOW_BRIGHTNESS = 0.1  # 기본 무지개 효과의 밝기 (0.0 ~ 1.0)

# [동작 시간 및 민감도 설정]
# 시간 단위는 나노초(ns)입니다. (1초 = 1,000,000,000 ns)
SW_DEBOUNCE_NS = 200_000_000         # 스위치 버튼 디바운싱 시간 (0.2초)
VOLUME_DISPLAY_NS = 2_000_000_000    # 볼륨 조절 후 LED 표시 유지 시간 (2초)
PLAY_PAUSE_DISPLAY_NS = 1_000_000_000 # 재생/일시정지 후 LED 표시 유지 시간 (1초)
RAINBOW_UPDATE_NS = 50_000_000       # 무지개 효과 업데이트 간격 (0.05초)

# [로터리 엔코더 상태 테이블]
# 이전 상태(2비트)와 현재 상태(2비트)를 조합한 4비트 값으로 회전 방향을 판단합니다.
# 이 테이블 덕분에 빠르고 정확한 엔코더 감지가 가능합니다.
# key: (이전 CLK, 이전 DT, 현재 CLK, 현재 DT)의 4비트 값
# value: +1 (시계방향), -1 (반시계방향)
ENCODER_STATE_TABLE = {
    0b0001: -1, 0b0010: 1,  0b0100: 1,  0b0111: -1,
    0b1000: -1, 0b1011: 1,  0b1101: 1,  0b1110: -1,
}

# --- 2. 하드웨어 초기화 ---

# 로터리 엔코더 핀을 내부 풀업 저항이 있는 디지털 입력으로 설정합니다.
clk = digitalio.DigitalInOut(CLK_PIN)
clk.direction = digitalio.Direction.INPUT
clk.pull = digitalio.Pull.UP

dt = digitalio.DigitalInOut(DT_PIN)
dt.direction = digitalio.Direction.INPUT
dt.pull = digitalio.Pull.UP

sw = digitalio.DigitalInOut(SW_PIN)
sw.direction = digitalio.Direction.INPUT
sw.pull = digitalio.Pull.UP

# 네오픽셀 LED 객체를 생성합니다. auto_write=False로 설정하여 수동으로 write()를 호출할 때만 LED가 갱신되도록 합니다.
pixels = neopixel.NeoPixel(LED_PIN, NUM_PIXELS, auto_write=False, brightness=RAINBOW_BRIGHTNESS)

# PC에 미디어 제어 신호를 보낼 HID 객체를 생성합니다.
consumer_control = ConsumerControl(usb_hid.devices)


# --- 3. 유틸리티 및 LED 표시 함수 ---

def hsv_to_rgb(h, s, v):
    """HSV 색상 모델을 RGB로 변환하는 함수"""
    if s == 0.0: return (v, v, v)
    h = h % 360
    i = int(h / 60)
    f = (h / 60) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    
    # 튜플의 각 값을 정수로 변환하여 반환
    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else: r, g, b = v, p, q
    return (int(r * 255), int(g * 255), int(b * 255))

def show_rainbow(offset):
    """은은하게 움직이는 무지개 효과를 LED에 표시"""
    pixels.brightness = RAINBOW_BRIGHTNESS  # 기본 밝기로 설정
    for i in range(NUM_PIXELS):
        hue = (i * 360 // NUM_PIXELS + offset) % 360
        pixels[i] = hsv_to_rgb(hue, 1.0, 1.0)
    pixels.write()

def show_volume_level(level):
    """현재 볼륨 레벨을 LED 막대 그래프 형태로 표시"""
    pixels.brightness = 0.5  # 볼륨 표시는 조금 더 밝게
    pixels.fill((0, 0, 0))  # 모든 LED를 끔
    
    lit_pixels = int((level / 100) * NUM_PIXELS)
    
    # 볼륨 크기에 따라 색상 결정 (낮음: 녹색, 중간: 노란색, 높음: 빨간색)
    color = (0, 150, 0)
    if level >= 70: color = (150, 0, 0)
    elif level >= 30: color = (150, 150, 0)
        
    for i in range(lit_pixels):
        pixels[i] = color
    pixels.write()

def show_play_pause_feedback(is_playing):
    """재생/일시정지 상태를 LED 깜빡임으로 피드백"""
    pixels.brightness = 0.3
    if is_playing:
        pixels.fill((0, 80, 0))  # 재생: 녹색
    else:
        pixels.fill((80, 0, 0))  # 일시정지: 빨간색
    pixels.write()
    time.sleep(0.3) # 짧은 피드백 후 원래 상태로 돌아가기 위함


# --- 4. 메인 프로그램 (Main Logic) ---

def run_volume_controller():
    print("USB HID 볼륨 컨트롤러 시작")
    
    # 프로그램 상태를 저장하는 변수들
    volume_level = 20.0  # 현재 볼륨 레벨 (0-100)
    is_playing = True    # 현재 재생 상태
    rainbow_offset = 0   # 무지개 효과의 시작 색상 위치
    
    # 시간 기반 상태 관리를 위한 변수들
    last_volume_change_time = 0
    last_play_pause_time = 0
    last_rainbow_update_time = 0
    
    # 로터리 엔코더 상태 초기화 (현재 핀 상태를 읽어 초기값 설정)
    last_encoder_state = (clk.value << 1) | dt.value
    last_sw_state = sw.value
    last_sw_change_time = 0

    while True:
        current_time = time.monotonic_ns()

        # 1. 로터리 엔코더 처리
        encoder_state = (clk.value << 1) | dt.value
        if encoder_state != last_encoder_state:
            # 상태 테이블 조회를 위해 4비트 키 생성
            lookup_key = (last_encoder_state << 2) | encoder_state
            direction = ENCODER_STATE_TABLE.get(lookup_key, 0) # 테이블에 없으면 0 (무시)

            if direction != 0:
                # 볼륨 조절 및 최대/최소값 제한
                volume_level = max(0, min(100, volume_level + (direction * 2)))
                # PC로 볼륨 조절 신호 전송
                if direction > 0:
                    consumer_control.send(ConsumerControlCode.VOLUME_INCREMENT)
                else:
                    consumer_control.send(ConsumerControlCode.VOLUME_DECREMENT)
                
                print(f"볼륨: {int(volume_level)}%")
                show_volume_level(volume_level)
                last_volume_change_time = current_time # 마지막 변경 시간 기록
            
            last_encoder_state = encoder_state # 현재 상태를 다음 루프를 위해 저장

        # 2. 스위치 버튼 처리
        sw_state = sw.value
        # 버튼이 눌렸을 때 (신호가 LOW가 될 때) 그리고 디바운싱 시간이 지났을 때
        if sw_state != last_sw_state and not sw_state:
            if (current_time - last_sw_change_time) > SW_DEBOUNCE_NS:
                is_playing = not is_playing
                consumer_control.send(ConsumerControlCode.PLAY_PAUSE)
                
                print("재생/일시정지 토글")
                show_play_pause_feedback(is_playing)
                last_play_pause_time = current_time
                last_sw_change_time = current_time
        
        last_sw_state = sw_state

        # 3. LED 디스플레이 상태 관리 (우선순위: 볼륨 > 재생/일시정지 > 무지개)
        # 아무런 입력이 없을 때만 무지개 효과를 표시합니다.
        # 볼륨/재생 표시는 해당 이벤트가 발생했을 때 이미 처리되었으므로,
        # 여기서는 일정 시간 동안 다른 효과가 나오지 않도록 막는 역할만 합니다.
        if (current_time - last_volume_change_time) < VOLUME_DISPLAY_NS:
            pass # 볼륨 표시 유지
        elif (current_time - last_play_pause_time) < PLAY_PAUSE_DISPLAY_NS:
            pass # 재생/일시정지 피드백 후 대기
        else:
            # 기본 상태: 무지개 효과를 일정 간격으로 업데이트
            if (current_time - last_rainbow_update_time) > RAINBOW_UPDATE_NS:
                rainbow_offset = (rainbow_offset + 1) % 360
                show_rainbow(rainbow_offset)
                last_rainbow_update_time = current_time
        
        # CPU 자원을 불필요하게 사용하지 않도록 아주 짧은 대기시간을 줍니다.
        time.sleep(0.001)

# 이 스크립트가 직접 실행될 때만 함수를 호출합니다.
if __name__ == "__main__":
    run_volume_controller()
