Tested on **Python 3.13**

# Riichi Mahjong ML and GUI

Riichi mahjong - Japanese variation of the classic tile-based game.

## Features

- **Neural network model training**
- **Model comparison**
- **Interactive GUI** which lets you play against selected models

## Prerequisites
- python  
- uv
- (optional) CUDA capable device

## Installation

### Game only

1. Clone the repository:  
- `git clone https://github.com/notEloiir/RiichiMahjong.git`
   
2. Install dependencies:
- `cd RiichiMahjong`
- `uv sync --extra=cpu`

### + Data engineering

3. Download match replays
   1. Clone phoenix-logs repository into the project directory  
   - `git clone https://github.com/ApplySci/phoenix-logs.git`

### + ML  

4. Recommended, if on CUDA-capable device
  - `uv sync --extra=cu128`

## Usage

### Game

- `uv run main.py`

### Data engineering && ML  

1. Download raw logs as explained at https://github.com/ApplySci/phoenix-logs/blob/master/README.md
    1. example (maybe doesn't work on Linux):
    - download ids: `uv run python phoenix-logs/main.py -a id -y 2017`
    - download content (needs ids): `uv run python phoenix-logs/main.py -a content -y 2017 -l 100000 -t 100`
      - 1e5 matches is about 1.2GB of raw data (float32, after preliminary filtering)
    - check content (optional): `uv run python phoenix-logs/debug.py -y 2017`

2. Open CLI menu
  - `uv run cli_menu.py`

3. Prepare data
    1. example:
    - parse logs into raw data: `data 2017 2017raw`
    - refine raw data: `process 2017raw 2017processed`  

4. Train and save model
    1. example:
    - `init 8 512`
    - `train 2017processed`
    - `save 2017model`

