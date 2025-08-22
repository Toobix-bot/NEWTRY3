import random


def play_number_guess():
    print("Zahlenraten: Ich denke mir eine Zahl zwischen 1 und 100. Kannst du sie erraten?")
    target = random.randint(1, 100)
    tries = 0
    max_tries = 10
    while tries < max_tries:
        raw = input(f"Versuch {tries+1}/{max_tries} – Deine Zahl: ")
        try:
            guess = int(raw)
        except ValueError:
            print("Bitte gib eine ganze Zahl ein.")
            continue
        tries += 1
        if guess == target:
            print(f"Richtig! Die Zahl war {target}. Du hast {tries} Versuche gebraucht.")
            return
        hint = "größer" if guess < target else "kleiner"
        print(f"Leider nein. Die gesuchte Zahl ist {hint}.")
    print(f"Schade! Die Zahl war {target}.")
