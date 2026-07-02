import asyncio
import os
import json
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaWebPage, MessageMediaPoll

STATE_FILE = "copier_state.json"


def get_last_copied_id(source_id: int) -> int:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state.get(str(source_id), 0)
        except Exception:
            pass
    return 0


def save_last_copied_id(source_id: int, last_id: int):
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


async def call_with_retry(func, *args, **kwargs):
    """Оболочка для обработки ограничений Telegram (FloodWaitError)."""
    while True:
        try:
            return await func(*args, **kwargs)
        except FloodWaitError as e:
            print(f"[!] Превышен лимит запросов. Ожидание {e.seconds + 2} сек...")
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            print(f"[!] Ошибка при выполнении операции: {e}")
            raise e


async def send_album(client: TelegramClient, target, messages_group):
    """Копирует группу медиафайлов (альбом) как единое сообщение."""
    files = []
    caption = ""
    entities = None

    for msg in messages_group:
        if msg.media:
            files.append(msg.media)
        if msg.message and not caption:
            caption = msg.message
            entities = msg.entities

    print(f"[*] Копирование альбома из {len(files)} элементов...")

    async def _send():
        try:
            # Пытаемся отправить напрямую из облака Telegram (быстро и без трафика)
            await client.send_file(
                target,
                files,
                caption=caption,
                formatting_entities=entities
            )
        except Exception as e:
            print(f"[!] Не удалось отправить альбом напрямую ({e}). Скачивание локально...")
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
    """Копирует одиночное сообщение (текст или медиа)."""
    print(f"[*] Копирование сообщения ID {message.id} ({'Медиа' if message.media else 'Текст'})")

    async def _send():
        if message.media:
            # Веб-страницы обрабатываем как простой текст с превью
            if isinstance(message.media, MessageMediaWebPage):
                await client.send_message(
                    target,
                    message.message,
                    formatting_entities=message.entities
                )
            elif isinstance(message.media, MessageMediaPoll):
                print(f"[-] Сообщение {message.id} содержит опрос. Пересылаем напрямую...")
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
                    print(f"[!] Прямая отправка медиа не удалась ({e}). Скачивание на диск...")
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


async def copy_channel(client: TelegramClient, source, target):
    print("[*] Получение данных каналов...")
    source_entity = await client.get_entity(source)
    target_entity = await client.get_entity(target)

    source_id = source_entity.id
    last_copied_id = get_last_copied_id(source_id)

    if last_copied_id > 0:
        print(f"[+] Найден сохраненный прогресс. Возобновление работы с ID сообщения: {last_copied_id}")
    else:
        print("[*] Начало копирования с самого первого сообщения.")

    # Получаем общее количество сообщений для ориентира
    total_messages = (await client.get_messages(source_entity, limit=0)).total
    print(f"[*] Всего сообщений в источнике: {total_messages}")

    album_buffer = []
    current_grouped_id = None

    # Итерируем сообщения в хронологическом порядке (reverse=True)
    async for message in client.iter_messages(source_entity, reverse=True, min_id=last_copied_id):
        # Пропускаем служебные сообщения (создание группы, закрепления и т.д.)
        if message.action:
            continue

        # Обработка альбомов (сообщений с одинаковым grouped_id)
        if message.grouped_id is not None:
            if current_grouped_id is None:
                current_grouped_id = message.grouped_id
                album_buffer.append(message)
            elif message.grouped_id == current_grouped_id:
                album_buffer.append(message)
            else:
                # Отправляем предыдущую группу, если началась новая
                await send_album(client, target_entity, album_buffer)
                save_last_copied_id(source_id, album_buffer[-1].id)

                current_grouped_id = message.grouped_id
                album_buffer = [message]
            continue

        # Если в буфере оставался альбом, а текущее сообщение обычное — отправляем альбом
        if album_buffer:
            await send_album(client, target_entity, album_buffer)
            save_last_copied_id(source_id, album_buffer[-1].id)
            album_buffer = []
            current_grouped_id = None

        # Отправка одиночного сообщения
        await send_single(client, target_entity, message)
        save_last_copied_id(source_id, message.id)

        # Небольшая пауза во избежание агрессивных лимитов Telegram
        await asyncio.sleep(1.0)

    # Досылаем оставшийся в буфере альбом в самом конце
    if album_buffer:
        await send_album(client, target_entity, album_buffer)
        save_last_copied_id(source_id, album_buffer[-1].id)

    print("[+] Копирование канала успешно завершено!")
