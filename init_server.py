import uuid
import subprocess
import json
import os
import shutil
from datetime import datetime

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
CONFIG_PATH = "/usr/local/etc/xray/config.json"
# Файл для хранения информации о сервере, которую мы будем переиспользовать
SERVER_INFO_PATH = "/usr/local/etc/xray/server_info.json"
XRAY_BINARY_PATH = "/usr/local/bin/xray"

# Замените на IP-адрес вашего сервера
SERVER_IP = "77.110.110.205"
# Домен для маскировки трафика
REALITY_DEST_DOMAIN = "www.microsoft.com"
# Имя первого пользователя
INITIAL_USER_EMAIL = "user-01"


def run_command(command):
    """Безопасно выполняет системную команду и возвращает ее вывод."""
    try:
        process = subprocess.run(
            command, capture_output=True, text=True, check=True, encoding='utf-8'
        )
        return process.stdout.strip()
    except FileNotFoundError:
        print(f"Ошибка: Команда не найдена. Убедитесь, что '{command[0]}' установлен и доступен в PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды '{' '.join(command)}':")
        print(e.stderr)
        return None

def generate_new_keys():
    """Генерирует новый UUID и пару ключей REALITY."""
    print("1. Генерация нового UUID...")
    user_uuid = run_command([XRAY_BINARY_PATH, "uuid"])
    if not user_uuid: return None, None, None

    print("2. Генерация новой пары ключей для REALITY...")
    key_output = run_command([XRAY_BINARY_PATH, "x25519"])
    if not key_output: return None, None, None
    
    private_key = key_output.split("\n")[0].split(":")[1].strip()
    public_key = key_output.split("\n")[1].split(":")[1].strip()
    
    print("   -> Ключи успешно сгенерированы.")
    return user_uuid, private_key, public_key

def create_config_json(user_uuid, private_key):
    """Создает структуру нового config.json в виде словаря Python."""
    return {
      "log": {"loglevel": "warning"},
      "inbounds": [{
          "listen": "0.0.0.0", "port": 443, "protocol": "vless",
          "settings": {
            "clients": [{"id": user_uuid, "flow": "xtls-rprx-vision", "email": INITIAL_USER_EMAIL}],
            "decryption": "none"
          },
          "streamSettings": {
            "network": "tcp", "security": "reality",
            "realitySettings": {
              "show": False, "dest": f"{REALITY_DEST_DOMAIN}:443", "xver": 0,
              "serverNames": [REALITY_DEST_DOMAIN],
              "privateKey": private_key,
              "shortIds": [run_command(["openssl", "rand", "-hex", "8"])] # Генерируем случайный shortId
            }
          }
      }],
      "outbounds": [{"protocol": "freedom", "tag": "direct"}]
    }
    
def generate_vless_link(user_uuid, email, public_key):
    """Генерирует полную ссылку для подключения VLESS."""
    config = create_config_json(user_uuid, "dummy") # Создаем временный конфиг для получения данных
    short_id = config['inbounds'][0]['streamSettings']['realitySettings']['shortIds'][0]
    sni = config['inbounds'][0]['streamSettings']['realitySettings']['serverNames'][0]

    link = (
        f"vless://{user_uuid}@{SERVER_IP}:443?"
        f"encryption=none&security=reality&sni={sni}&fp=chrome"
        f"&pbk={public_key}&sid={short_id}&type=tcp&flow=xtls-rprx-vision"
        f"#{email}"
    )
    return link


def main():
    """Основной исполняемый блок скрипта."""
    if os.geteuid() != 0:
        print("Ошибка: Запустите этот скрипт с правами суперпользователя (sudo).")
        return
        
    user_uuid, private_key, public_key = generate_new_keys()
    if not all([user_uuid, private_key, public_key]):
        print("\nНе удалось сгенерировать ключи. Прерывание операции.")
        return

    print("\n3. Остановка службы Xray...")
    run_command(["systemctl", "stop", "xray"])
    
    if os.path.exists(CONFIG_PATH):
        backup_path = f"{CONFIG_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"4. Создание резервной копии старого конфига -> {backup_path}")
        shutil.move(CONFIG_PATH, backup_path)
    
    print("5. Создание нового файла конфигурации...")
    new_config = create_config_json(user_uuid, private_key)
    
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(new_config, f, indent=2)
        print("   -> Новый config.json успешно записан.")
    except IOError as e:
        print(f"   -> КРИТИЧЕСКАЯ ОШИБКА: Не удалось записать файл. {e}")
        return
        
    # --- ВАЖНОЕ ИЗМЕНЕНИЕ: СОХРАНЯЕМ ПАРАМЕТРЫ СЕРВЕРА ---
    print("6. Сохранение информации о сервере для будущего использования...")
    server_info = {
        "server_ip": SERVER_IP,
        "public_key": public_key,
        "sni": REALITY_DEST_DOMAIN
    }
    try:
        with open(SERVER_INFO_PATH, 'w') as f:
            json.dump(server_info, f, indent=2)
        print(f"   -> Информация сохранена в {SERVER_INFO_PATH}")
    except IOError as e:
        print(f"   -> КРИТИЧЕСКАЯ ОШИБКА: Не удалось записать файл info. {e}")
        return

    print("7. Проверка синтаксиса нового конфига...")
    validation_result = run_command([XRAY_BINARY_PATH, "-test", "-config", CONFIG_PATH])
    
    if validation_result and "Configuration OK" in validation_result:
        print("   -> Конфигурация в порядке.")
        print("8. Запуск службы Xray...")
        run_command(["systemctl", "start", "xray"])
        
        status = run_command(["systemctl", "status", "xray"])
        if "active (running)" in status:
             print("   -> Служба Xray успешно запущена!")
        else:
             print("   -> !!! ВНИМАНИЕ: Служба Xray не смогла запуститься.")

    else:
        print("\n   -> !!! КРИТИЧЕСКАЯ ОШИБКА: Новый конфиг не прошел проверку!")
        # Логика восстановления...
        return

    vless_link = generate_vless_link(user_uuid, INITIAL_USER_EMAIL, public_key)
    
    print("\n" + "="*50)
    print("✅ ВСЕ ГОТОВО! СЕРВЕР НАСТРОЕН С НУЛЯ.")
    print("Используйте эту ссылку для подключения в вашем клиенте:")
    print(vless_link)
    print("="*50 + "\n")

if __name__ == "__main__":
    main()