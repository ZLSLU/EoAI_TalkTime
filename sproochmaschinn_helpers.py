"""Reusable helper functions for the Sproochmaschinn workshop."""
from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


DEFAULT_TIMEOUT = 30


def create_session(base_url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    response = requests.post(f"{base_url}/api/session", timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data["session_id"]


def submit_tts(
    base_url: str,
    session_id: str,
    text: str,
    model: str = "claude",
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    response = requests.post(
        f"{base_url}/api/tts/{session_id}",
        json={"text": text, "model": model},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data["request_id"]


def submit_stt(
    base_url: str,
    session_id: str,
    audio_path: str | Path,
    enable_speaker_identification: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    audio_path = Path(audio_path)
    with audio_path.open("rb") as f:
        response = requests.post(
            f"{base_url}/api/stt/{session_id}",
            files={"audio": f},
            data={
                "enable_speaker_identification": str(enable_speaker_identification).lower()
            },
            timeout=timeout,
        )
    response.raise_for_status()
    data = response.json()
    return data["request_id"]


def get_result(
    base_url: str,
    request_id: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    response = requests.get(f"{base_url}/api/result/{request_id}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def poll_result(
    base_url: str,
    request_id: str,
    sleep_seconds: float = 1.0,
    max_polls: int = 120,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    for _ in range(max_polls):
        result = get_result(base_url, request_id, timeout=timeout)
        status = result.get("status")
        if status == "completed":
            return result
        if status == "failed":
            raise RuntimeError(f"Request failed: {result}")
        time.sleep(sleep_seconds)
    raise TimeoutError(f"Request {request_id} did not complete in time.")


def export_result(
    base_url: str,
    request_id: str,
    export_type: str = "timestamps",
    params: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    response = requests.get(
        f"{base_url}/api/result/{request_id}/export/{export_type}",
        params=params or {},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def decode_base64_wav_to_file(data_b64: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    audio_bytes = base64.b64decode(data_b64)
    output_path.write_bytes(audio_bytes)
    return output_path
