import os
import sys
from typing import Callable, Dict

from .ollama_quiz import run_ollama_quiz
from .llm_client import ensure_ollama_up
from .ai_lifesim import run_lifesim
from .number_guess import play_number_guess
from .tic_tac_toe import play_tic_tac_toe


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def prompt(msg: str) -> str:
    try:
        return input(msg)
    except EOFError:
        return ""


def health_check(verbose: bool = False) -> bool:
    ok = True
    # Python version
    if sys.version_info < (3, 9):
        ok = False
        if verbose:
            print("Python >= 3.9 required. Detected:", sys.version)
    else:
        if verbose:
            print("Python version OK:", sys.version.split()[0])

    # Ollama
    try:
        up = ensure_ollama_up(verbose=verbose)
        ok = ok and up
    except Exception as e:
        ok = False
        if verbose:
            print("Ollama check error:", e)

    return ok


def main_menu():
    actions: Dict[str, Callable[[], None]] = {
        "1": play_number_guess,
        "2": play_tic_tac_toe,
        "3": run_ollama_quiz,
        "4": run_lifesim,
        "q": lambda: None,
    }

    while True:
        clear_screen()
        print("=== Python Spielesammlung ===")
        print("1) Zahlenraten (Konsole)")
        print("2) Tic-Tac-Toe (Konsole)")
        print("3) KI-Quiz (Ollama gemma3:1b)")
        print("4) LifeSim: KI als Spielerin & Designerin")
        print("q) Beenden")
        choice = prompt("Auswahl: ").strip().lower()
        if choice == "q":
            print("Bye!")
            break
        action = actions.get(choice)
        if action:
            clear_screen()
            action()
            input("\nDrücke Enter, um zum Menü zurückzukehren...")
        else:
            print("Ungültige Auswahl.")
            input("Enter...")
