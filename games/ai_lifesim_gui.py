from typing import Tuple, Dict, Any, List
from .llm_client import chat, ensure_ollama_up, parse_ava_turn
from .schemas import AvaTurn, WorldPatch
import pygame  # type: ignore


CELL = 32
GRID = (15, 10)
WIN = (GRID[0] * CELL, GRID[1] * CELL + 140)

SYSTEM = (
    "Du bist 'Ava', eine KI-Figur in einer 2D-Gitterwelt. Antworte als JSON gemäß Schema: "
    "thoughts, action, speech, design_feedback, perceptions, experience, insights, conclusions, wishes, fears, world_patch."
)


def draw_grid(screen: pygame.Surface) -> None:
    screen.fill((20, 20, 25))
    for x in range(GRID[0]):
        for y in range(GRID[1]):
            rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            pygame.draw.rect(screen, (40, 40, 50), rect, 1)


def clamp_pos(pos: Tuple[int, int]) -> Tuple[int, int]:
    x, y = pos
    x = max(0, min(GRID[0] - 1, x))
    y = max(0, min(GRID[1] - 1, y))
    return x, y


def apply_action(state: Dict[str, Any], action: str) -> str:
    x, y = state["pos"]
    if action == "move_up":
        y -= 1
    elif action == "move_down":
        y += 1
    elif action == "move_left":
        x -= 1
    elif action == "move_right":
        x += 1
    # wait/interact: no movement
    state["pos"] = clamp_pos((x, y))
    return f"Ava {action} -> {state['pos']}"


def _apply_world_patch(state: Dict[str, Any], wp: WorldPatch) -> None:
    # In GUI-Variante halten wir Patches klein; Notizen anzeigen
    if wp.set_goal:
        state["notes"] = (state.get("notes", "") + f" | Ziel: {wp.set_goal}").strip(" |")


def _step_ai(history: List[Dict[str, str]], state: Dict[str, Any]) -> bool:
    try:
        content = chat(history)
    except Exception as e:
        print("KI-Fehler:", e)
        return False
    parsed: AvaTurn | None = parse_ava_turn(content)
    if not parsed:
        history.append({"role": "assistant", "content": content})
        history.append({"role": "user", "content": "Bitte antworte strikt als JSON im vereinbarten Schema."})
        return False

    world_reaction = apply_action(state, parsed.action)
    state["speech"] = parsed.speech
    state["thoughts"] = parsed.thoughts
    state["perceptions"] = parsed.perceptions or ""
    state["wishes"] = parsed.wishes or ""
    state["fears"] = parsed.fears or ""
    if parsed.world_patch:
        _apply_world_patch(state, parsed.world_patch)

    history.append({"role": "assistant", "content": content})
    history.append({"role": "user", "content": f"Welt: {world_reaction}. Zustand: pos={state['pos']}."})
    return True


def run_lifesim_gui(max_turns: int = 50) -> None:
    if not ensure_ollama_up(verbose=True):
        print("Bitte starte Ollama und lade 'gemma3:1b'.")
        return

    pygame.init()
    screen = pygame.display.set_mode(WIN)
    pygame.display.set_caption("LifeSim GUI – Ava (KI)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    state: Dict[str, Any] = {
        "pos": (GRID[0] // 2, GRID[1] // 2),
        "hint": "",
        "speech": "",
        "thoughts": "",
        "perceptions": "",
        "wishes": "",
        "fears": "",
        "notes": "",
        "auto": False,
    }

    history: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Startposition: {state['pos']} auf einem leeren Gitter. Warte auf deine Aktion."}
    ]

    turn = 0
    auto_frames = 0
    running = True
    while running and turn < max_turns:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    state["auto"] = not state.get("auto", False)
                    auto_frames = 0
                elif event.key == pygame.K_RETURN:
                    hint = state.get("hint", "").strip()
                    if hint:
                        history.append({"role": "user", "content": f"Benutzer-Hinweis: {hint}"})
                        state["hint"] = ""
                    if _step_ai(history, state):
                        turn += 1
                elif event.key == pygame.K_BACKSPACE:
                    state["hint"] = state.get("hint", "")[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        state["hint"] = state.get("hint", "") + event.unicode

        # Auto-step pacing (every ~40 frames)
        if running and state.get("auto", False):
            auto_frames += 1
            if auto_frames >= 40:
                if _step_ai(history, state):
                    turn += 1
                auto_frames = 0

        draw_grid(screen)
        ax, ay = state["pos"]
        rect = pygame.Rect(ax * CELL + 4, ay * CELL + 4, CELL - 8, CELL - 8)
        pygame.draw.rect(screen, (80, 180, 250), rect)

        panel = pygame.Rect(0, GRID[1] * CELL, WIN[0], 140)
        pygame.draw.rect(screen, (15, 15, 18), panel)
        txt = font.render(
            f"Enter=Zug  Space=Auto {'ON' if state.get('auto') else 'OFF'}  | Hinweis: {state.get('hint','')}",
            True, (230, 230, 230)
        )
        screen.blit(txt, (8, GRID[1] * CELL + 8))
        pos_txt = font.render(f"Pos: {state['pos']}  Turn: {turn}", True, (200, 200, 200))
        screen.blit(pos_txt, (8, GRID[1] * CELL + 30))
        y = GRID[1] * CELL + 52
        if state.get("speech"):
            screen.blit(font.render(f"Ava: {state['speech'][:90]}", True, (180, 220, 255)), (8, y)); y += 20
        if state.get("thoughts"):
            screen.blit(font.render(f"Gedanken: {state['thoughts'][:90]}", True, (220, 200, 160)), (8, y)); y += 20
        if state.get("perceptions"):
            screen.blit(font.render(f"Wahrnehmung: {state['perceptions'][:90]}", True, (200, 230, 200)), (8, y)); y += 20
        wishes = state.get("wishes", ""); fears = state.get("fears", "")
        if wishes or fears:
            screen.blit(font.render(f"Wünsche/Ängste: {wishes[:40]} | {fears[:40]}", True, (230, 200, 200)), (8, y)); y += 20
        if state.get("notes"):
            screen.blit(font.render(f"Notizen: {state['notes'][:90]}", True, (210, 210, 210)), (8, y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
