import asyncio
import sys
from tg_channel_copier.config import load_config
from tg_channel_copier.client import get_client
from tg_channel_copier.copier import copy_channel


async def main():
    print("==========================================")
    print("       Telegram Channel Copier Tool       ")
    print("==========================================")

    try:
        config = load_config()
    except KeyboardInterrupt:
        print("\n[-] Настройка прервана пользователем.")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Ошибка конфигурации: {e}")
        sys.exit(1)

    client = get_client(
        session_name=config["session_name"],
        api_id=config["api_id"],
        api_hash=config["api_hash"]
    )

    print("[*] Подключение к Telegram...")
    await client.start()
    print("[+] Успешное подключение!")

    try:
        await copy_channel(client, config["source"], config["target"])
    except KeyboardInterrupt:
        print("\n[-] Процесс копирования приостановлен пользователем.")
    except Exception as e:
        print(f"\n[-] Критическая ошибка при работе: {e}")
    finally:
        await client.disconnect()
        print("[*] Сессия закрыта.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[-] Выход...")
