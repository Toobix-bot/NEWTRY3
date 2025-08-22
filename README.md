# NEWTRY3 – Python Spielesammlung mit Ollama (gemma3:1b)

Diese Repo enthält eine kleine Spielesammlung für die Konsole sowie ein KI-Quiz, das lokal über Ollama mit dem Modell `gemma3:1b` läuft.

## Inhalte

- Zahlenraten (Konsole)
- Tic-Tac-Toe (Konsole)
- KI-Quiz (Ollama gemma3:1b)
- LifeSim: KI als Spielerin & Meta-Designer (Konsole)
- LifeSim GUI (pygame)
- Co-Play: Ava (KI) + Ben (Mensch) (Konsole)
- Co-Play GUI (pygame)
- Neuer GUI-Launcher (pygame) zum Starten aller Varianten per Mausklick

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

Spielesammlung (Konsolen-Menü) starten:

```powershell
python .\main.py
```

Grafischen Launcher starten (empfohlen):

```powershell
python .\main.py --gui
```

### LifeSim & Co-Play – Prinzip: Mikro-Handlung + Makro-Design

Die KI agiert auf zwei Ebenen:

- Individuum (Mikro): Ava führt pro Zug genau eine Aktion aus (z. B. move_up/move_right/wait/interact oder sprechen). Diese verändert die unmittelbare Spielsituation.
- Großes Ganze (Makro): Ava liefert zusätzlich design_feedback (und perspektivisch world_patches), um Regeln, Ziele oder Weltobjekte iterativ zu verbessern. Dadurch „lebt“ die Welt mit und die KI gestaltet sie aktiv mit.

Im Textmodus erfolgt die Interaktion über Tastatur. In den GUI-Varianten steuerst du Ben per Pfeiltasten/WASD, bestätigst Züge mit Enter und kannst unten kurze Hinweise an die KI tippen, die in den nächsten Zug einfließen.

Geplant/Optional: Ein JSON-Feld `world_patch` (z. B. {"add_item": ..., "open_exit": ...}) erlaubt es der KI, kleine, überprüfte Änderungen an der Welt vorzuschlagen, die das Spiel nach Sicherheitsprüfungen übernimmt.

## Ordnerstruktur

```
main.py
games/
	__init__.py
	menu.py
	launcher_gui.py
	number_guess.py
	tic_tac_toe.py
	ollama_quiz.py
	ai_lifesim.py
	ai_lifesim_gui.py
	ai_coplay.py
	ai_coplay_gui.py
requirements.txt
```

## Hinweise

- Das KI-Quiz nutzt die lokale Ollama-API unter `http://localhost:11434`. Stelle sicher, dass Ollama läuft und `gemma3:1b` vorhanden ist.
- Das Modell gibt die Frage/Antwort im JSON-Format zurück. Falls das Parsing scheitert, wird eine Fehlermeldung ausgegeben.
- Für schnelle Iteration kannst du den GUI-Launcher nutzen. Konsolenspiele werden unter Windows in einem separaten Konsolenfenster gestartet, damit die Eingaben sauber funktionieren.

