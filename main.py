import argparse
from games.menu import main_menu, health_check


def parse_args():
    parser = argparse.ArgumentParser(description="Game Collection with Ollama integration")
    parser.add_argument("--check", action="store_true", help="Run environment and Ollama health checks and exit")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.check:
        ok = health_check(verbose=True)
        raise SystemExit(0 if ok else 2)
    main_menu()


if __name__ == "__main__":
    main()
