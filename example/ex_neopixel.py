import board
import neopixel
import time

pixels = neopixel.NeoPixel(board.GP15, 8, brightness=0.2, auto_write=True)

print("네오픽셀 출력 테스트 시작!")

# 네온 핑크로 1초간 점등
pixels.fill((255, 0, 127))
time.sleep(1.0)

# 꺼지기
pixels.fill((0, 0, 0))
print("네오픽셀 테스트 완료!")
