import pygame
from typing import Tuple, Dict, Any, List
from .llm_client import chat, ensure_ollama_up, extract_json_block

CELL = 32
GRID = (15, 10)  # cols, rows
WIN = (GRID[0] * CELL, GRID[1] * CELL + 120)

SYSTEM = (
    "Du bist 'Ava', eine KI-Figur in einer 2D-Gitterwelt mit einem Menschen (Ben). "
    "Antworte NUR als JSON mit Schlüsseln: thoughts, action, speech, design_feedback. "
    "Action ist genau eine aus: move_up, move_down, move_left, move_right, wait, interact."
)


def clamp_pos(pos: Tuple[int, int]) -> Tuple[int, int]:
    x, y = pos
    x = max(0, min(GRID[0] - 1, x))
    y = max(0, min(GRID[1] - 1, y))
    return x, y


def apply_action(state: Dict[str, Any], who: str, action: str) -> str:
    key = "ava" if who == "ava" else "ben"
    x, y = state["pos"][key]
    if action == "move_up":
        y -= 1
    elif action == "move_down":
        y += 1
    elif action == "move_left":
        x -= 1
    elif action == "move_right":
        x += 1
    # wait/interact: no movement change
    state["pos"][key] = clamp_pos((x, y))
    return f"{who} {action} -> {state['pos'][key]}"


def draw_grid(screen):
    screen.fill((18, 18, 22))
    for x in range(GRID[0]):
        for y in range(GRID[1]):
            rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            pygame.draw.rect(screen, (38, 38, 48), rect, 1)


def draw_hud(screen, font, state: Dict[str, Any], turn: int):
    panel = pygame.Rect(0, GRID[1] * CELL, WIN[0], 120)
    pygame.draw.rect(screen, (15, 15, 18), panel)
    line1 = f"Enter=Zug ausführen | Ben-Aktion: {state.get('pending_ben','wait')} | Hinweis: {state.get('hint','')}"
    line2 = f"Turn: {turn}  Ava@{state['pos']['ava']}  Ben@{state['pos']['ben']}"
    txt1 = font.render(line1, True, (230, 230, 230))
    txt2 = font.render(line2, True, (200, 200, 200))
    screen.blit(txt1, (8, GRID[1] * CELL + 8))
    screen.blit(txt2, (8, GRID[1] * CELL + 34))
    y = GRID[1] * CELL + 56
    if state.get("speech"):
        txt3 = font.render(f"Ava sagt: {state['speech'][:80]}", True, (180, 220, 255))
        screen.blit(txt3, (8, y))
        y += 22
    if state.get("thoughts"):
        txt4 = font.render(f"Gedanken: {state['thoughts'][:80]}", True, (220, 200, 160))
        screen.blit(txt4, (8, y))
        y += 22
    if state.get("feedback"):
        txt5 = font.render(f"Feedback: {state['feedback'][:80]}", True, (200, 220, 200))
        screen.blit(txt5, (8, y))


def run_coplay_gui(max_turns: int = 100):
    if not ensure_ollama_up(verbose=True):
        print("Bitte starte Ollama und lade 'gemma3:1b'.")
        return

    pygame.init()
    screen = pygame.display.set_mode(WIN)
    pygame.display.set_caption("Co-Play GUI – Ava (KI) & Ben (Mensch)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    state: Dict[str, Any] = {
        "pos": {"ava": (GRID[0] // 2, GRID[1] // 2), "ben": (1, 1)},
        "hint": "",
        "pending_ben": "wait",
    "speech": "",
    "thoughts": "",
    "feedback": "",
    }

    history: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Startpositionen: Ava@{state['pos']['ava']}, Ben@{state['pos']['ben']} auf {GRID}."}
    ]

    def set_ben_action_from_key(key: int):
        if key in (pygame.K_UP, pygame.K_w):
            state["pending_ben"] = "move_up"
        elif key in (pygame.K_DOWN, pygame.K_s):
            state["pending_ben"] = "move_down"
        elif key in (pygame.K_LEFT, pygame.K_a):
            state["pending_ben"] = "move_left"
        elif key in (pygame.K_RIGHT, pygame.K_d):
            state["pending_ben"] = "move_right"

    turn = 0
    running = True
    while running and turn < max_turns:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN:
                    # Execute a co-play turn
                    ben_act = state.get("pending_ben", "wait")
                    world_ben = apply_action(state, "ben", ben_act)
                    prompt_ai = (
                        f"Zustand: Ava@{state['pos']['ava']}, Ben@{state['pos']['ben']}. "
                        f"Ben-Aktion: {ben_act}. Weltreaktion: {world_ben}."
                    )
                    uhint = state.get("hint", "").strip()
                    if uhint:
                        prompt_ai += f" Benutzer-Feedback: {uhint}."
                    history.append({"role": "user", "content": prompt_ai})

                    try:
                        content = chat(history)
                    except Exception as e:
                        print("KI-Fehler:", e)
                        running = False
                        break

                    data = extract_json_block(content)
                    if not data:
                        history.append({"role": "assistant", "content": content})
                        history.append({"role": "user", "content": "Bitte gültiges JSON liefern."})
                    else:
                        action_ava = str(data.get("action", "wait"))
                        state["speech"] = str(data.get("speech", ""))
                        state["thoughts"] = str(data.get("thoughts", ""))
                        state["feedback"] = str(data.get("design_feedback", ""))
                        world_ava = apply_action(state, "ava", action_ava)
                        # Feed back
                        fb = (
                            f"Weltreaktionen – Ben: {world_ben}; Ava: {world_ava}. "
                            f"Neuer Zustand: Ava@{state['pos']['ava']}, Ben@{state['pos']['ben']}."
                        )
                        history.append({"role": "assistant", "content": content})
                        history.append({"role": "user", "content": fb})
                        turn += 1
                    # reset for next turn
                    state["pending_ben"] = "wait"
                    state["hint"] = ""
                elif event.key == pygame.K_BACKSPACE:
                    state["hint"] = state.get("hint", "")[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        state["hint"] = state.get("hint", "") + event.unicode
                    # also capture movement keys
                    set_ben_action_from_key(event.key)

        # Draw world
        draw_grid(screen)
        # Draw Ben (green) and Ava (blue)
        bx, by = state["pos"]["ben"]
        ax, ay = state["pos"]["ava"]
        ben_rect = pygame.Rect(bx * CELL + 4, by * CELL + 4, CELL - 8, CELL - 8)
        ava_rect = pygame.Rect(ax * CELL + 4, ay * CELL + 4, CELL - 8, CELL - 8)
        pygame.draw.rect(screen, (100, 220, 100), ben_rect)
        pygame.draw.rect(screen, (80, 180, 250), ava_rect)

        draw_hud(screen, font, state, turn)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
