"""
Вспомогательные утилиты
"""

import re
from typing import Optional, Tuple
from .config import Server


class Colors:
    """ANSI цветовые коды"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def print_colored(color: str, message: str):
    """Печатает цветное сообщение"""
    print(f"{color}{message}{Colors.NC}")


def validate_server_data(name: str, host: str, port: int, username: str) -> Tuple[bool, Optional[str]]:
    """
    Валидирует данные сервера
    
    Returns:
        (is_valid, error_message)
    """
    # Проверка имени
    if not name or not name.strip():
        return False, "❌ Имя сервера не может быть пустым"
    
    # Проверка хоста
    if not host or not host.strip():
        return False, "❌ Хост не может быть пустым"
    
    # Проверка порта
    if not isinstance(port, int) or port < 1 or port > 65535:
        return False, f"❌ Неверный порт: {port} (должен быть 1-65535)"
    
    # Проверка пользователя
    if not username or not username.strip():
        return False, "❌ Имя пользователя не может быть пустым"
    
    return True, None


def read_password_with_confirmation() -> str:
    """
    Безопасный ввод пароля с подтверждением
    
    Returns:
        Пароль или пустая строка
    """
    import getpass
    
    while True:
        password1 = getpass.getpass("🔐 Пароль (Enter для пропуска): ")
        
        # Если пароль пустой - возвращаем пустой
        if not password1:
            return ""
        
        password2 = getpass.getpass("🔁 Подтвердите пароль: ")
        
        if password1 == password2:
            return password1
        else:
            print_colored(Colors.RED, "❌ Пароли не совпадают. Попробуйте снова.")
            print()


def show_server_summary(server: Server):
    """Показывает сводку информации о сервере"""
    print()
    print_colored(Colors.BLUE, "Подтверждение:")
    print(f"📝 Имя: {server.name}")
    print(f"🌐 Хост: {server.host}:{server.port}")
    print(f"👤 Пользователь: {server.username}")
    
    if server.password:
        print("🔐 Пароль: установлен")
    else:
        print("🔐 Пароль: не установлен")
    
    if server.extra_params:
        print(f"📋 Параметры: {server.extra_params}")
    else:
        print("📋 Параметры: -")
    print()



