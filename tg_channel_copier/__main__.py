import asyncio
import sys
import qrcode
from telethon.errors import SessionPasswordNeededError
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
    await client.connect()

    # Проверяем, авторизован ли уже клиент под этой сессией
    if not await client.is_user_authorized():
        print("[!] Сессия не авторизована.")
        print("[*] Запуск входа через QR-код (рекомендуемый способ)...")

        try:
            # Инициируем сессию QR-входа
            qr_login = await client.qr_login()

            # Генерация QR-кода для отображения в терминале
            qr = qrcode.QRCode(border=1)
            qr.add_data(qr_login.url)
            qr.make(fit=True)

            print("\n" + "=" * 60)
            print("1. Откройте Telegram на вашем мобильном телефоне.")
            print("2. Перейдите в: Настройки -> Устройства -> Подключить устройство")
            print("   (Settings -> Devices -> Link Desktop Device)")
            print("3. Отсканируйте QR-код ниже:")
            print("=" * 60 + "\n")

            # Отрисовка QR-кода ASCII символами прямо в консоли
            qr.print_ascii(invert=True)
            print("\nОжидание сканирования кода...")

            try:
                # Ожидаем подтверждения входа от пользователя
                await qr_login.wait()
                print("[+] Авторизация по QR-коду успешно завершена!")
            except SessionPasswordNeededError:
                # Если на аккаунте включен 2FA (двухэтапный пароль)
                print("[!] Требуется пароль двухэтапной аутентификации (2FA).")
                password = input("Введите ваш облачный пароль (2FA): ").strip()
                await client.sign_in(password=password)
                print("[+] Успешный вход с использованием пароля 2FA!")

        except Exception as e:
            print(f"[-] Ошибка при авторизации через QR-код: {e}")
            await client.disconnect()
            sys.exit(1)
    else:
        print("[+] Успешное подключение с использованием сохраненной сессии!")

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