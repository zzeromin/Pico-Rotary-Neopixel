import board
import digitalio
import rotaryio
import neopixel
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# 1. 하드웨어 및 키보드 초기화
keyboard = Keyboard(usb_hid.devices)
encoder = rotaryio.IncrementalEncoder(board.GP12, board.GP11)
last_position = encoder.position

button = digitalio.DigitalInOut(board.GP10)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP
last_button = button.value

pixels = neopixel.NeoPixel(board.GP15, 8, brightness=0.2, auto_write=True)
pixels.fill((0, 0, 0))

# 2. 상태별 LED 컬러 정의 (R, G, B)
COLOR_FORWARD = (255, 0, 127)  # ⏩ 10초 앞으로 (핫핑크)
COLOR_REWIND  = (0, 255, 255)  # ⏪ 10초 뒤로 (사이언)
COLOR_PAUSE   = (180, 0, 255)  # ⏯️ 재생/일시정지 (보라)

# 3. 시간 제어 변수 (쿨다운 및 디바운스)
SEEK_COOLDOWN = 0.15           # 탐색 쿨다운 (연속 회전 시 부드러운 반응을 위해 0.15초 조정)
last_seek_time = 0

def seek_animation(color, direction_forward=True):
    """LED 회전 방향 애니메이션"""
    pixel_range = range(8) if direction_forward else range(7, -1, -1)
    for i in pixel_range:
        pixels[i] = color
        time.sleep(0.01)
    time.sleep(0.03)
    pixels.fill((0, 0, 0))

print("🎬 유튜브 컨트롤러 준비 완료! 브라우저 창 활성화 후 조작하세요.")

while True:
    current_time = time.monotonic()

    # [기능 1] 엔코더 회전: 10초 앞/뒤 탐색 (J / L)
    current_position = encoder.position
    if current_position != last_position:
        if current_time - last_seek_time > SEEK_COOLDOWN:
            if current_position > last_position:
                keyboard.send(Keycode.L)  # 유튜브 +10초 탐색
                seek_animation(COLOR_FORWARD, direction_forward=True)
            else:
                keyboard.send(Keycode.J)  # 유튜브 -10초 탐색
                seek_animation(COLOR_REWIND, direction_forward=False)
            last_seek_time = current_time
        last_position = current_position

    # [기능 2] 엔코더 버튼: 재생 / 일시정지 (K)
    current_button = button.value
    # 버튼이 눌렸을 때 (Active LOW)
    if not current_button and last_button:
        keyboard.send(Keycode.K)          # 유튜브 표준 재생/일시정지
        pixels.fill(COLOR_PAUSE)
        time.sleep(0.15)
        pixels.fill((0, 0, 0))
        time.sleep(0.05)                 # 버튼 디바운스 대기
    last_button = current_button

    time.sleep(0.005)