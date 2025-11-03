import time
import cv2
import RPi.GPIO as GPIO
import config
import camera
import battery
import audio_player
from tflite_model import TFLiteModel

# 전역 변수 초기화
button_pressed = False         # 버튼 눌림 상태
last_play_led_blink_time = 0.0 # 재생 상태 LED 깜빡임 마지막 시간
last_battery_check_time = 0.0  # 배터리 잔량 마지막 측정 시간
playing = False                # 오디오 재생 상태
paused = False                 # 오디오 일시정지 상태
last_audio_process = None      # 마지막 오디오 재생 프로세스
last_playback_end_time = 0.0   # 마지막 오디오 재생 종료 시간
last_cropped_frame = None      # 마지막 크롭된 프레임 (TFLite 모델 추론)
last_display_frame = None      # 마지막 디스플레이 프레임 (화면 출력)

# 버튼 눌림 감지 버튼 콜백 함수
def on_button_press(_):
    global button_pressed
    button_pressed = True

# GPIO 초기화 및 설정
def init_gpio():
    GPIO.setmode(GPIO.BCM)
    for pin in (config.BATTERY_GREEN_LED_PIN, config.BATTERY_YELLOW_LED_PIN, config.BATTERY_RED_LED_PIN):
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(config.PLAY_LED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(config.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(config.BUTTON_PIN, GPIO.FALLING, callback=on_button_press, bouncetime=200)

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

# 모든 LED 끄기
def cleanup_led():
    set_battery_led(False, False, False)
    set_play_led(False)

# 리소스(카메라, OpenCV, I2C, GPIO 등) 해제 및 정리
def cleanup_resources(cap, smbus):
    try:
        if cap:
            cap.release()
        cv2.destroyAllWindows()
    except Exception as exception:
        print(f"ERROR: 카메라 및 OpenCV 리소스 해제 실패 - {exception}")
    try:
        if smbus:
            smbus.close()
    except Exception as exception:
        print(f"ERROR: I2C SMBus 연결 종료 실패 - {exception}")
    try:
        cleanup_led()
        GPIO.cleanup()
    except Exception as exception:
        print(f"ERROR: LED 및 GPIO 리소스 정리 실패 - {exception}")
    
# 배터리 잔량 측정 핸들러
def handle_battery(smbus):
    global last_battery_check_time
    now = time.time()
    if (now - last_battery_check_time) < config.BATTERY_CHECK_INTERVAL_SECONDS:
        return
    last_battery_check_time = now
    soc = battery.get_battery_soc(smbus)
    print(f"배터리 잔량: {soc}%")
    if soc > config.BATTERY_THRESHOLD_HIGH:
        set_battery_led(green=True)
    elif soc > config.BATTERY_THRESHOLD_LOW:
        set_battery_led(yellow=True)
    else:
        set_battery_led(red=True)

# 오디오 핸들러
def handle_audio():
    global playing, paused, last_audio_process, last_playback_end_time
    if not playing:
        return
    if last_audio_process and last_audio_process.poll() is not None:
        playing = False
        paused = False
        set_play_led(False)
        last_audio_process = None
        last_playback_end_time = time.time()

# TFLite 모델 추론
def inference(model: TFLiteModel, frame):
    label, probability = model.run_inference(frame)
    return label, probability

# 오디오 재생
def play_audio(label: str):
    global playing, last_audio_process
    mp3_file_path = audio_player.find_mp3_file(label)
    popen = audio_player.play_mp3_file(mp3_file_path)
    if popen:
        playing = True
        last_audio_process = popen

# 버튼 핸들러
def handle_button(model: TFLiteModel):
    global button_pressed, playing, paused, last_cropped_frame
    if not button_pressed:
        return
    button_pressed = False
    if playing or last_cropped_frame is None:
        return
    label, probability = model.run_inference(last_cropped_frame)
    print(f"추론 결과: {label} (정확도: {probability:.2f})")
    play_audio(label)
    paused = True

if __name__ == "__main__":
    init_gpio()
    cap = camera.create_video_capture()
    camera.setup_fullscreen_window(config.WINDOW_NAME)
    smbus = battery.init_smbus()
    model = TFLiteModel(config.LABELS_PATH, config.MODEL_PATH)
    try:
        while True:
            handle_battery(smbus)
            handle_audio()
            if playing:
                last_play_led_blink_time = update_play_led_blink(last_play_led_blink_time)
            elif GPIO.input(config.PLAY_LED_PIN) == GPIO.HIGH:
                set_play_led(False)
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    print("프레임 읽기 실패")
                    break
                display_frame = cv2.resize(frame, (480, 360), interpolation=cv2.INTER_LINEAR)
                height, width = display_frame.shape[:2]
                crop_size = min(height, width)
                x1 = (width - crop_size) // 2
                y1 = (height - crop_size) // 2
                cropped_image = display_frame[y1:y1+crop_size, x1:x1+crop_size]
                last_cropped_frame = cv2.resize(cropped_image, (config.INPUT_WIDTH, config.INPUT_WIDTH), interpolation=cv2.INTER_LINEAR)
                last_display_frame = display_frame
            if last_display_frame is not None:
                cv2.imshow(config.WINDOW_NAME, last_display_frame)
            handle_button(model)
            if cv2.waitKey(1) == 27:
                break
    except Exception as exception:
        print(f"{exception}")
    finally:
        print("프로그램 종료")
        cleanup_resources(cap, smbus)