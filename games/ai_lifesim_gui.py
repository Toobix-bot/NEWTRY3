import pygame
from typing import Tuple, Dict, Any, List
from .llm_client import chat, ensure_ollama_up, extract_json_block

CELL = 32
GRID = (15, 10)  # cols, rows
WIN = (GRID[0] * CELL, GRID[1] * CELL + 60)

SYSTEM = (
    "Du bist 'Ava', eine KI-Figur in einer 2D-Gitterwelt. "
    "Antworte als JSON mit Schlüsseln: thoughts, action, speech, design_feedback. "
    "Action ist eine der: 'move_up', 'move_down', 'move_left', 'move_right', 'wait', 'interact'."
)


def draw_grid(screen):
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
    elif action == "wait" or action == "interact":
        pass
    state["pos"] = clamp_pos((x, y))
    return f"Ava {action} -> {state['pos']}"


def run_lifesim_gui(max_turns: int = 50):
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
    }

    history: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Startposition: {state['pos']} auf einem leeren Gitter. Warte auf deine Aktion."}
    ]

    turn = 0
    user_hint = ""
    running = True
    while running and turn < max_turns:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN:
                    user_hint = state.get("hint", "").strip()
                    if user_hint:
                        history.append({"role": "user", "content": f"Benutzer-Hinweis: {user_hint}"})
                        state["hint"] = ""
                    # Step the AI one turn
                    try:
                        content = chat(history)
                    except Exception as e:
                        print("KI-Fehler:", e)
                        running = False
                        break
                    data = extract_json_block(content)
                    if not data:
                        history.append({"role": "assistant", "content": content})
                        history.append({"role": "user", "content": "Bitte liefere gültiges JSON."})
                    else:
                        action = str(data.get("action", "wait"))
                        world = apply_action(state, action)
                        history.append({"role": "assistant", "content": content})
                        history.append({"role": "user", "content": f"Weltreaktion: {world}. Neue Position: {state['pos']}"})
                        turn += 1
                elif event.key == pygame.K_BACKSPACE:
                    state["hint"] = state.get("hint", "")[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        state["hint"] = state.get("hint", "") + event.unicode

        draw_grid(screen)
        # Draw Ava
        ax, ay = state["pos"]
        rect = pygame.Rect(ax * CELL + 4, ay * CELL + 4, CELL - 8, CELL - 8)
        pygame.draw.rect(screen, (80, 180, 250), rect)

        # UI panel
        panel = pygame.Rect(0, GRID[1] * CELL, WIN[0], 60)
        pygame.draw.rect(screen, (15, 15, 18), panel)
        txt = font.render(f"Enter: Nächster Zug | Hinweis tippen: {state.get('hint','')}", True, (230, 230, 230))
        screen.blit(txt, (8, GRID[1] * CELL + 8))
        pos_txt = font.render(f"Pos: {state['pos']}  Turn: {turn}", True, (200, 200, 200))
        screen.blit(pos_txt, (8, GRID[1] * CELL + 30))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
