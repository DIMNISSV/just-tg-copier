import os
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaWebPage, MessageMediaPoll


async def call_with_retry(func, *args, **kwargs):
    """Оболочка для безопасного вызова функций с обработкой FloodWaitError."""
    while True:
        try:
            return await func(*args, **kwargs)
        except FloodWaitError as e:
            print(f"[!] Превышен лимит запросов. Ожидание {e.seconds + 2} сек...")
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            print(f"[!] Ошибка при выполнении операции отправки: {e}")
            raise e


async def send_album(client: TelegramClient, target, messages_group):
    """Отправляет группу медиафайлов (альбом) с сохранением текста."""
    files = []
    caption = ""
    entities = None

    for msg in messages_group:
        if msg.media:
            files.append(msg.media)
        if msg.message and not caption:
            caption = msg.message
            entities = msg.entities

    print(f"[*] Отправка альбома из {len(files)} элементов...")

    async def _send():
        try:
            # Попытка отправки без скачивания на диск
            await client.send_file(
                target,
                files,
                caption=caption,
                formatting_entities=entities
            )
        except Exception as e:
            print(f"[!] Прямая отправка альбома не удалась ({e}). Скачивание файлов...")
            local_files = []
            for msg in messages_group:
                if msg.media:
                    path = await msg.download_media()
                    if path:
                        local_files.append(path)

            if local_files:
                await client.send_file(
                    target,
                    local_files,
                    caption=caption,
                    formatting_entities=entities
                )
                for path in local_files:
                    if os.path.exists(path):
                        os.remove(path)
            elif caption:
                await client.send_message(target, caption, formatting_entities=entities)

    await call_with_retry(_send)


async def send_single(client: TelegramClient, target, message):
    """Отправляет одиночное сообщение (текст, опрос или медиа)."""
    print(f"[*] Отправка сообщения ID {message.id} ({'Медиа' if message.media else 'Текст'})")

    async def _send():
        if message.media:
            if isinstance(message.media, MessageMediaWebPage):
                await client.send_message(
                    target,
                    message.message,
                    formatting_entities=message.entities
                )
            elif isinstance(message.media, MessageMediaPoll):
                print(f"[-] Сообщение {message.id} — опрос. Пересылка...")
                await client.forward_messages(target, message)
            else:
                try:
                    await client.send_file(
                        target,
                        message.media,
                        caption=message.message,
                        formatting_entities=message.entities
                    )
                except Exception as e:
                    print(f"[!] Прямая отправка медиа не удалась ({e}). Резервное скачивание...")
                    path = await message.download_media()
                    if path:
                        await client.send_file(
                            target,
                            path,
                            caption=message.message,
                            formatting_entities=message.entities
                        )
                        if os.path.exists(path):
                            os.remove(path)
                    elif message.message:
                        await client.send_message(target, message.message, formatting_entities=message.entities)
        else:
            await client.send_message(
                target,
                message.message,
                formatting_entities=message.entities
            )

    await call_with_retry(_send)
