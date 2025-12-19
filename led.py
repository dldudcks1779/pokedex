import time
import RPi.GPIO as GPIO
import config

# LED 초기화
def setup_leds():
    for pin in (config.BATTERY_GREEN_LED_PIN, config.BATTERY_YELLOW_LED_PIN, config.BATTERY_RED_LED_PIN):
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(config.PLAY_LED_PIN, GPIO.OUT, initial=GPIO.LOW)

# 배터리 잔량 LED 설정
def set_battery_led(green=False, yellow=False, red=False):
    GPIO.output(config.BATTERY_GREEN_LED_PIN, GPIO.HIGH if green else GPIO.LOW)
    GPIO.output(config.BATTERY_YELLOW_LED_PIN, GPIO.HIGH if yellow else GPIO.LOW)
    GPIO.output(config.BATTERY_RED_LED_PIN, GPIO.HIGH if red else GPIO.LOW)

# 재생 상태 LED 설정
def set_play_led(play: bool):
    GPIO.output(config.PLAY_LED_PIN, GPIO.HIGH if play else GPIO.LOW)

# 재생 상태 LED 토글
def toggle_play_led():
    GPIO.output(config.PLAY_LED_PIN, not GPIO.input(config.PLAY_LED_PIN))

# 재생 상태 LED 깜빡임 업데이트
def update_play_led_blink(last_time, blink_interval=0.1):
    now = time.time()
    if (now - last_time) >= blink_interval:
        toggle_play_led()
        return now
    return last_time

# LED 정리
def cleanup_leds():
    set_battery_led(False, False, False)
    set_play_led(False)