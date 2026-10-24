from io import BytesIO
from types import SimpleNamespace
import wave
import pytest
import solem_audio as audio


def wav(seconds=1):
    out = BytesIO()
    with wave.open(out, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(16000)
        f.writeframes(b"\x00\x00" * (16000 * seconds))
    return out.getvalue()


def test_transcription_and_lock_release(monkeypatch):
    class Model:
        def transcribe(self, stream, **kwargs):
            assert isinstance(stream, BytesIO) and kwargs['language'] == 'pt'
            assert kwargs['vad_filter']
            return iter([SimpleNamespace(text=' Biscoito recheado 114 gramas. ')]), None
    monkeypatch.setattr(audio, '_model', lambda: Model())
    assert audio.transcribe_audio(wav()) == 'Biscoito recheado 114 gramas.'
    assert not audio._lock.locked()
    with audio._lock:
        with pytest.raises(ValueError, match='ocupado'): audio.transcribe_audio(wav())


@pytest.mark.parametrize('data', [b'bad', wav(61), wav()[:-20]], ids=['invalid','too_long','truncated'])
def test_rejects_before_loading_model(monkeypatch, data):
    def fail(): raise AssertionError('Invalid audio must not load a model')
    monkeypatch.setattr(audio, '_model', fail)
    with pytest.raises(ValueError): audio.transcribe_audio(data)


def test_silence_and_model_failure_release_lock(monkeypatch):
    monkeypatch.setattr(audio, '_model', lambda: SimpleNamespace(transcribe=lambda *a, **kw: (iter([]),None)))
    with pytest.raises(ValueError, match='fala'): audio.transcribe_audio(wav())
    assert not audio._lock.locked()
    def fail(): raise RuntimeError('model unavailable')
    monkeypatch.setattr(audio, '_model', fail)
    with pytest.raises(RuntimeError): audio.transcribe_audio(wav())
    assert not audio._lock.locked()


def test_recording_deduplicated_reviewable_and_retryable(monkeypatch):
    import solem_voice_ui as ui
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    calls=[]
    monkeypatch.setattr(st, 'audio_input', lambda *a, **kw: BytesIO(wav()))
    def transcribe(data):
        calls.append(data)
        return 'biscoito recheado 114 acumulado'
    monkeypatch.setattr(ui, 'transcribe_audio', transcribe)
    app=AppTest.from_string("""
from solem_voice_ui import voice_input
from solem_meal_analysis import catalog
voice_input('meal','test',foods=catalog())
""").run()
    assert not app.exception and len(calls)==1
    assert app.text_area[0].value == 'biscoito recheado 114 acumulado'
    app.text_area[0].set_value('biscoito recheado 115 acumulado').run()
    assert len(calls)==1 and app.text_area[0].value.endswith('115 acumulado')
    def fail(data): raise ValueError('Falha de teste')
    monkeypatch.setattr(ui, 'transcribe_audio', fail)
    app=AppTest.from_string("""
from solem_voice_ui import voice_input
from solem_meal_analysis import catalog
voice_input('meal','retry',foods=catalog())
""").run()
    assert not app.exception and app.button(key='retry_retry')
    monkeypatch.setattr(ui, 'transcribe_audio', transcribe)
    app.button(key='retry_retry').click().run()
    assert app.text_area[0].value == 'biscoito recheado 114 acumulado'
    assert 'retry_audio_error' not in app.session_state
