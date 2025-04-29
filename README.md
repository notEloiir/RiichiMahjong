Tested on **Python 3.13**

# Riichi Mahjong ML and GUI

Riichi mahjong - Japanese variation of the classic tile-based game.

## Features

- **Neural network model training**
- **Model comparison**
- **Interactive GUI** which lets you play against selected models

## Prerequisites
- python  
- uv (preferably)  
- CUDA capable device (preferably, if training)

## Installation

### GUI only - just play the game

1. Clone the repository:  
- `git clone https://github.com/notEloiir/RiichiMahjong.git`
   
2. Install dependencies:
- `cd RiichiMahjong`
- if you have uv: `uv sync --extra=cpu`
- otherwise: `pip install -r requirements.txt`

### Data engineering:

3. Download match replays
  1. Clone phoenix-logs repository into the project directory  
    - `git clone https://github.com/ApplySci/phoenix-logs.git`  
  2. Install phoenix-logs and download logs and their contents, phoenix-logs/README.md explains how
    - https://github.com/ApplySci/phoenix-logs

### ML  

4. Install extra dependencies
  - if using CUDA: `uv sync --extra=cu128`
  - else: `uv sync --extra=cpu`

## Run

### GUI

- `uv run main.py`

### Data engineering && ML  

- `uv run cli_menu.py`

