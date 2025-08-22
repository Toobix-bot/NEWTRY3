import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Mapping, Optional, cast

from .schemas import AvaTurn

OLLAMA_API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma3:1b"


def ensure_ollama_up(verbose: bool = False) -> bool:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as resp:
            if resp.status == 200:
                if verbose:
                    print("Ollama server erreichbar.")
                return True
    except Exception as e:
        if verbose:
            print("Ollama scheint nicht zu laufen auf http://localhost:11434", e)
    return False


def chat(messages: List[Dict[str, str]], model: str = DEFAULT_MODEL, stream: bool = False, timeout: int = 60) -> str:
    data = json.dumps({
        "model": model,
        "messages": messages,
        "stream": stream
    }).encode("utf-8")

    req = urllib.request.Request(OLLAMA_API_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload: Dict[str, Any] = json.loads(resp.read().decode("utf-8"))
            msg: Mapping[str, Any] = payload.get("message", {}) or {}
            content = str(msg.get("content", ""))
            return content
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Ollama HTTPError: {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Ollama URLError: {e.reason}") from e


def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Extract first top-level JSON object from text, if present."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end+1]
        try:
            raw = json.loads(snippet)
            if isinstance(raw, dict):
                return cast(Dict[str, Any], raw)
        except Exception:
            return None
    return None


def parse_ava_turn(text: str) -> Optional[AvaTurn]:
    """Parse and validate an Ava turn from model output; returns None if invalid."""
    raw = extract_json_block(text)
    if not raw:
        return None
    try:
        return AvaTurn.model_validate(raw)
    except Exception:
        return None
