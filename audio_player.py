import os
import subprocess
import config

# mp3 파일 경로 조회
def find_mp3_file(label: str):
    file_name = f"{label}.mp3"
    file_path = os.path.join(config.SOUNDS_DIRECTORY, file_name)
    if os.path.isfile(file_path):
        return file_path
    else:
        raise FileNotFoundError(f"ERROR: MP3 파일 조회 실패 (경로: {file_path})")

# MP3 파일을 mpg123를 사용하여 비동기적으로 재생 (Non-blocking 방식으로 실행)
# - mpg123: 오디오 플레이어 및 디코더 라이브러리
def play_mp3_file(file_path: str):
    try:
        popen = subprocess.Popen(["mpg123", "-q", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return popen
    except Exception as exception:
        raise RuntimeError(f"ERROR: MP3 재생 실패 - {exception}") from exception