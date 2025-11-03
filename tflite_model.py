import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import config

# TensorFlow Lite 모델(.tflite)을 로드하고 이미지 분류 추론의 모든 과정을 캡슐화하여 관리하는 에이전트 클래스
class TFLiteModel:
    # 생성자: 레이블 파일(.txt) 경로와 모델 파일(.tflite) 경로를 입력받아 초기화
    def __init__(self, labels_path, model_path):
        try:
            self.labels = self.load_labels(labels_path)
            self.interpreter = tflite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            input_details = self.interpreter.get_input_details()[0]
            output_details = self.interpreter.get_output_details()[0]
            self.input_index = input_details["index"]
            self.output_index = output_details["index"]
            self.input_shape = (config.INPUT_WIDTH, config.INPUT_HEIGHT)
        except Exception as exception:
            raise RuntimeError(f"ERROR: TFLite 모델 초기화 실패 - {exception}") from exception

    # 레이블 파일(.txt)에서 레이블 목록 로드
    def load_labels(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.split(maxsplit=1)[-1].strip() for line in file if line.strip()]

    # 이미지 전처리 (이미지 크기 조정, 색상 공간 변환, 정규화, 배치 차원 추가)
    def preprocess(self, bgr_image):
        roi = cv2.resize(bgr_image, self.input_shape, interpolation=cv2.INTER_LINEAR)
        rgb_image = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB).astype(np.float32) 
        rgb_image /= 255.0
        input_tensor = np.expand_dims(rgb_image, axis=0)
        return input_tensor

    # Softmax 함수
    def softmax(self, x):
        e = np.exp(x - np.max(x))
        return e / np.sum(e)

    # 추론 실행
    def run_inference(self, bgr_image):
        input_tensor = self.preprocess(bgr_image)
        self.interpreter.set_tensor(self.input_index, input_tensor)
        self.interpreter.invoke()
        raw_output = self.interpreter.get_tensor(self.output_index)[0].astype(np.float32)
        probabilities = self.softmax(raw_output)
        top_index = np.argmax(probabilities)
        probability = float(probabilities[top_index])
        label = self.labels[top_index]
        return label, probability
