"""
Основной CLI интерфейс
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional, List
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False

from .config import ConfigManager, Server
from .connection import Connection
from .menu import Menu
from .completion import CompletionManager, get_server_names, server_completer
from .utils import (
    Colors, print_colored, validate_server_data,
    read_password_with_confirmation, show_server_summary
)


class SSHGoCLI:
    """Основной класс CLI"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.menu = Menu(self.config_manager)
        self.completion_manager = CompletionManager()
    
    def list_servers(self):
        """Показывает список серверов"""
        servers = self.config_manager.get_servers()
        
        if not servers:
            print("Нет подключений в конфиге.")
            return
        
        print("Доступные подключения:")
        for server in servers:
            print(f"  • {server.name}")
    
    def connect_by_name(self, name: str):
        """Подключается к серверу по имени"""
        server = self.config_manager.get_server(name)
        
        if not server:
            print_colored(Colors.RED, f"❌ Подключение '{name}' не найдено в конфиге!")
            print("Доступные подключения:")
            for server_name in self.config_manager.get_server_names():
                print(f"  • {server_name}")
            sys.exit(1)
        
        # Создаем нужный тип подключения
        connection = Connection.create(server)
        
        print(f"Подключаемся к {server.username}@{server.host}:{server.port}...")
        return_code = connection.connect(server)
        
        if return_code != 0:
            print_colored(Colors.RED, f"❌ Ошибка подключения (код: {return_code})")
            sys.exit(return_code)
    
    def show_server(self, name: str):
        """Показывает информацию о сервере"""
        server = self.config_manager.get_server(name)
        
        if not server:
            print_colored(Colors.RED, f"❌ Сервер '{name}' не найден")
            return
        
        print_colored(Colors.BLUE, f"📋 Информация о сервере: {name}")
        print()
        print(f"🔌 Тип подключения: {server.type.upper()}")
        print(f"🌐 Хост: {server.host}")
        print(f"🚪 Порт: {server.port}")
        print(f"👤 Пользователь: {server.username}")
        print(f"🔐 Пароль: {'установлен' if server.password else 'не установлен'}")
        print(f"📋 Параметры: {server.extra_params if server.extra_params else '-'}")
        
        # Формируем команду в зависимости от типа
        if server.type.lower() == 'rdp':
            print(f"🔗 Команда подключения: xfreerdp /v:{server.host}:{server.port} /u:{server.username}")
        else:
            print(f"🔗 Команда подключения: ssh -p {server.port} {server.username}@{server.host}")
    
    def add_server_interactive(self):
        """Интерактивное добавление сервера"""
        print_colored(Colors.BLUE, "🚀 Добавление нового сервера")
        print()
        
        # Выбор типа подключения
        print("Тип подключения:")
        print("  1) SSH (по умолчанию)")
        print("  2) RDP")
        type_choice = input("Выберите тип [1]: ").strip()
        
        if type_choice == '2':
            connection_type = 'rdp'
            default_port = 3389  # Стандартный порт RDP
            extra_prompt = "📋 Дополнительные RDP параметры [необязательно]: "
        else:
            connection_type = 'ssh'
            default_port = 22
            extra_prompt = "📋 Дополнительные SSH параметры [необязательно]: "
        
        # Ввод данных
        name = input("📝 Имя сервера: ").strip()
        host = input("🌐 Хост (IP/домен): ").strip()
        port_str = input(f"🚪 Порт [{default_port}]: ").strip()
        username = input("👤 Пользователь: ").strip()
        
        # Пароль
        password = read_password_with_confirmation()
        
        extra = input(extra_prompt).strip()
        
        # Значения по умолчанию
        try:
            port = int(port_str) if port_str else default_port
        except ValueError:
            port = default_port
        
        # Валидация
        is_valid, error = validate_server_data(name, host, port, username)
        if not is_valid:
            print_colored(Colors.RED, error)
            return
        
        # Проверка уникальности
        if self.config_manager.server_exists(name):
            print_colored(Colors.RED, f"❌ Сервер с именем '{name}' уже существует")
            print_colored(Colors.BLUE, "💡 Используйте 'sshgo edit {name}' для редактирования")
            return
        
        # Создаем сервер
        server = Server(
            name=name,
            type=connection_type,
            host=host,
            port=port,
            username=username,
            password=password,
            extra_params=extra
        )
        
        # Подтверждение
        show_server_summary(server)
        confirm = input("Сохранить? [Y/n]: ").strip()
        
        if confirm.lower() in ['n', 'no']:
            print_colored(Colors.RED, "❌ Отменено")
            return
        
        # Сохранение
        if self.config_manager.add_server(server):
            print_colored(Colors.GREEN, f"✅ Сервер {name} добавлен в конфиг!")
        else:
            print_colored(Colors.RED, "❌ Ошибка при добавлении сервера")
    
    def add_server_quick(self, name: str, host: str, username: str, 
                        password: Optional[str] = None, port: int = 22):
        """Быстрое добавление сервера"""
        # Валидация
        is_valid, error = validate_server_data(name, host, port, username)
        if not is_valid:
            print_colored(Colors.RED, error)
            return
        
        # Проверка уникальности
        if self.config_manager.server_exists(name):
            print_colored(Colors.RED, f"❌ Сервер с именем '{name}' уже существует")
            return
        
        server = Server(
            name=name,
            host=host,
            port=port,
            username=username,
            password=password or "",
            extra_params=""
        )
        
        if self.config_manager.add_server(server):
            print_colored(Colors.GREEN, f"✅ Сервер {name} добавлен в конфиг!")
        else:
            print_colored(Colors.RED, "❌ Ошибка при добавлении сервера")
    
    def remove_server(self, name: str):
        """Удаляет сервер"""
        if not name:
            print_colored(Colors.RED, "❌ Использование: sshgo remove <name>")
            return
        
        server = self.config_manager.get_server(name)
        if not server:
            print_colored(Colors.RED, f"❌ Сервер '{name}' не найден")
            return
        
        print(f"❓ Удалить сервер {name} ({server.username}@{server.host}:{server.port})? [y/N]: ", end='')
        confirm = input().strip()
        
        if confirm.lower() not in ['y', 'yes']:
            print_colored(Colors.RED, "❌ Отменено")
            return
        
        if self.config_manager.remove_server(name):
            print_colored(Colors.GREEN, f"✅ Сервер {name} удален из конфига!")
        else:
            print_colored(Colors.RED, "❌ Ошибка при удалении сервера")
    
    def edit_server(self, name: str):
        """Редактирует сервер"""
        if not name:
            print_colored(Colors.RED, "❌ Использование: sshgo edit <name>")
            return
        
        server = self.config_manager.get_server(name)
        if not server:
            print_colored(Colors.RED, f"❌ Сервер '{name}' не найден")
            return
        
        print_colored(Colors.BLUE, f"✏️  Редактирование сервера {name}")
        print()
        print("Текущие значения:")
        print(f"🔌 Тип: {server.type.upper()}")
        print(f"📝 Имя: {server.name}")
        print(f"🌐 Хост: {server.host}")
        print(f"🚪 Порт: {server.port}")
        print(f"👤 Пользователь: {server.username}")
        print(f"🔐 Пароль: {'установлен' if server.password else 'не установлен'}")
        print(f"📋 Параметры: {server.extra_params if server.extra_params else '-'}")
        print()
        print("Введите новые значения (Enter для пропуска):")
        
        # Выбор типа подключения
        print("Тип подключения:")
        print("  1) SSH")
        print("  2) RDP")
        default_choice = 1 if server.type.lower() == 'ssh' else 2
        type_choice = input(f"Выберите тип [{default_choice}]: ").strip()
        if not type_choice:
            new_type = server.type  # Сохраняем текущий тип
        elif type_choice == '2':
            new_type = 'rdp'
        else:
            new_type = 'ssh'
        
        # Ввод новых значений
        new_name = input(f"📝 Имя [{server.name}]: ").strip() or server.name
        new_host = input(f"🌐 Хост [{server.host}]: ").strip() or server.host
        new_port_str = input(f"🚪 Порт [{server.port}]: ").strip()
        new_username = input(f"👤 Пользователь [{server.username}]: ").strip() or server.username
        
        print("🔐 Пароль (Enter для сохранения текущего, 'clear' для очистки):")
        import getpass
        new_password_input = getpass.getpass("   Новый пароль: ")
        
        new_extra = input(f"📋 Параметры [{server.extra_params}]: ").strip() or server.extra_params
        
        # Обработка порта
        try:
            new_port = int(new_port_str) if new_port_str else server.port
        except ValueError:
            new_port = server.port
        
        # Обработка пароля
        if new_password_input == "clear":
            new_password = ""
        elif not new_password_input:
            new_password = server.password
        else:
            new_password = new_password_input
        
        # Валидация
        if new_name != server.name and self.config_manager.server_exists(new_name):
            print_colored(Colors.RED, f"❌ Сервер с именем '{new_name}' уже существует")
            return
        
        is_valid, error = validate_server_data(new_name, new_host, new_port, new_username)
        if not is_valid:
            print_colored(Colors.RED, error)
            return
        
        # Создаем обновленный сервер
        updated_server = Server(
            name=new_name,
            type=new_type,
            host=new_host,
            port=new_port,
            username=new_username,
            password=new_password,
            extra_params=new_extra
        )
        
        # Подтверждение
        show_server_summary(updated_server)
        confirm = input("Сохранить изменения? [Y/n]: ").strip()
        
        if confirm.lower() in ['n', 'no']:
            print_colored(Colors.RED, "❌ Отменено")
            return
        
        # Обновление
        if self.config_manager.update_server(name, updated_server):
            print_colored(Colors.GREEN, f"✅ Сервер {new_name} обновлен!")
        else:
            print_colored(Colors.RED, "❌ Ошибка при обновлении сервера")
    
    def show_menu(self):
        """Показывает интерактивное меню"""
        server = self.menu.show_menu()
        
        if server:
            # Создаем нужный тип подключения
            connection = Connection.create(server)
            
            print(f"Подключаемся к {server.username}@{server.host}:{server.port}...")
            return_code = connection.connect(server)
            
            if return_code != 0:
                print_colored(Colors.RED, f"❌ Ошибка подключения (код: {return_code})")
            
            print()
            print(f"Отключились от {server.name}")
            input("Нажмите Enter для продолжения...")
    
    def setup_completion(self):
        """Настраивает completion для текущей оболочки"""
        self.completion_manager.setup_completion(setup_all_shells=False)
    
    def show_help(self):
        """Показывает справку"""
        print_colored(Colors.BLUE, "🚀 SSH Connection Manager - sshgo")
        print()
        print("Использование:")
        print("  sshgo [команда] [параметры]")
        print()
        print("Команды подключения:")
        print("  sshgo                    - интерактивное меню")
        print("  sshgo <name>             - подключиться к серверу")
        print("  sshgo list               - показать список серверов")
        print()
        print("Управление серверами:")
        print("  sshgo add                - добавить сервер (интерактивно)")
        print("  sshgo add <name> <host> <user> [pass] [port]")
        print("                           - быстрое добавление сервера")
        print("  sshgo edit <name>        - редактировать сервер")
        print("  sshgo remove <name>      - удалить сервер")
        print("  sshgo show <name>        - информация о сервере")
        print()
        print("Другое:")
        print("  sshgo setup-completion   - настроить автодополнение")
        print("  sshgo help               - эта справка")
        print()
        print("Примеры:")
        print("  sshgo add prod-server 192.168.1.10 root mypass 22")
        print("  sshgo edit prod-server")
        print("  sshgo prod-server")




def main():
    """Точка входа"""
    cli = SSHGoCLI()
    
    # Создаем парсер аргументов
    parser = argparse.ArgumentParser(
        description='SSH Connection Manager',
        prog='sshgo'
    )
    
    # Получаем список серверов для автодополнения
    server_names = get_server_names()
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Добавляем позиционный аргумент для имени сервера (для автодополнения)
    # Это будет использоваться когда пользователь просто набирает sshgo <Tab>
    # НО только если нет команды
    server_arg = parser.add_argument(
        'server_name',
        nargs='?',
        help='Имя сервера для подключения (если не указана команда)',
        metavar='SERVER'
    )
    
    # Настраиваем completer для автодополнения серверов
    if ARGCOMPLETE_AVAILABLE:
        server_arg.completer = server_completer
    
    # Команда list
    subparsers.add_parser('list', help='Показать список серверов')
    
    # Команда add
    add_parser = subparsers.add_parser('add', help='Добавить сервер')
    add_parser.add_argument('name', nargs='?', help='Имя сервера')
    add_parser.add_argument('host', nargs='?', help='Хост (IP/домен)')
    add_parser.add_argument('username', nargs='?', help='Имя пользователя')
    add_parser.add_argument('password', nargs='?', help='Пароль')
    add_parser.add_argument('port', nargs='?', type=int, help='Порт (по умолчанию 22)')
    
    # Команда remove
    remove_parser = subparsers.add_parser('remove', aliases=['rm'], help='Удалить сервер')
    if ARGCOMPLETE_AVAILABLE:
        remove_parser.add_argument('name', choices=server_names).completer = server_completer
    else:
        remove_parser.add_argument('name', choices=server_names if server_names else None)
    
    # Команда edit
    edit_parser = subparsers.add_parser('edit', help='Редактировать сервер')
    if ARGCOMPLETE_AVAILABLE:
        edit_parser.add_argument('name', choices=server_names).completer = server_completer
    else:
        edit_parser.add_argument('name', choices=server_names if server_names else None)
    
    # Команда show
    show_parser = subparsers.add_parser('show', help='Информация о сервере')
    if ARGCOMPLETE_AVAILABLE:
        show_parser.add_argument('name', choices=server_names if server_names else None, help='Имя сервера').completer = server_completer
    else:
        show_parser.add_argument('name', help='Имя сервера', choices=server_names if server_names else None)
    
    # Команда setup-completion
    subparsers.add_parser('setup-completion', help='Настроить автодополнение для текущей оболочки')
    
    # Команда help
    subparsers.add_parser('help', help='Показать справку')
    
    # Настройка argcomplete
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)
    
    # Если нет аргументов - показываем меню
    if len(sys.argv) == 1:
        cli.show_menu()
        return
    
    # Список известных команд
    known_commands = ['list', 'add', 'remove', 'rm', 'edit', 'show', 'setup-completion', 'help', '--help', '-h']
    
    # Если первый аргумент не известная команда, проверяем, является ли он именем сервера
    if len(sys.argv) > 1 and sys.argv[1] not in known_commands:
        # Проверяем, является ли это именем сервера
        potential_server_name = sys.argv[1]
        if cli.config_manager.server_exists(potential_server_name):
            # Это имя сервера - подключаемся напрямую
            cli.connect_by_name(potential_server_name)
            return
        # Если не сервер и не команда - пробуем распарсить через argparse
        # (может быть это опция типа --help)
    
    # Парсинг аргументов
    try:
        args = parser.parse_args()
    except SystemExit:
        return
    
    # Обработка команд
    if not args.command:
        # Если нет команды, но есть server_name - подключаемся
        if args.server_name:
            cli.connect_by_name(args.server_name)
        else:
            cli.show_menu()
    elif args.command == 'list':
        cli.list_servers()
    elif args.command == 'add':
        if args.name and args.host and args.username:
            # Быстрое добавление
            cli.add_server_quick(
                args.name,
                args.host,
                args.username,
                args.password,
                args.port or 22
            )
        else:
            # Интерактивное добавление
            cli.add_server_interactive()
    elif args.command in ['remove', 'rm']:
        if args.name:
            cli.remove_server(args.name)
        else:
            print_colored(Colors.RED, "❌ Использование: sshgo remove <name>")
    elif args.command == 'edit':
        if args.name:
            cli.edit_server(args.name)
        else:
            print_colored(Colors.RED, "❌ Использование: sshgo edit <name>")
    elif args.command == 'show':
        if args.name:
            cli.show_server(args.name)
        else:
            print_colored(Colors.RED, "❌ Использование: sshgo show <name>")
    elif args.command == 'setup-completion':
        cli.setup_completion()
    elif args.command == 'help':
        cli.show_help()


if __name__ == "__main__":
    main()

