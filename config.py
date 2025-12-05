# GStreamer를 이용한 카메라 데이터 처리 파이프라인 정의
GSTREAMER_PIPELINE = (
    "libcamerasrc "                                      # libcamera 라이브러리를 통해 카메라 하드웨어에서 영상 데이터 수집
    "! video/x-raw,width=480,height=360,framerate=30/1 " # 카메라에서 나오는 영상의 속성을 설정: 압축되지 않은 원본(raw) 비디오를 가로 480, 세로 360 픽셀 크기와 초당 30프레임으로 지정
    "! videoconvert ! video/x-raw,format=BGR "           # 영상 데이터의 색상 형식을 변환: OpenCV 라이브러리에서 표준으로 사용하는 색상 순서인 BGR 형식으로 변환
    "! videoscale "                                      # 영상 데이터의 크기를 조절: 다른 요소들 간의 데이터 형식 호환성을 보장하고 파이프라인의 안정성을 높임
    "! appsink drop=1 max-buffers=1 sync=false"          # 처리된 영상을 현재 실행 중인 파이썬 애플리케이션으로 전달: 처리가 늦어질 경우 오래된 프레임을 버리고 가능한 한 가장 최신 프레임을 빠르게 전달하여 실시간 성능을 극대화
)

# 창 이름
WINDOW_NAME = "POKEDEX WINDOW"

# GPIO 핀 번호 (BCM)
BATTERY_GREEN_LED_PIN = 13  # 초록색 LED (배터리 잔량 51% ~ 100%)
BATTERY_YELLOW_LED_PIN = 19 # 노란색 LED (배터리 잔량 16% ~ 50 %)
BATTERY_RED_LED_PIN = 26    # 빨간색 LED (배터리 잔량 0% ~ 15%)
PLAY_LED_PIN = 16           # 재생 상태 LED
BUTTON_PIN = 20             # 버튼

# 배터리 임계값 (%)
BATTERY_THRESHOLD_HIGH = 50.0 # 배터리 잔량 높은 기준
BATTERY_THRESHOLD_LOW = 15.0  # 배터리 잔량 낮은 기준

# I2C 통신 설정 (MAX17043 배터리 잔량 측정 IC)
MAX17043_I2C_ADDRESS = 0x36  # MAX17043 칩의 I2C 장치 주소
MAX17043_SOC_REGISTER = 0x04 # 칩 내부의 배터리 잔량(SOC) 값이 저장된 레지스터 주소

# 배터리 체크 주기 (초)
BATTERY_CHECK_INTERVAL_SECONDS = 5.0

# Teachable Machine TFLite 모델 설정
MODEL_PATH = "pokedex.tflite"         # TFLite 모델 경로
LABELS_PATH = "labels.txt"            # 라벨 파일 경로
INPUT_HEIGHT, INPUT_WIDTH = 224, 224  # 모델 입력 이미지 크기 (높이, 너비)

# 사운드 파일(.mp3) 디렉터리 경로
SOUNDS_DIRECTORY = "./sounds"