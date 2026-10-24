"""Bounded, in-memory transcription on the Solem server; no paid speech API."""
from functools import lru_cache
from io import BytesIO
from threading import Lock
import os
import wave

MAX_SECONDS = 60
MAX_BYTES = 2_000_000
_lock = Lock()


def validate_audio(data):
    if not isinstance(data, bytes) or not 44 <= len(data) <= MAX_BYTES:
        raise ValueError("Grave até 60 segundos e tente novamente.")
    try:
        with wave.open(BytesIO(data), "rb") as audio:
            frames, rate = audio.getnframes(), audio.getframerate()
            if (audio.getnchannels() != 1 or audio.getsampwidth() != 2 or rate != 16000
                    or not 0 < frames / rate <= MAX_SECONDS):
                raise ValueError("Use o gravador abaixo, com até 60 segundos por fala.")
            if len(audio.readframes(frames)) != frames * 2:
                raise ValueError("A gravação ficou incompleta. Grave novamente.")
    except (wave.Error, EOFError) as error:
        raise ValueError("Não foi possível ler o áudio. Grave novamente.") from error


@lru_cache(maxsize=1)
def _model():
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    from faster_whisper import WhisperModel
    return WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=2, num_workers=1)


def transcribe_audio(data):
    validate_audio(data)
    if not _lock.acquire(blocking=False):
        raise ValueError("O transcritor está ocupado. Aguarde um pouco e toque em Tentar transcrever novamente.")
    try:
        segments, _ = _model().transcribe(BytesIO(data), language="pt", beam_size=3,
            vad_filter=True, condition_on_previous_text=False)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        if not text:
            raise ValueError("Não identifiquei fala. Confira o microfone e grave novamente.")
        if len(text) > 2000:
            raise ValueError("A fala ficou longa. Divida em gravações menores.")
        return text
    finally:
        _lock.release()
