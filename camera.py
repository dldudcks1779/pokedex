import cv2
import config

# GStreamer 파이프라인을 사용하여 VideoCapture 객체 생성
def create_video_capture():
    try:
        cap = cv2.VideoCapture(config.GSTREAMER_PIPELINE, cv2.CAP_GSTREAMER)
    except Exception as exception:
        raise RuntimeError(f"ERROR: VideoCapture 객체 생성 실패 - {exception}") from exception
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"ERROR: 카메라 열기 실패")
    return cap

# 전체 화면 창 설정
def setup_fullscreen_window(window_name):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)