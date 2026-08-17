import board
import digitalio
import rotaryio
import neopixel
import time

NUM_LEDS = 8
pixels = neopixel.NeoPixel(board.GP15, NUM_LEDS, auto_write=False)

# 로터리 엔코더 (KY-040) 핀 설정
encoder = rotaryio.IncrementalEncoder(board.GP12, board.GP11)
sw = digitalio.DigitalInOut(board.GP10)
sw.direction = digitalio.Direction.INPUT
sw.pull = digitalio.Pull.UP

# 색상 테마 팔레트 (RGB 튜플)
PALETTES = [
    (255, 105, 180), # 파스텔 핑크
    (64, 224, 208),  # 터콰이즈 민트
    (255, 182, 193), # 벚꽃 연분홍
    (255, 215, 0),   # 웜 골드
    (138, 43, 226)   # 딥 바이올렛
]

color_idx = 0
brightness = 5  # 1 ~ 10 단계
last_position = encoder.position
last_sw_time = 0

def render_light():
    r, g, b = PALETTES[color_idx]
    factor = brightness / 10.0
    pixels.fill((int(r * factor), int(g * factor), int(b * factor)))
    pixels.show()

# 최초 켜기
render_light()

while True:
    # 1. 엔코더 돌려서 밝기 조절
    current_position = encoder.position
    if current_position != last_position:
        diff = current_position - last_position
        brightness = max(1, min(10, brightness + diff))
        render_light()
        last_position = current_position

    # 2. 엔코더 버튼 누르면 색상 테마 변경
    now = time.monotonic()
    if not sw.value:
        if now - last_sw_time > 0.3: # 버튼 중복 입력 방지 (300ms)
            color_idx = (color_idx + 1) % len(PALETTES)
            render_light()
            last_sw_time = now

    time.sleep(0.001)