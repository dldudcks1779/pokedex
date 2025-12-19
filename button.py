import RPi.GPIO as GPIO
import config

# 버튼 눌림 상태 변수 초기화
button_pressed = False

# 버튼 눌림 감지 버튼 콜백 함수
def on_button_press(_):
    global button_pressed
    button_pressed = True

# 버튼 초기화
def setup_button():
    GPIO.setup(config.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(config.BUTTON_PIN, GPIO.FALLING, callback=on_button_press, bouncetime=200)

# 버튼 눌림 확인
def consume_button_press():
    global button_pressed
    if button_pressed:
        button_pressed = False
        return True
    return False

# 버튼 정리
def cleanup_button():
    GPIO.remove_event_detect(config.BUTTON_PIN)