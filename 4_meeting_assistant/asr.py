import os
import numpy as np
# 관련 정보를 하나의 객체로 묶어 관리하기 위해 사용~
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import torch
from qwen_asr import Qwen3ASRModel
from pathlib import Path


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


# 오디오 파일을 불러와 모노 변환 및 리샘플링 후 오디오 데이터와 샘플링 레이트를 반환하는 함수
def load_audio_file(path: str | Path) -> tuple[np.ndarray, int]:
    path = Path(path)
    # 파일 존재 여부 확인
    if not path.is_file():
        raise FileNotFoundError(f"음성 파일 없음: {path}")
    # soundfile 모듈 불러오기
    try:
        import soundfile as sf
    except ImportError as e:
        raise ImportError("soundfile 모듈 에러!") from e
    # 오디오 파일 읽기 (채널 수와 관계없이 2차원 배열로 반환 -> 우선은 무조건 스테레오로 받아오는거임)
    # wav: 압축하지않은 음성 원본 데이터, sr: 샘플링 레이트
    """
        예시: 5초짜리 음성 데이터가 들어가있는데 44100hz라면
        wav파일의 shape는? 
        
        -> 5초 * 44100hz = 220500
        -> 이게 채널당 샘플 수임(스테레오라면 shape는 (220500, 2)임)

    """
    # always_2d=True : 모노와 스테레오 관계없이 항상 스테레오(2차원 배열)로 반환해라!!
    wav, sr = sf.read(str(path), dtype="float32", always_2d=True)
    # 채널별 평균을 구해 모노(1채널)로 변환
    wav = wav.mean(axis=1)
    # 샘플링 레이트가 TARGET_SR(16000)과 다르면 리샘플링
    if sr != TARGET_SR:
        # len(wav): 음성 샘플 수이고 이걸 sr로 나누는거임(sr은 원본 샘플링 레이트임 = 녹음본에 따라 달라짐)
        # 그럼 결국 duration = 음성 길이가 되는것임
        duration = len(wav) / sr
        # 목표 샘플링 레이트에 맞는 샘플 수 계산
        new_len = max(1, int(round(duration * TARGET_SR)))
        # 1차원 선형 보간을 이용해 리샘플링
        # 1차원 선형 보간: 기존 샘플을 기준으로 새로운 샘플 위치에 맞춰 값을 보간하여 리샘플링 수행
        # linspace: 1차원 선형 보간| 기존에 측정한 샘플 사이의 값을 직선으로 연결해 새로운 위치 값을 추정
        """
            시간 0초의 음성 진폭: 0.2
            시간 1초의 음성 진폭: 0.8
            그렇다면 0.5초 지점의 진폭은 얼마일까?
            -> 0.5초는 0초와 1초의 중간이므로, y = 0.2 + (0.8 - 0.2) * 0.5 = 0.5임!
        """
        wav = np.interp(
            # np.linspace(0, duration, new_len, endpoint=False): 이게 첫번째 = 새로운 샘플 위치 배열
                # linspace: 지정한 구간에 일정한 간격으로 숫자 생성
                # linspace(0, 1, 4)라면~ > [0, 0.25, 0.5, 0.75]가 만들어질거임
                # endpoint=False: 마지막 값 넣지 말라는거임 (1 넣지 마라는 뜻..?)
                # 결론은 기존 시간과 진폭을 참고해 새로운 시간 좌표에서 진폭을 계산하라는거~
            # np.arange(len(wav)) / sr: 기존 샘플 위치 배열
            # wav: 기존 샘플 값 배열
            np.linspace(0, duration, new_len, endpoint=False), np.arange(len(wav)) / sr,wav
        ).astype(np.float32)
        # 샘플링 레이트를 목표값으로 갱신
        sr = TARGET_SR
    if MAX_SECONDS > 0:
        wav = wav[: int(MAX_SECONDS * TARGET_SR)]
    return wav.astype(np.float32), sr


def preprocess_audio_file(path: str | Path) -> AudioFeatures:
    wav, sr = load_audio_file(path)

# ASR 모드 결정 함수
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

# ASR 상태 확인 함수
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

def transcribe_file(path: str | Path) -> TranscriptResult:
    features = preprocess_audio_file(path)