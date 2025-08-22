from typing import Dict, Any, List
from .llm_client import chat, ensure_ollama_up, parse_ava_turn
from .schemas import AvaTurn, WorldPatch

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

    for turn_idx in range(1, max_turns + 1):
        print("\n--- Runde", turn_idx, "---")
        render_state(state)

        # 1) KI-Zug holen und validieren
        try:
            content = chat(history)
        except Exception as e:
            print("KI-Fehler:", e)
            print("Tipp: Stelle sicher, dass das Modell 'gemma3:1b' vorhanden ist (z.B. 'ollama run gemma3:1b').")
            break

        parsed: AvaTurn | None = parse_ava_turn(content)
        if not parsed:
            print("Antwort nicht valides JSON-Schema. Ich bitte die KI um korrektes Format…")
            history.append({"role": "assistant", "content": content})
            history.append({"role": "user", "content": "Bitte antworte strikt als JSON im vereinbarten Schema."})
            continue

        # 2) Mikro-Ebene anwenden
        world_reaction = apply_action(state, parsed.action)
        print("Ava sagt:", parsed.speech)
        print("Welt:", world_reaction)

        # 3) Makro-Ebene (optionale kleine Patches)
        if parsed.world_patch:
            wp: WorldPatch = parsed.world_patch
            if wp.open_exit:
                src = wp.open_exit.get("from")
                direction = wp.open_exit.get("dir")
                to = wp.open_exit.get("to")
                if src and direction and to and src in state["world"]:
                    state["world"].setdefault(src, {}).setdefault("exits", {})[direction] = to
                    print(f"Design: Ausgang geöffnet {src} --{direction}--> {to}")
            if wp.add_item:
                at = wp.add_item.get("at")
                item = wp.add_item.get("item")
                if at and item and at in state["world"]:
                    state["world"][at].setdefault("items", []).append(item)
                    print(f"Design: Item hinzugefügt {item} @ {at}")
            if wp.set_goal:
                state["notes"] = (state.get("notes", "") + f"\nZiel: {wp.set_goal}").strip()
                print(f"Ziel gesetzt: {wp.set_goal}")

        if parsed.design_feedback:
            print("Feedback:", parsed.design_feedback)
        if parsed.self_update:
            state["ava_identity"] = (state.get("ava_identity", "Ava") + "; " + parsed.self_update).strip()

        # 4) Kontext für nächsten Zug aktualisieren
        history.append({"role": "assistant", "content": content})
        history.append({
            "role": "user",
            "content": (
                f"Weltreaktion: {world_reaction}. Zustand: {state}. "
                "Wenn sinnvoll, schlage kleine world_patch-Änderungen vor."
            ),
        })

        # 5) Benutzer-Einfluss / Fortsetzen
        user_in = input("Weiter mit Enter | Einfluss (optional) | q zum Beenden: ").strip()
        if user_in.lower() in ("q", "quit", "exit"):
            print("Session vom Benutzer beendet.")
            break
        if user_in:
            history.append({"role": "user", "content": f"Benutzer-Hinweis: {user_in}"})
