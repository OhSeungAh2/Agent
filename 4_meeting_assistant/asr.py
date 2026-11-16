import os
import numpy as np
import torch

# 관련 정보를 하나의 객체로 묶어 관리하기 위해 사용~
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
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

_model = None


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

# 오디오 파일의 RMS(Root Mean Square) 계산 함수
def compute_rms(wav: np.ndarray) -> float:
    if wav.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(wav ** 2)))

# Peak Normalization 함수: 음성 신호의 최대 진폭을 기준으로 전체 신호의 크기를 조절하여 일정한 음량으로 맞추는 함수
def peak_normalize(wav: np.ndarray, target: float=0.9) -> np.ndarray:
    peak = float(np.max(np.abs(wav))) if wav.size else 0.0
    if 1e-6 <= peak < target:
        return (wav * (target / peak)).astype(np.float32)
    return wav.astype(np.float32)

# 오디오 파일의 RMS와 Peak를 측정하고, 무음 여부 판단 및 정규화 후 AudioFeatures 객체로 반환하는 함수
def preprocess_audio_file(path: str | Path) -> AudioFeatures:
    wav, sr = load_audio_file(path)
    # RMS: 음성 신호의 평균적인 크기를 측정
    # Peak: 음성 신호에서 가장 큰 진폭을 측정(절댓값이 가장 큰 값)
    # Peak Normalization: 가장 큰 진폭을 기준으로 음성 전체의 크기를 조절
    # 음성 정규화를 하는 이유: 같은 사람이 같은 문장을 녹음하더라도 녹음 환경에 따라 음성 신호의 크기가 달라지기 때문(일정한 음량으로 맞추기 위해)
    rms = compute_rms(wav)
    # RMS가 SILENCE_RMS보다 작으면 무음으로 간주하고 정규화를 건너뛰도록 설정
    peak = float(np.max(np.abs(wav))) if wav.size else 0.0
    skipped = rms < SILENCE_RMS 
    # 무음이 아닌 경우에만 Peak Normalization 수행
    if not skipped:
        wav = peak_normalize(wav)
        peak = float(np.max(np.abs(wav))) if wav.size else 0.0
        rms = compute_rms(wav)
    # 전처리된 음성 데이터, 샘플링 레이트, RMS, Peak, 무음 여부, 파일 경로를 저장하는 객체
    return AudioFeatures(
        wav=wav,
        sample_rate=sr,
        rms=rms,
        peak=peak,
        skipped_silence=skipped,
        path=str(path)
    )

# Qwen ASR 모델을 가져오는 내부 함수
def _get_qwen_model():
    global _model
    if _model is not None:
        return _model
    if not torch.cuda.is_available():
        raise RuntimeError("GPU 필요해!!")
    # 해석: ASR_DTYPE 환경 변수가 "float16"이면 torch.float16을 사용하고, 그렇지 않으면 torch.bfloat16을 사용
    dtype = (torch.float16 if os.getenv("ASR_DTYPE", "bfloat16").lower() == "float16" else torch.bfloat16)
    _model = Qwen3ASRModel.from_pretrained(
        ASR_MODEL_PATH, dtype=dtype, device_map="cuda:0", max_inference_batch_size=1, max_new_tokens=256
    )
    return _model

#  무음 여부와 ASR 모드에 따라 음성을 텍스트로 변환하고 TranscriptResult 객체로 반환하는 함수
def transcribe_features(features: AudioFeatures, mode: str | None = None) -> TranscriptResult:
    # ASR 모드 결정 (mode가 지정되지 않았다면 resolve_asr_mode() 호출)
    mode = mode or resolve_asr_mode()
    # 무음으로 판단된 경우 ASR을 실행하지 않고 빈 텍스트 반환
    if features.skipped_silence:
        return TranscriptResult(
            text="",
            mode=mode,
            rms=features.rms,
            peak=features.peak,
            skipped_silence=True,
            detail=f"무음으로 건너뜀 (RMS={features.rms:.4f} < {SILENCE_RMS})"
        )
    # Qwen 모드인 경우 실제 ASR 모델로 음성을 텍스트로 변환
    if mode == "qwen":
        # _get_qwen_model(): Qwen-ASR 모델 가져오기
        model = _get_qwen_model()
        # transcribe(): 음성 데이터와 샘플링 레이트를 전달해 음성 인식 수행
        result = model.transcribe(audio=(features.wav, features.sample_rate), language=ASR_LANGUAGE)
        # 인식 결과에서 텍스트 추출 및 앞뒤 공백 제거
        text = (getattr(result[0], "text", "") or "").strip()
        # 실제 음성 인식 결과 반환
        return TranscriptResult(
            text=text,
            mode="qwen",
            rms=features.rms,
            peak=features.peak,
            skipped_silence=False,
            detail=f"Qwen-ASR 실전사"
        )
    # Qwen 모드가 아닌 경우 Mock 텍스트 반환 (실제 음성 인식 수행하지 않음)
    return TranscriptResult(
        text=MOCK_TRANSCRIPT,
        mode="mock",
        rms=features.rms,
        peak=features.peak,
        skipped_silence=False,
        detail=f"Mock 전사"
    )

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
    return transcribe_features(features)