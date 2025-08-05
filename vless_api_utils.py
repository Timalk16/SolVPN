#!/usr/bin/env python3
"""
Simplified VLESS utilities for API bridge
This version doesn't include telegram dependencies
"""

import os
import json
import logging
import subprocess
import uuid
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Xray configuration paths
CONFIG_PATH = "/usr/local/etc/xray/config.json"
SERVER_INFO_PATH = "/usr/local/etc/xray/server_info.json"
XRAY_BINARY_PATH = "/usr/local/bin/xray"

def run_command(command):
    """Безопасно выполняет системную команду и возвращает ее вывод."""
    try:
        # Use absolute paths for system commands
        if command[0] == 'systemctl':
            command[0] = '/usr/bin/systemctl'
        elif command[0] == 'xray':
            command[0] = '/usr/local/bin/xray'
        
        process = subprocess.run(
            command, capture_output=True, text=True, check=True, encoding='utf-8'
        )
        return process.stdout.strip()
    except FileNotFoundError:
        logger.error(f"Ошибка: Команда не найдена. Убедитесь, что '{command[0]}' установлен и доступен в PATH.")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при выполнении команды '{' '.join(command)}': {e.stderr}")
        return None

def restart_xray():
    """Перезапускает сервис Xray и проверяет статус."""
    logger.info("Перезапуск сервиса Xray...")
    
    # Try to restart Xray service
    restart_result = run_command(["/usr/bin/systemctl", "restart", "xray"])
    if restart_result is None:
        logger.warning("Не удалось перезапустить Xray через systemctl, попробуем альтернативный способ...")
        # Try alternative restart method
        try:
            # Kill existing xray process and start new one
            subprocess.run(["/usr/bin/pkill", "-f", "xray"], capture_output=True)
            subprocess.run(["/usr/local/bin/xray", "-config", CONFIG_PATH], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                         start_new_session=True)
            logger.info("Xray перезапущен альтернативным способом")
            return True
        except Exception as e:
            logger.error(f"Ошибка при альтернативном перезапуске Xray: {e}")
            return False
    
    # Check if service is running
    status = run_command(["/usr/bin/systemctl", "is-active", "xray"])
    if status == "active":
        logger.info("-> Сервис Xray успешно перезапущен.")
        return True
    else:
        logger.warning("-> ВНИМАНИЕ! Сервис Xray не смог запуститься после перезапуска.")
        # Try to start manually
        try:
            subprocess.run(["/usr/local/bin/xray", "-config", CONFIG_PATH], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                         start_new_session=True)
            logger.info("Xray запущен вручную")
            return True
        except Exception as e:
            logger.error(f"Ошибка при ручном запуске Xray: {e}")
            return False

def read_json_file(path):
    """Читает JSON файл и возвращает его содержимое."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {path}: {e}")
        return None

def write_json_file(path, data):
    """Записывает данные в JSON файл."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Ошибка при записи файла {path}: {e}")
        return False

def generate_vless_link_from_config(user_uuid, email):
    """Генерирует VLESS ссылку на основе конфигурации сервера."""
    try:
        # Read server info
        server_info = read_json_file(SERVER_INFO_PATH)
        if not server_info:
            logger.error("Не удалось прочитать server_info.json")
            return None
        
        # Extract server parameters
        server_ip = server_info.get('public_host', '77.110.110.205')
        sni = server_info.get('sni', 'www.github.com')
        short_id = server_info.get('shortId', '0123abcd')
        
        logger.info(f"Генерация VLESS ссылки для пользователя {email} с UUID {user_uuid}")
        logger.info(f"Извлеченные параметры: server_ip={server_ip}, sni={sni}, short_id={short_id}")
        
        # Generate VLESS URI
        vless_uri = f"vless://{user_uuid}@{server_ip}:443?security=reality&sni={sni}&fp=chrome&pbk={server_info.get('publicKey', '')}&sid={short_id}&type=tcp&flow=xtls-rprx-vision#VLESS-{email}"
        
        logger.info(f"Сгенерирована VLESS ссылка: {vless_uri[:50]}...")
        return vless_uri
        
    except Exception as e:
        logger.error(f"Ошибка при генерации VLESS ссылки: {e}")
        return None

def add_user_via_config(email):
    """Добавляет пользователя в конфигурацию Xray."""
    try:
        logger.info(f"Добавление пользователя '{email}' через config.json...")
        
        # Read current config
        config = read_json_file(CONFIG_PATH)
        if not config:
            logger.error("Не удалось прочитать config.json")
            return None
        
        # Find VLESS inbound
        vless_inbound = None
        for inbound in config.get('inbounds', []):
            if inbound.get('protocol') == 'vless':
                vless_inbound = inbound
                break
        
        if not vless_inbound:
            logger.error("VLESS inbound не найден в конфигурации")
            return None
        
        # Generate UUID for user
        user_uuid = str(uuid.uuid4())
        
        # Add user to clients
        if 'settings' not in vless_inbound:
            vless_inbound['settings'] = {}
        if 'clients' not in vless_inbound['settings']:
            vless_inbound['settings']['clients'] = []
        
        # Check if user already exists
        for client in vless_inbound['settings']['clients']:
            if client.get('email') == email:
                logger.error(f"Ошибка: Пользователь с email '{email}' уже существует.")
                return None
        
        # Add new client
        new_client = {
            "id": user_uuid,
            "email": email,
            "flow": "xtls-rprx-vision"
        }
        vless_inbound['settings']['clients'].append(new_client)
        
        # Write updated config
        if write_json_file(CONFIG_PATH, config):
            logger.info(f"Пользователь '{email}' успешно добавлен через config.json.")
            restart_xray()
            return {
                'uuid': user_uuid,
                'email': email
            }
        else:
            logger.error("Ошибка при записи обновленной конфигурации")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при добавлении пользователя через config.json: {e}")
        return None

def remove_user_via_config(email):
    """Удаляет пользователя из конфигурации Xray."""
    try:
        logger.info(f"Удаление пользователя '{email}' из config.json...")
        
        # Read current config
        config = read_json_file(CONFIG_PATH)
        if not config:
            logger.error("Не удалось прочитать config.json")
            return False
        
        # Find VLESS inbound
        vless_inbound = None
        for inbound in config.get('inbounds', []):
            if inbound.get('protocol') == 'vless':
                vless_inbound = inbound
                break
        
        if not vless_inbound:
            logger.error("VLESS inbound не найден в конфигурации")
            return False
        
        # Remove user from clients
        if 'settings' in vless_inbound and 'clients' in vless_inbound['settings']:
            original_count = len(vless_inbound['settings']['clients'])
            vless_inbound['settings']['clients'] = [
                client for client in vless_inbound['settings']['clients']
                if client.get('email') != email
            ]
            
            if len(vless_inbound['settings']['clients']) < original_count:
                # Write updated config
                if write_json_file(CONFIG_PATH, config):
                    logger.info(f"Пользователь '{email}' успешно удален из config.json.")
                    restart_xray()
                    return True
                else:
                    logger.error("Ошибка при записи обновленной конфигурации")
                    return False
            else:
                logger.warning(f"Пользователь '{email}' не найден в конфигурации")
                return False
        else:
            logger.error("Секция clients не найдена в VLESS inbound")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при удалении пользователя из config.json: {e}")
        return False 