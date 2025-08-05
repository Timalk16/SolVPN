import json
import subprocess
import os
import sys

# --- ПУТИ К ФАЙЛАМ ---
CONFIG_PATH = "/usr/local/etc/xray/config.json"
SERVER_INFO_PATH = "/usr/local/etc/xray/server_info.json"
XRAY_BINARY_PATH = "/usr/local/bin/xray"

def run_command(command):
    """Выполняет команду, возвращает вывод или None."""
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.PIPE).strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Ошибка выполнения команды {' '.join(command)}: {e}")
        return None

def read_json_file(path):
    """Читает и возвращает содержимое JSON файла."""
    if not os.path.exists(path):
        print(f"Ошибка: Файл конфигурации {path} не найден!")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла {path}.")
        return None

def write_json_file(path, data):
    """Записывает данные в JSON файл."""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        print(f"Критическая ошибка записи в файл {path}: {e}")
        return False

def restart_xray():
    """Перезапускает сервис Xray и проверяет статус."""
    print("Перезапуск сервиса Xray...")
    run_command(["systemctl", "restart", "xray"])
    status = run_command(["systemctl", "is-active", "xray"])
    if status == "active":
        print("-> Сервис Xray успешно перезапущен.")
        return True
    else:
        print("-> ВНИМАНИЕ! Сервис Xray не смог запуститься после перезапуска.")
        return False

def generate_vless_link(user_uuid, email):
    """
    Генерирует ссылку VLESS, читая ВСЕ параметры из файлов конфигурации.
    """
    server_info = read_json_file(SERVER_INFO_PATH)
    config = read_json_file(CONFIG_PATH)

    if not server_info or not config:
        return "Не удалось сгенерировать ссылку: отсутствуют файлы конфигурации."

    # Извлекаем все необходимые данные
    server_ip = server_info.get("server_ip")
    public_key = server_info.get("public_key")
    sni = server_info.get("sni")
    short_id = config['inbounds'][0]['streamSettings']['realitySettings']['shortIds'][0]
    
    # Проверяем, что все данные на месте
    if not all([server_ip, public_key, sni, short_id]):
         return "Ошибка: в файлах конфигурации не хватает данных для генерации ссылки."

    link = (
        f"vless://{user_uuid}@{server_ip}:443?"
        f"encryption=none&security=reality&sni={sni}&fp=chrome"
        f"&pbk={public_key}&sid={short_id}&type=tcp&flow=xtls-rprx-vision"
        f"#{email}"
    )
    return link

def add_user(email):
    """Добавляет нового пользователя в config.json."""
    config = read_json_file(CONFIG_PATH)
    if not config: return

    # Проверяем, не существует ли уже пользователь с таким email
    for client in config['inbounds'][0]['settings']['clients']:
        if client.get("email") == email:
            print(f"Ошибка: Пользователь с email '{email}' уже существует.")
            return

    # Генерируем новый UUID
    user_uuid = run_command([XRAY_BINARY_PATH, "uuid"])
    if not user_uuid:
        print("Не удалось сгенерировать UUID для нового пользователя.")
        return

    new_client = {
        "id": user_uuid,
        "email": email,
        "flow": "xtls-rprx-vision"
    }

    config['inbounds'][0]['settings']['clients'].append(new_client)
    
    if write_json_file(CONFIG_PATH, config) and restart_xray():
        print(f"\n✅ Пользователь '{email}' успешно добавлен.")
        link = generate_vless_link(user_uuid, email)
        print("Ссылка для подключения:")
        print(link)

def remove_user(email):
    """Удаляет пользователя из config.json по email."""
    config = read_json_file(CONFIG_PATH)
    if not config: return

    clients = config['inbounds'][0]['settings']['clients']
    original_user_count = len(clients)
    
    # Создаем новый список без удаляемого пользователя
    clients_after_removal = [client for client in clients if client.get("email") != email]

    if len(clients_after_removal) == original_user_count:
        print(f"Ошибка: Пользователь с email '{email}' не найден.")
        return

    config['inbounds'][0]['settings']['clients'] = clients_after_removal

    if write_json_file(CONFIG_PATH, config) and restart_xray():
        print(f"\n✅ Пользователь '{email}' успешно удален.")

def list_users():
    """Выводит список всех пользователей и их ссылки."""
    config = read_json_file(CONFIG_PATH)
    if not config: return
    
    print("="*50)
    print("Список пользователей:")
    clients = config['inbounds'][0]['settings']['clients']
    if not clients:
        print("Пользователи не найдены.")
    else:
        for client in clients:
            email = client.get('email', 'N/A')
            uuid = client.get('id')
            print(f"\nEmail: {email}")
            print(f"  UUID: {uuid}")
            print(f"  Ссылка: {generate_vless_link(uuid, email)}")
    print("="*50)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python3 manage_users.py add <email>")
        print("  python3 manage_users.py remove <email>")
        print("  python3 manage_users.py list")
        sys.exit(1)

    command = sys.argv[1]
    
    if command == "add":
        if len(sys.argv) < 3:
            print("Ошибка: Укажите email для нового пользователя.")
        else:
            add_user(sys.argv[2])
    elif command == "remove":
        if len(sys.argv) < 3:
            print("Ошибка: Укажите email пользователя для удаления.")
        else:
            remove_user(sys.argv[2])
    elif command == "list":
        list_users()
    else:
        print(f"Неизвестная команда: {command}")