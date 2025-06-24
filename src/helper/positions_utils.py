import json
import os

POSITIONS_FILE = "positions.json"

def save_positions(positions, path=POSITIONS_FILE):
    with open(path, "w") as f:
        json.dump(positions, f)

def load_positions(path=POSITIONS_FILE):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}
import json
import os

POSITIONS_FILE = "positions.json"

def save_positions(positions, path=POSITIONS_FILE):
    with open(path, "w") as f:
        json.dump(positions, f)

def load_positions(path=POSITIONS_FILE):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}