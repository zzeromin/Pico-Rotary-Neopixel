import board
import digitalio
import rotaryio
import time

encoder = rotaryio.IncrementalEncoder(board.GP12, board.GP11)
last_position = encoder.position

button = digitalio.DigitalInOut(board.GP10)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP
last_button = button.value

print("엔코더 입력 테스트 시작!")

while True:
    current_position = encoder.position
    if current_position != last_position:
        if current_position > last_position:
            print(f"🔄 오른쪽 회전! ({current_position})")
        else:
            print(f"🔄 왼쪽 회전! ({current_position})")
        last_position = current_position

    current_button = button.value
    if not current_button and last_button:
        print("🔘 버튼 클릭 감지!")
        time.sleep(0.15)
    last_button = current_button

    time.sleep(0.01)
