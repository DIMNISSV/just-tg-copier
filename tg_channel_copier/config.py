import os
from dotenv import load_dotenv

load_dotenv()


def parse_channel_id(val: str):
    val = val.strip()
    if val.startswith('-'):
        try:
            return int(val)
        except ValueError:
            return val
    elif val.isdigit():
        try:
            return int(val)
        except ValueError:
            return val
    return val


def load_config() -> dict:
    # Запрос API_ID и API_HASH (получить на my.telegram.org)
    api_id = os.getenv("API_ID")
    if not api_id:
        api_id = input("Введите ваш API_ID: ").strip()
        with open(".env", "a", encoding="utf-8") as f:
            f.write(f"API_ID={api_id}\n")

    api_hash = os.getenv("API_HASH")
    if not api_hash:
        api_hash = input("Введите ваш API_HASH: ").strip()
        with open(".env", "a", encoding="utf-8") as f:
            f.write(f"API_HASH={api_hash}\n")

    # Источник и цель (username, ссылка или ID)
    source = os.getenv("SOURCE_CHANNEL")
    if not source:
        source = input("Введите юзернейм или ID канала-ИСТОЧНИКА (например, @source_channel): ").strip()
        with open(".env", "a", encoding="utf-8") as f:
            f.write(f"SOURCE_CHANNEL={source}\n")

    target = os.getenv("TARGET_CHANNEL")
    if not target:
        target = input("Введите юзернейм или ID канала-ПОЛУЧАТЕЛЯ (например, @target_channel): ").strip()
        with open(".env", "a", encoding="utf-8") as f:
            f.write(f"TARGET_CHANNEL={target}\n")

    session_name = os.getenv("SESSION_NAME", "channel_copier_session")

    return {
        "api_id": int(api_id),
        "api_hash": api_hash,
        "source": parse_channel_id(source),
        "target": parse_channel_id(target),
        "session_name": session_name
    }
