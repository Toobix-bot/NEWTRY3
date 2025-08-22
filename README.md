# NEWTRY3 – Python Spielesammlung mit Ollama (gemma3:1b)

Diese Repo enthält eine kleine Spielesammlung für die Konsole sowie ein KI-Quiz, das lokal über Ollama mit dem Modell `gemma3:1b` läuft.

## Inhalte

- Zahlenraten (Konsole)
- Tic-Tac-Toe (Konsole)
- KI-Quiz (Ollama gemma3:1b)
 - LifeSim: KI als Spielerin & Meta-Designer (Ollama gemma3:1b)

## Voraussetzungen

- Windows mit Python 3.9+ (empfohlen 3.10+)
- Optional: [Ollama](https://ollama.com/) installiert und laufend, mit Modell `gemma3:1b`

## Setup (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Optional: Ollama und Modell installieren/laden

```powershell
# Installiere Ollama (siehe Website); dann:
ollama run gemma3:1b  # lädt das Modell beim ersten Mal herunter
```

## Start

Gesundheitscheck (Python-Version, Ollama-Erreichbarkeit):

```powershell
python .\main.py --check
```

Spielesammlung starten:

```powershell
python .\main.py
```

### LifeSim

Im Menü Option "LifeSim" wählen. Ava (die KI) spielt eine Figur und gibt gleichzeitig konkretes Design-Feedback im JSON-Format zurück. Das Spiel parst die Antwort, führt die Aktion in der Welt aus und füttert die Reaktion wieder an die KI zurück.

## Ordnerstruktur

```
main.py
games/
	__init__.py
	menu.py
	number_guess.py
	tic_tac_toe.py
	ollama_quiz.py
requirements.txt
```

## Hinweise

- Das KI-Quiz nutzt die lokale Ollama-API unter `http://localhost:11434`. Stelle sicher, dass Ollama läuft und `gemma3:1b` vorhanden ist.
- Das Modell gibt die Frage/Antwort im JSON-Format zurück. Falls das Parsing scheitert, wird eine Fehlermeldung ausgegeben.

