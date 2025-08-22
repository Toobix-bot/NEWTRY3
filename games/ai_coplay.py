from typing import Dict, Any, List, Tuple
from .llm_client import chat, ensure_ollama_up, extract_json_block

SYSTEM = (
    "Du bist 'Ava', eine KI-Figur in einer gemeinsamen Life-Simulation mit einem Menschen (Ben). "
    "Jede Runde handeln sowohl Ava als auch Ben in der Welt. Du antwortest NUR als JSON mit: "
    "thoughts (kurz), action (move_up/move_down/move_left/move_right/wait/interact/speak:<text>), "
    "speech (was Ava sagt), design_feedback (konkrete Verbesserungen), self_update (Identitätsanpassung)."
)

GRID: Tuple[int, int] = (7, 5)


def clamp_pos(pos: Tuple[int, int]) -> Tuple[int, int]:
    x, y = pos
    x = max(0, min(GRID[0] - 1, x))
    y = max(0, min(GRID[1] - 1, y))
    return x, y


def apply_action(state: Dict[str, Any], who: str, action: str) -> str:
    key = "ava" if who == "ava" else "ben"
    x, y = state["pos"][key]
    a = action.lower()
    if a == "move_up":
        y -= 1
    elif a == "move_down":
        y += 1
    elif a == "move_left":
        x -= 1
    elif a == "move_right":
        x += 1
    elif a.startswith("speak:"):
        # speaking has no position change, but we can log it
        msg = a.split(":", 1)[1].strip()
        return f"{who} spricht: {msg}"
    # wait or interact don't move by default
    state["pos"][key] = clamp_pos((x, y))
    return f"{who} {a} -> {state['pos'][key]}"


def render(state: Dict[str, Any]) -> None:
    print(f"Karte {GRID[0]}x{GRID[1]}")
    print(f"Ava@{state['pos']['ava']}  Ben@{state['pos']['ben']}")
    if state.get("log"):
        print("Log:", state["log"][-1])


def normalize_human_action(raw: str) -> str:
    r = raw.strip().lower()
    mapping = {
        "w": "move_up", "a": "move_left", "s": "move_down", "d": "move_right",
        "oben": "move_up", "links": "move_left", "unten": "move_down", "rechts": "move_right",
        "warte": "wait", "warten": "wait", "interagiere": "interact"
    }
    if r in mapping:
        return mapping[r]
    if r.startswith("speak ") or r.startswith("sage "):
        return "speak:" + raw.split(" ", 1)[1]
    return r or "wait"


def run_coplay(max_turns: int = 20) -> None:
    if not ensure_ollama_up(verbose=True):
        print("Bitte starte Ollama und lade 'gemma3:1b'.")
        return

    state: Dict[str, Any] = {
        "pos": {"ava": (GRID[0] // 2, GRID[1] // 2), "ben": (0, 0)},
        "log": [],
        "notes": "",
    }

    print("Co-Play: Ava (KI) & Ben (Mensch) handeln abwechselnd pro Runde. Eingaben: w/a/s/d oder 'speak Hallo' etc.")

    history: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Start: Ava@{state['pos']['ava']}, Ben@{state['pos']['ben']} auf {GRID}."}
    ]

    for turn in range(1, max_turns + 1):
        print(f"\n=== Runde {turn} ===")
        render(state)

        # 1) Human (Ben) acts + can give feedback
        raw = input("Ben Aktion (w/a/s/d, speak <text>, oder Enter=wait) | q zum Beenden: ").strip()
        if raw.lower() in ("q", "quit", "exit"):
            print("Session beendet.")
            break
        human_feedback = input("Optionales Feedback/Ideen an das System (Enter überspringt): ").strip()
        action_ben = normalize_human_action(raw)
        world_ben = apply_action(state, "ben", action_ben)
        print("Welt (Ben):", world_ben)

        # 2) AI (Ava) acts
        prompt_ai = (
            f"Zustand: Ava@{state['pos']['ava']}, Ben@{state['pos']['ben']}. "
            f"Ben-Aktion: {action_ben}. Weltreaktion: {world_ben}."
        )
        if human_feedback:
            prompt_ai += f" Benutzer-Feedback: {human_feedback}."
        history.append({"role": "user", "content": prompt_ai})

        try:
            content = chat(history)
        except Exception as e:
            print("KI-Fehler:", e)
            print("Tipp: Stelle sicher, dass 'gemma3:1b' verfügbar ist.")
            break

        data = extract_json_block(content)
        if not data:
            print("KI-Antwort kein valides JSON. Runde übersprungen.")
            history.append({"role": "assistant", "content": content})
            history.append({"role": "user", "content": "Bitte striktes JSON liefern."})
            continue

        thoughts = str(data.get("thoughts", ""))
        action_ava = str(data.get("action", "wait"))
        speech = str(data.get("speech", ""))
        design_feedback = str(data.get("design_feedback", ""))
        self_update = str(data.get("self_update", ""))

        print("Ava denkt:", thoughts)
        if speech:
            print("Ava sagt:", speech)
        world_ava = apply_action(state, "ava", action_ava)
        print("Welt (Ava):", world_ava)
        if design_feedback:
            print("Ava-Feedback:", design_feedback)
        if self_update:
            state["notes"] = (state.get("notes", "") + " | " + self_update).strip(" |")

        # Mutual influence log
        state["log"].append({
            "turn": turn,
            "ben_action": action_ben,
            "ava_action": action_ava,
            "human_feedback": human_feedback,
            "ava_feedback": design_feedback,
        })

        # Feed back to model
        fb = (
            f"Weltreaktionen – Ben: {world_ben}; Ava: {world_ava}. "
            f"Neuer Zustand: Ava@{state['pos']['ava']}, Ben@{state['pos']['ben']}."
        )
        history.append({"role": "assistant", "content": content})
        history.append({"role": "user", "content": fb})
