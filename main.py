import cv2
import time
import RPi.GPIO as GPIO
import config
import camera
import led
import button
import battery
import audio_player
from tflite_model import TFLiteModel

# 전역 변수 초기화
last_play_led_blink_time = 0.0 # 재생 상태 LED 깜빡임 마지막 시간
last_battery_check_time = 0.0  # 배터리 잔량 마지막 측정 시간
playing = False                # 오디오 재생 상태
paused = False                 # 오디오 일시정지 상태
last_audio_process = None      # 마지막 오디오 재생 프로세스
last_playback_end_time = 0.0   # 마지막 오디오 재생 종료 시간
last_cropped_frame = None      # 마지막 크롭된 프레임 (TFLite 모델 추론)
last_display_frame = None      # 마지막 디스플레이 프레임 (화면 출력)

# 모듈 (LED, 버튼) 설정
def setup_modules():
    led.setup_leds()
    button.setup_button()

# 모듈 (LED, 버튼) 정리
def cleanup_modules():
    try:
        led.cleanup_leds()
        button.cleanup_button()
    except Exception as exception:
        print(f"ERROR: 모듈 (LED, 버튼) 정리 실패 - {exception}")

# 리소스 (카메라, I2C, GPIO) 정리
def cleanup_resources(cap=None, smbus=None):
    if cap:
        try:
            cap.release()
        except Exception as exception:
            print(f"ERROR: 카메라 해제 실패 - {exception}")
    cv2.destroyAllWindows()
    if smbus:
        try:
            smbus.close()
        except Exception as exception:
            print(f"ERROR: SMBus 종료 실패 - {exception}")
    try:
        GPIO.cleanup()
    except Exception as exception:
        print(f"ERROR: GPIO 정리 실패 - {exception}")
    
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
        led.set_battery_led(green=True)
    elif soc > config.BATTERY_THRESHOLD_LOW:
        led.set_battery_led(yellow=True)
    else:
        led.set_battery_led(red=True)

# 오디오 핸들러
def handle_audio():
    global playing, paused, last_audio_process, last_playback_end_time
    if not playing:
        return
    if last_audio_process and last_audio_process.poll() is not None:
        playing = False
        paused = False
        led.set_play_led(False)
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
    global playing, paused, last_cropped_frame
    if not button.consume_button_press():
        return
    if playing or last_cropped_frame is None:
        return
    label, probability = model.run_inference(last_cropped_frame)
    print(f"추론 결과: {label} (정확도: {probability:.2f})")
    play_audio(label)
    paused = True

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    setup_modules()
    cap = camera.create_video_capture()
    camera.setup_fullscreen_window(config.WINDOW_NAME)
    smbus = battery.init_smbus()
    model = TFLiteModel(config.LABELS_PATH, config.MODEL_PATH)
    try:
        while True:
            handle_battery(smbus)
            handle_audio()
            if playing:
                last_play_led_blink_time = led.update_play_led_blink(last_play_led_blink_time)
            elif GPIO.input(config.PLAY_LED_PIN) == GPIO.HIGH:
                led.set_play_led(False)
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
        print(exception)
    finally:
        print("프로그램 종료")
        cleanup_modules()
        cleanup_resources(cap, smbus)