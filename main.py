import argparse
from games.menu import main_menu, health_check

# Optional imports for direct run mapping
from games.number_guess import play_number_guess
from games.tic_tac_toe import play_tic_tac_toe
from games.ollama_quiz import run_ollama_quiz
from games.ai_lifesim import run_lifesim
from games.ai_lifesim_gui import run_lifesim_gui
from games.ai_coplay import run_coplay
from games.ai_coplay_gui import run_coplay_gui
from games.launcher_gui import run_launcher


def parse_args():
    parser = argparse.ArgumentParser(description="Game Collection with Ollama integration")
    parser.add_argument("--check", action="store_true", help="Run environment and Ollama health checks and exit")
    parser.add_argument("--gui", action="store_true", help="Start the graphical launcher (pygame)")
    parser.add_argument("--run", type=str, help="Run a specific game by id (used by GUI launcher)")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.check:
        ok = health_check(verbose=True)
        raise SystemExit(0 if ok else 2)
    if getattr(args, "gui", False):
        run_launcher()
        return
    run_id = getattr(args, "run", None)
    if run_id:
        # Map run_id to concrete game function
        mapping = {
            "number_guess": play_number_guess,
            "tic_tac_toe": play_tic_tac_toe,
            "ollama_quiz": run_ollama_quiz,
            "lifesim": run_lifesim,
            "lifesim_gui": run_lifesim_gui,
            "coplay": run_coplay,
            "coplay_gui": run_coplay_gui,
        }
        fn = mapping.get(run_id)
        if not fn:
            print(f"Unbekannte Run-ID: {run_id}")
            raise SystemExit(2)
        fn()
        return
    main_menu()


if __name__ == "__main__":
    main()
