import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List, TypedDict, Mapping, cast

OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3:1b"


SYSTEM_PROMPT = (
    "Du bist ein freundlicher Quizmaster für ein Konsolenspiel. "
    "Stelle eine einzige Frage aus einer zufälligen Kategorie (Allgemeinwissen, Film, Tech, Sport). "
    "Gib die Antwort separat im JSON-Feld 'answer' als kurzer String an. "
    "Antwortformat: JSON mit Schlüsseln 'question' und 'answer' ohne zusätzliche Erklärungen."
)


def ensure_ollama_up(verbose: bool = False) -> bool:
    try:
        # Use the /api/tags endpoint to check if server is up
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as resp:
            if resp.status == 200:
                if verbose:
                    print("Ollama server erreichbar.")
                return True
    except Exception as e:
        if verbose:
            print("Ollama scheint nicht zu laufen auf http://localhost:11434", e)
    return False


class QuizQA(TypedDict):
    question: str
    answer: str


def _chat(messages: List[Dict[str, str]]) -> str:
    data = json.dumps({
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(OLLAMA_API_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload: Dict[str, Any] = json.loads(resp.read().decode("utf-8"))
            # Ollama chat format: { message: { role, content }, ... }
            msg: Dict[str, Any] = payload.get("message", {}) or {}
            content: str = str(msg.get("content", ""))
            return content
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Ollama HTTPError: {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Ollama URLError: {e.reason}") from e


def get_quiz_question() -> Optional[QuizQA]:
    content = _chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Bitte eine Frage generieren."}
    ])
    try:
        # Attempt to parse JSON from the model content
        raw: Any = json.loads(content)
    except Exception:
        return None

    parsed: Dict[str, Any]
    if isinstance(raw, dict):
        # Treat as Mapping[str, Any] for type checker
        raw_map: Mapping[str, Any] = cast(Mapping[str, Any], raw)
        parsed = {k: raw_map[k] for k in raw_map.keys()}
        q: Any = parsed.get("question")
        a: Any = parsed.get("answer")
        if isinstance(q, str) and isinstance(a, str):
            return {"question": q, "answer": a}
    return None


def run_ollama_quiz() -> None:
    print("KI-Quiz (gemma3:1b via Ollama)")
    if not ensure_ollama_up(verbose=True):
        print("Hinweis: Installiere und starte Ollama, und lade das Modell 'gemma3:1b'.")
        print("Siehe README für Schritte.")
        return

    qa: Optional[QuizQA] = get_quiz_question()
    if not qa:
        print("Konnte keine gültige Frage generieren. Probiere es später erneut.")
        return

    question: str = qa.get("question", "?")
    answer: str = qa.get("answer", "")

    print("Frage:")
    print(question)
    user = input("Deine Antwort: ").strip()

    # Simple check (case-insensitive, trimmed)
    if user.lower() == answer.strip().lower():
        print("Richtig! 🎉")
    else:
        print(f"Nicht ganz. Richtige Antwort: {answer}")
