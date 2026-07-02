from telethon import TelegramClient


def get_client(session_name: str, api_id: int, api_hash: str) -> TelegramClient:
    return TelegramClient(session_name, api_id, api_hash)
