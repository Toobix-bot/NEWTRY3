import os
import sys
import subprocess
from typing import List, Tuple, Dict, Any

# Simple Pygame-based GUI launcher that spawns each game in a separate Python process.
# Console games are launched with a new console window on Windows for proper input handling.

try:
    import pygame  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError("Pygame ist erforderlich für den GUI-Launcher. Bitte 'pip install -r requirements.txt' ausführen.") from e


CELL_H = 56
PAD_X = 20
PAD_Y = 20
BTN_W = 460
BTN_H = 44
GAP = 12


def _main_path() -> str:
    base = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base, "main.py")


def _spawn_game(run_id: str, needs_console: bool) -> None:
    py = sys.executable
    main_py = _main_path()
    if not os.path.exists(main_py):
        print("main.py nicht gefunden:", main_py)
        return

    args = [py, main_py, "--run", run_id]

    # On Windows, open console games in a new console window for stdin support.
    creationflags = 0
    if os.name == "nt" and needs_console:
        creationflags = 0x00000010  # CREATE_NEW_CONSOLE

    try:
        subprocess.Popen(args, creationflags=creationflags)
    except Exception as e:
        print("Konnte Spiel nicht starten:", e)


def run_launcher() -> None:
    entries: List[Dict[str, Any]] = [
        {"title": "Zahlenraten (Konsole)", "run": "number_guess", "console": True},
        {"title": "Tic-Tac-Toe (Konsole)", "run": "tic_tac_toe", "console": True},
        {"title": "KI-Quiz (Ollama, Konsole)", "run": "ollama_quiz", "console": True},
        {"title": "LifeSim (Text, KI)", "run": "lifesim", "console": True},
        {"title": "LifeSim GUI (pygame, KI)", "run": "lifesim_gui", "console": False},
        {"title": "Co-Play (Text: Ava+Ben)", "run": "coplay", "console": True},
        {"title": "Co-Play GUI (pygame: Ava+Ben)", "run": "coplay_gui", "console": False},
    ]

    pygame.init()
    font = pygame.font.SysFont(None, 24)
    title_font = pygame.font.SysFont(None, 32, bold=True)

    width = PAD_X * 2 + BTN_W
    height = PAD_Y * 2 + (BTN_H + GAP) * len(entries) + 80
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Spielesammlung – Launcher")
    clock = pygame.time.Clock()

    # Precompute button rects
    buttons: List[Tuple[pygame.Rect, Dict[str, Any]]] = []
    y = PAD_Y + 60
    for e in entries:
        rect = pygame.Rect(PAD_X, y, BTN_W, BTN_H)
        buttons.append((rect, e))
        y += BTN_H + GAP

    quit_rect = pygame.Rect(PAD_X, height - PAD_Y - BTN_H, BTN_W, BTN_H)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if quit_rect.collidepoint(mx, my):
                    running = False
                else:
                    for rect, meta in buttons:
                        if rect.collidepoint(mx, my):
                            _spawn_game(str(meta["run"]), bool(meta.get("console", False)))
                            break

        # Draw
        screen.fill((18, 18, 22))
        title = title_font.render("Python Spielesammlung – Launcher", True, (235, 235, 245))
        screen.blit(title, (PAD_X, PAD_Y))

        mouse = pygame.mouse.get_pos()
        for rect, meta in buttons:
            hover = rect.collidepoint(mouse)
            color = (55, 120, 200) if hover else (45, 90, 160)
            pygame.draw.rect(screen, color, rect, border_radius=8)
            pygame.draw.rect(screen, (20, 40, 80), rect, width=2, border_radius=8)

            label = meta["title"]
            txt = font.render(label, True, (240, 240, 250))
            screen.blit(txt, (rect.x + 12, rect.y + 12))

        # Quit button
        hover_q = quit_rect.collidepoint(mouse)
        qcolor = (200, 70, 70) if hover_q else (160, 50, 50)
        pygame.draw.rect(screen, qcolor, quit_rect, border_radius=8)
        pygame.draw.rect(screen, (90, 30, 30), quit_rect, width=2, border_radius=8)
        qtxt = font.render("Beenden (Esc)", True, (250, 235, 235))
        screen.blit(qtxt, (quit_rect.x + 12, quit_rect.y + 12))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
