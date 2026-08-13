import board
import digitalio
import rotaryio
import neopixel
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# 1. 하드웨어 설정
keyboard = Keyboard(usb_hid.devices)
encoder = rotaryio.IncrementalEncoder(board.GP12, board.GP11)
last_position = encoder.position

button = digitalio.DigitalInOut(board.GP10)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP
last_button = button.value

pixels = neopixel.NeoPixel(board.GP15, 8, brightness=0.2, auto_write=True)
pixels.fill((0, 0, 0))

# 2. 감성 색상 지정
COLOR_NEXT = (255, 0, 127)   # 👇 다음 영상 (핫핑크)
COLOR_PREV = (0, 255, 255)   # 👆 이전 영상 (사이언)
COLOR_MUTE = (255, 255, 0)   # 🔇 음소거 (노랑)
COLOR_PAUSE = (180, 0, 255)  # ⏯️ 재생/일시정지 (보라)

# 3. 타이머 변수 (쿨다운 및 더블클릭 판별)
SWIPE_COOLDOWN = 0.4          # 스와이프 쿨다운 (0.4초)
last_swipe_time = 0

DOUBLE_CLICK_THRESHOLD = 0.35 # 더블클릭 제한시간 (0.35초)
click_count = 0
last_click_time = 0

def swipe_animation(color):
    """네온 컬러 회전 애니메이션"""
    for i in range(8):
        pixels[i] = color
        time.sleep(0.015)
    time.sleep(0.05)
    pixels.fill((0, 0, 0))

print("📱 숏폼 스와이퍼 준비 완료! 숏폼 화면을 클릭한 후 사용하세요.")

while True:
    current_time = time.monotonic()

    # --- [기능 A] 스와이프 회전 제어 (쿨다운 적용) ---
    current_position = encoder.position
    if current_position != last_position:
        if current_time - last_swipe_time > SWIPE_COOLDOWN:
            if current_position > last_position:
                keyboard.send(Keycode.DOWN_ARROW) # 아래로 스와이프 (다음 영상)
                swipe_animation(COLOR_NEXT)
            else:
                keyboard.send(Keycode.UP_ARROW)   # 위로 스와이프 (이전 영상)
                swipe_animation(COLOR_PREV)
            last_swipe_time = current_time
        last_position = current_position

    # --- [기능 B & C] 버튼 1회(음소거) / 2회(재생/일시정지) 판별 ---
    current_button = button.value
    if not current_button and last_button: # 버튼 누름 순간
        click_count += 1
        last_click_time = current_time
        time.sleep(0.05) # 바운싱 방지
    last_button = current_button

    # 클릭 후 일정 시간(0.35초)이 지났을 때 클릭 횟수 판별
    if click_count > 0 and (current_time - last_click_time > DOUBLE_CLICK_THRESHOLD):
        if click_count == 1:
            # 🔘 [기능 B] 1회 클릭: M 키 (음소거 / 해제)
            keyboard.send(Keycode.M)
            pixels.fill(COLOR_MUTE)
            time.sleep(0.15)
            pixels.fill((0, 0, 0))
        elif click_count >= 2:
            # 🔘🔘 [기능 C] 2회 클릭: Spacebar (재생 / 일시정지)
            keyboard.send(Keycode.SPACE)
            pixels.fill(COLOR_PAUSE)
            time.sleep(0.2)
            pixels.fill((0, 0, 0))
            
        click_count = 0 # 클릭 횟수 리셋

    time.sleep(0.005)
