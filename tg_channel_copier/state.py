import os
import json

STATE_FILE = "copier_state.json"


def get_last_copied_id(source_id: int) -> int:
    """Возвращает ID последнего скопированного сообщения для указанного канала."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state.get(str(source_id), 0)
        except Exception:
            pass
    return 0


def save_last_copied_id(source_id: int, last_id: int):
    """Сохраняет ID последнего скопированного сообщения."""
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass
    state[str(source_id)] = last_id
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)
