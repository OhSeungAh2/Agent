import os
import numpy as np
# 관련 정보를 하나의 객체로 묶어 관리하기 위해 사용~
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import torch
from qwen_asr import Qwen3ASRModel


# asr.py가 위치한 폴더의 상위 폴더에서 .env 찾기
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(ENV_PATH)

# 오디오 샘플링 레이트를 16000으로 설정하는 상수
TARGET_SR = 16000

ASR_MODE_ENV = os.getenv("ASR_MODE", "auto").strip().lower()
ASR_MODEL_PATH = os.getenv("ASR_MODEL_PATH", "Qwen/Qwen3-ASR-1.7B")
ASR_LANGUAGE = os.getenv("ASR_LANGUAGE", "Korean")
MAX_SECONDS = float(os.getenv("ASR_MAX_SECONDS", 20))
SILENCE_RMS = float(os.getenv("ASR_SILENCE_RMS", 0.01))

MOCK_TRANSCRIPT = (
    "김사과: 이번 주 목표 공유\n"
    "이메론: API 완료 예정\n"
    "김사과: 문서화는 반하나가 담당\n"
    "반하나: 그럼 김사과가 README 작성해야해"
)


# 오디오 특징을 저장하는 데이터 클래스
@dataclass
class AudioFeatures:
    wav: np.ndarray           # 음성 파일을 > 음성 샘플 배열로 ndarray 변환한 것
    sample_rate: int          # 샘플링 레이트
    rms: float                # Root Mean Square 음성 신호의 전반작인 크기 : 정규화된 음성 샘플 기준으로 비교하기 위해..
    peak: float               # 음성 신호에서 절댓값이 가장 큰 샘플의 크기
    skipped_silence: bool     # 무음 구간이 건너뛰어졌는지 여부 저장(true면 무음 판단)
    path: str                 # 오디오 파일 경로
"""
Root Mean Square (RMS) 
    - 음성 신호의 전반적인 크기를 나타내며
    - 음성의 크고 작음을 비교할 때 사용

Peak
    - 음성 신호에서 절댓값이 가장 큰 샘플의 크기
    - 음성 신호에서 순간적으로 큰 소리가 발생했는지 확인할 때 사용

두가지 차이점 알고있기!!!
RMS는 음성 신호의 전반적인 크기를 나타내며, 평균적인 음량을 파악할 때 유용합니다.
Peak는 음성 신호에서 순간적으로 가장 큰 소리를 나타내며, 순간적인 클리핑이나 큰 소리를 감지할 때 유용합니다.
"""

# 전사 결과를 저장하는 데이터 클래스 > 음성파일에서 뽑아낸 결과론적인 클래스임
@dataclass
class TranscriptResult:
    text: str                  # 인식된 음성 텍스트(전사된 결과)
    mode: str                  # 사용한 인식 방식(전사 모드)
    rms: float                 # 입력 음성의 RMS = 음성 신호의 전반적인 크기
    peak: float                # 입력 음성의 Peak = 음성 신호에서 절댓값이 가장 큰 샘플의 크기
    skipped_silence: bool      # 무음 구간이 건너뛰어졌는지 여부
    detail: str                # 처리 과정에 대한 추가 설명(전사 상세 정보)



def resolve_asr_mode() -> str:
    if ASR_MODE_ENV in {"qwen", "mock"}:
        return ASR_MODE_ENV
    try:
        # 이런식으로 사용하면 메모리 절약 가능: 필요할 때만 모듈을 임포트함
        # 근데 import 하는데 시간 오래걸려서 timeout떠서 위로 올림..
        # import torch
        # from qwen_asr import Qwen3ASRModel

        if torch.cuda.is_available():
            return "qwen"
    except Exception:
        pass
    return "mock"


def asr_status() -> dict:
    mode = resolve_asr_mode()
    cuda = False
    qwen = False
    try:
        import torch
        cuda = bool(torch.cuda.is_available())
    except Exception:
        cuda = False
    try:
        import qwen_asr
        qwen =True
    except Exception:
        qwen = False
    return {
        "mode": mode,
        "requested": ASR_MODE_ENV,
        "cuda": cuda,
        "qwen_asr_installed": qwen,
        "model_path": ASR_MODEL_PATH,
        "silence_rms": SILENCE_RMS,
        "max_seconds": MAX_SECONDS,
        "markdown": (
            f"### ASR 상태\n\n"
            f"- 사용 모드: {mode}\n"
            f"- 요청 모드: {ASR_MODE_ENV}\n"
            f"- CUDA: {cuda}\n"
            f"- qwen_asr: {qwen}\n"
            f"- 모델: {ASR_MODEL_PATH}\n"
            f"- 무음 RMS 임계값: {SILENCE_RMS}\n\n"
        )
    }