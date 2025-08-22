from typing import List, Optional

Board = List[str]


def print_board(b: Board) -> None:
    print(f"{b[0]}|{b[1]}|{b[2]}")
    print("-+-+-")
    print(f"{b[3]}|{b[4]}|{b[5]}")
    print("-+-+-")
    print(f"{b[6]}|{b[7]}|{b[8]}")


def winner(b: Board) -> Optional[str]:
    wins = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, c, d in wins:
        if b[a] == b[c] == b[d] and b[a] in ("X", "O"):
            return b[a]
    return None


def full(b: Board) -> bool:
    return all(cell in ("X", "O") for cell in b)


def play_tic_tac_toe() -> None:
    print("Tic-Tac-Toe: Spieler X beginnt. Gib Position 1-9 ein.")
    board: Board = [str(i) for i in range(1, 10)]
    player = "X"
    while True:
        print_board(board)
        move = input(f"Spieler {player}, Position (1-9): ")
        if not move.isdigit() or not (1 <= int(move) <= 9):
            print("Ungültige Eingabe.")
            continue
        idx = int(move) - 1
        if board[idx] in ("X", "O"):
            print("Feld belegt.")
            continue
        board[idx] = player
        w = winner(board)
        if w:
            print_board(board)
            print(f"Spieler {w} gewinnt!")
            return
        if full(board):
            print_board(board)
            print("Unentschieden!")
            return
        player = "O" if player == "X" else "X"
