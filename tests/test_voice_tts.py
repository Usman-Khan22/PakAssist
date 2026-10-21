import io
import threading
import wave
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from google.genai import errors, types

import backend.api.app as api


def response_for(data, mime):
    return types.GenerateContentResponse(candidates=[types.Candidate(
        content=types.Content(parts=[types.Part(
            inline_data=types.Blob(data=data, mime_type=mime),
        )]),
    )])


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-secret')
    monkeypatch.delenv('TTS_MODEL', raising=False)
    monkeypatch.delenv('TTS_VOICE', raising=False)
    factory = MagicMock()
    factory.return_value.__enter__.return_value.models.generate_content.return_value = response_for(
        b'\x00\x00' * 240, 'audio/L16;codec=pcm;rate=24000',
    )
    monkeypatch.setattr(api.genai, 'Client', factory)
    return factory


@pytest.mark.parametrize('text', ['Hello, welcome to PakAssist.', 'Assalam o alaikum, aap ka CNIC tayyar hai.'])
def test_tts_pcm_is_playable_wav(provider, text):
    response = TestClient(api.app).post('/voice/tts', json={'text': ' ' + text + ' '})
    assert response.status_code == 200
    assert response.headers['content-type'] == 'audio/wav'
    assert response.headers['cache-control'] == 'no-store'
    with wave.open(io.BytesIO(response.content), 'rb') as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, 24000)
        assert audio.getnframes() == 240
    call = provider.return_value.__enter__.return_value.models.generate_content.call_args.kwargs
    assert call['contents'] == text
    assert call['model'] == 'gemini-3.8-flash-lite-tts'
    assert call['config'].speech_config.voice_config.prebuilt_voice_config.voice_name == 'Iapetus'
    options = provider.call_args.kwargs['http_options']
    assert options.timeout == 60000
    assert options.retry_options.attempts == 2
    assert options.retry_options.http_status_codes == [429, 503]


def test_native_wav_preserved(provider):
    wav = api._tts_wav(response_for(b'\x00\x00' * 24, 'audio/L16;rate=24000'))
    provider.return_value.__enter__.return_value.models.generate_content.return_value = response_for(wav, 'audio/wav')
    response = TestClient(api.app).post('/voice/tts', json={'text': 'Hello'})
    assert response.content == wav


@pytest.mark.parametrize('text', ['', '   ', 'x' * 5001])
def test_invalid_text(provider, text):
    assert TestClient(api.app).post('/voice/tts', json={'text': text}).status_code == 400
    provider.assert_not_called()


def test_missing_key(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    assert TestClient(api.app).post('/voice/tts', json={'text': 'Hello'}).status_code == 503


@pytest.mark.parametrize('code,expected', [(400, 502), (403, 502), (404, 502), (429, 503), (500, 502), (503, 503)])
def test_provider_error_is_sanitized(provider, code, expected):
    provider.return_value.__enter__.return_value.models.generate_content.side_effect = errors.APIError(code, {'error': {'message': 'private provider details'}})
    response = TestClient(api.app).post('/voice/tts', json={'text': 'Hello'})
    assert response.status_code == expected
    assert 'private' not in response.text


@pytest.mark.parametrize('result', [
    types.GenerateContentResponse(),
    response_for(b'', 'audio/wav'),
    response_for(b'not a wav', 'audio/wav'),
    response_for(b'odd', 'audio/L16'),
    response_for(b'xx', 'audio/L16;rate=0'),
    response_for(b'xx', 'audio/mpeg'),
])
def test_invalid_provider_audio(provider, result):
    provider.return_value.__enter__.return_value.models.generate_content.return_value = result
    assert TestClient(api.app).post('/voice/tts', json={'text': 'Hello'}).status_code == 502


def test_network_failure(provider):
    provider.return_value.__enter__.return_value.models.generate_content.side_effect = TimeoutError('secret')
    assert TestClient(api.app).post('/voice/tts', json={'text': 'Hello'}).status_code == 502


@pytest.mark.anyio
async def test_sync_generation_runs_off_event_loop(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test')
    loop_thread = threading.get_ident()
    def generate(*args):
        assert threading.get_ident() != loop_thread
        return b'audio'
    monkeypatch.setattr(api, '_generate_speech', generate)
    assert (await api.voice_tts(api.TTSRequest(text='Hello'))).status_code == 200


@pytest.fixture
def anyio_backend():
    return 'asyncio'
