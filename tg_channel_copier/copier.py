import asyncio
from telethon import TelegramClient
from tg_channel_copier.state import get_last_copied_id, save_last_copied_id
from tg_channel_copier.sender import send_album, send_single


async def copy_channel(client: TelegramClient, source, target):
    print("[*] Получение данных каналов...")
    source_entity = await client.get_entity(source)
    target_entity = await client.get_entity(target)

    source_id = source_entity.id
    last_copied_id = get_last_copied_id(source_id)

    if last_copied_id > 0:
        print(f"[+] Возобновление работы с ID сообщения: {last_copied_id}")
    else:
        print("[*] Начало копирования с самого первого сообщения.")

    total_messages = (await client.get_messages(source_entity, limit=0)).total
    print(f"[*] Всего сообщений в источнике: {total_messages}")

    album_buffer = []
    current_grouped_id = None

    async def flush_album():
        """Вспомогательная функция для очистки буфера альбома."""
        nonlocal current_grouped_id, album_buffer
        if album_buffer:
            await send_album(client, target_entity, album_buffer)
            save_last_copied_id(source_id, album_buffer[-1].id)
            album_buffer = []
            current_grouped_id = None

    # Итерация истории в хронологическом порядке
    async for message in client.iter_messages(source_entity, reverse=True, min_id=last_copied_id):
        if message.action:
            continue

        # Логика накопления альбома
        if message.grouped_id is not None:
            if current_grouped_id is None:
                current_grouped_id = message.grouped_id
                album_buffer.append(message)
            elif message.grouped_id == current_grouped_id:
                album_buffer.append(message)
            else:
                await flush_album()
                current_grouped_id = message.grouped_id
                album_buffer = [message]
            continue

        # Если встретили обычное сообщение — сначала отправляем накопленный альбом
        await flush_album()

        # Отправка обычного сообщения
        await send_single(client, target_entity, message)
        save_last_copied_id(source_id, message.id)

        # Небольшая пауза для снижения нагрузки на API
        await asyncio.sleep(1.0)

    # Отправка остатков альбомов в конце цикла
    await flush_album()

    print("[+] Копирование канала завершено успешно!")
