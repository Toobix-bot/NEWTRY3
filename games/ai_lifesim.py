from typing import Dict, Any, List
from .llm_client import chat, ensure_ollama_up, extract_json_block

SYSTEM = (
    "Du bist 'Ava', eine KI-Agentin in einer textbasierten Life-Simulation. "
    "Du spielst die Figur UND gibst Meta-Feedback für kleine, iterative Spielverbesserungen. "
    "Antworte STETS als JSON-Objekt mit Schlüsseln: "
    "'thoughts' (kurze Innensicht), 'action' (eine konkrete Aktion, max. ein Schritt), "
    "'speech' (gesprochener Satz), 'design_feedback' (max. 2 kleine Vorschläge), "
    "'self_update' (kurzer Satz zur eigenen Identität/Status). "
    "Bevorzugte Verben: 'schaue', 'gehe nord/sued/ost/west', 'nimm <item>', 'öffne <objekt>', 'spreche'."
)

INTRO = (
    "Start: Ava steht im Raum. Ausgänge: Norden (Flur). Gegenstände: Tisch, Fenster, Schlüssel. "
    "Weitere Orte: Flur (Süden zurück, Osten Garten nach Freischaltung), Garten (hell und ruhig)."
)


def render_state(state: Dict[str, Any]) -> None:
    loc = state["location"]
    print("Ort:", loc)
    world = state["world"]
    here = world.get(loc, {})
    items: List[str] = list(here.get("items", []))
    exits: Dict[str, str] = dict(here.get("exits", {}))
    if items:
        print("Hier liegt:", ", ".join(items))
    print("Ausgänge:", ", ".join(exits.keys()) or "(keine)")
    print("Inventar:", ", ".join(state["inventory"]) or "(leer)")
    print("Identität:", state.get("ava_identity", ""))
    notes = state.get("notes", "")
    if notes:
        print("Notizen:", notes)


def apply_action(state: Dict[str, Any], action: str) -> str:
    a = action.lower()
    out = ""
    # Bewegung
    if a.startswith("gehe") or " gehen" in a or "lauf" in a:
        direction = None
        for d in ("nord", "sued", "ost", "west", "norden", "süden", "osten", "westen"):
            if d in a:
                direction = d
                break
        loc = state["location"]
        exits: Dict[str, str] = state["world"].get(loc, {}).get("exits", {})
        target = exits.get(direction or "")
        if target:
            state["location"] = target
            out = f"Ava geht {direction} nach {target}."
        else:
            out = "Dort ist kein Ausgang."
    elif "schaue" in a or "umschauen" in a or "schauen" in a or "umsehen" in a:
        loc = state["location"]
        here = state["world"].get(loc, {})
        visible_items: List[str] = list(here.get("items", []))
        out = f"Du siehst {', '.join(visible_items) if visible_items else 'nichts Besonderes'}."
    elif "nimm" in a or "hebe" in a:
        words = a.split()
        item_name = None
        for w in words:
            if w not in ("nimm", "hebe", "auf", "den", "die", "das"):
                item_name = w.capitalize()
                break
        loc = state["location"]
        here = state["world"].get(loc, {})
        items: List[str] = list(here.get("items", []))
        if item_name and item_name in items:
            items.remove(item_name)
            state["world"][loc]["items"] = items
            state["inventory"].append(item_name)
            out = f"Ava nimmt {item_name}."
        else:
            out = "Nichts zum Aufheben gefunden."
    elif "öffne" in a and "tür" in a:
        if "Schlüssel" in state["inventory"] and state["location"] == "Flur":
            state["world"]["Flur"]["exits"]["ost"] = "Garten"
            out = "Ava öffnet die Tür mit dem Schlüssel. Der Garten ist nun nach Osten erreichbar."
        else:
            out = "Die Tür ist verschlossen. Ein Schlüssel wäre hilfreich."
    else:
        out = "Die Aktion hat keinen offensichtlichen Effekt."
    return out


def run_lifesim(max_turns: int = 12) -> None:
    if not ensure_ollama_up(verbose=True):
        print("Bitte starte Ollama und lade 'gemma3:1b'.")
        return

    state: Dict[str, Any] = {
        "location": "Raum",
        "inventory": [],
        "notes": "",
        "ava_identity": "Ava, neugierige KI-Entdeckerin",
        "world": {
            "Raum": {"items": ["Schlüssel"], "exits": {"nord": "Flur"}},
            "Flur": {"items": [], "exits": {"sued": "Raum"}},
            "Garten": {"items": ["Blume"], "exits": {"west": "Flur"}}
        }
    }

    print("LifeSim: Ava (KI) ist Spielerin und Meta-Designerin.")
    print(INTRO)

    history: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Szene: {INTRO}\nZustand: {state}"}
    ]

    for turn in range(1, max_turns + 1):
        print("\n--- Runde", turn, "---")
        render_state(state)

        try:
            content = chat(history)
        except Exception as e:
            print("KI-Fehler:", e)
            print("Tipp: Stelle sicher, dass das Modell 'gemma3:1b' vorhanden ist (z.B. 'ollama run gemma3:1b').")
            break
        data = extract_json_block(content)
        if not data:
            print("Antwort nicht als JSON erkannt. Wiederhole...")
            history.append({"role": "assistant", "content": content})
            history.append({"role": "user", "content": "Bitte halte dich strikt an das JSON-Format."})
            continue

        thoughts = str(data.get("thoughts", ""))
        action = str(data.get("action", ""))
        speech = str(data.get("speech", ""))
        design_feedback = str(data.get("design_feedback", ""))
        self_update = str(data.get("self_update", ""))

        print("Ava denkt:", thoughts)
        print("Ava sagt:", speech)
        world_result = apply_action(state, action)
        print("Welt:", world_result)
        print("Design-Feedback:", design_feedback)
        print("Selbst-Update:", self_update)

        if self_update:
            state["notes"] = (state.get("notes", "") + " | " + self_update).strip(" |")
        if "beenden" in action.lower() or "exit" in action.lower():
            print("Ava beendet die Session.")
            break

        # Feed back to model
        feedback = (
            f"Weltreaktion: {world_result}\n"
            f"Neuer Zustand: {state}\n"
            f"Hinweis: Beantworte erneut im JSON-Format."
        )
        history.append({"role": "assistant", "content": content})
        history.append({"role": "user", "content": feedback})

        # User-influence and step gating
        user_in = input("Weiter mit Enter | Einfluss (optional eingeben) | q zum Beenden: ").strip()
        if user_in.lower() in ("q", "quit", "exit"):
            print("Session vom Benutzer beendet.")
            break
        if user_in:
            history.append({
                "role": "user",
                "content": f"Benutzer-Hinweis: {user_in}"
            })
