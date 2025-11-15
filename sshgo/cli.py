"""
Основной CLI интерфейс
"""

import sys
import os
import argparse
import shutil
from pathlib import Path
from typing import Optional, List
try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False

from .config import ConfigManager, Server
from .connection import SSHConnection
from .menu import Menu
from .utils import (
    Colors, print_colored, validate_server_data,
    read_password_with_confirmation, show_server_summary
)


class SSHGoCLI:
    """Основной класс CLI"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.connection = SSHConnection()
        self.menu = Menu(self.config_manager)
    
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
        
        print(f"Подключаемся к {server.username}@{server.host}:{server.port}...")
        return_code = self.connection.connect(server)
        
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
        print(f"🌐 Хост: {server.host}")
        print(f"🚪 Порт: {server.port}")
        print(f"👤 Пользователь: {server.username}")
        print(f"🔐 Пароль: {'установлен' if server.password else 'не установлен'}")
        print(f"📋 Параметры: {server.extra_params if server.extra_params else '-'}")
        print(f"🔗 Команда подключения: ssh -p {server.port} {server.username}@{server.host}")
    
    def add_server_interactive(self):
        """Интерактивное добавление сервера"""
        print_colored(Colors.BLUE, "🚀 Добавление нового сервера")
        print()
        
        # Ввод данных
        name = input("📝 Имя сервера: ").strip()
        host = input("🌐 Хост (IP/домен): ").strip()
        port_str = input("🚪 Порт [22]: ").strip()
        username = input("👤 Пользователь: ").strip()
        
        # Пароль
        password = read_password_with_confirmation()
        
        extra = input("📋 Дополнительные SSH параметры [необязательно]: ").strip()
        
        # Значения по умолчанию
        try:
            port = int(port_str) if port_str else 22
        except ValueError:
            port = 22
        
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
        print(f"📝 Имя: {server.name}")
        print(f"🌐 Хост: {server.host}")
        print(f"🚪 Порт: {server.port}")
        print(f"👤 Пользователь: {server.username}")
        print(f"🔐 Пароль: {'установлен' if server.password else 'не установлен'}")
        print(f"📋 Параметры: {server.extra_params if server.extra_params else '-'}")
        print()
        print("Введите новые значения (Enter для пропуска):")
        
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
            print(f"Подключаемся к {server.username}@{server.host}:{server.port}...")
            return_code = self.connection.connect(server)
            
            if return_code != 0:
                print_colored(Colors.RED, f"❌ Ошибка подключения (код: {return_code})")
            
            print()
            print(f"Отключились от {server.name}")
            input("Нажмите Enter для продолжения...")
    
    def _get_sshgo_path(self):
        """Определяет путь к sshgo"""
        home = Path.home()
        user_bin = home / ".local" / "bin"
        sshgo_path = user_bin / "sshgo"
        
        if not sshgo_path.exists():
            # Пробуем найти в PATH
            sshgo_cmd = shutil.which("sshgo")
            if sshgo_cmd:
                sshgo_path = Path(sshgo_cmd)
            else:
                sshgo_path = Path("sshgo")  # Будет искать в PATH
        
        return sshgo_path
    
    def _create_completion_script(self):
        """Создает скрипт completion для bash/zsh"""
        home = Path.home()
        bash_completion_dir = home / ".bash_completion.d"
        bash_completion_dir.mkdir(exist_ok=True)
        
        completion_script = bash_completion_dir / "sshgo-completion.sh"
        sshgo_path = self._get_sshgo_path()
        
        with open(completion_script, 'w') as f:
            f.write(f"""# SSH Connection Manager - Auto-completion
# Путь к sshgo: {sshgo_path}

# Функция автодополнения (работает всегда, даже без argcomplete)
_sshgo_completion() {{
    local cur prev
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    
    # Если это первый аргумент после sshgo, предлагаем только серверы
    if [ $COMP_CWORD -eq 1 ]; then
        local config_file="${{SSH_CONFIG_FILE:-$HOME/.config/sshgo/connections.conf}}"
        
        if [ -f "$config_file" ]; then
            local servers=$(grep -v '^#' "$config_file" | grep -v '^$' | cut -d'|' -f1 2>/dev/null | tr '\\n' ' ')
            COMPREPLY=( $(compgen -W "$servers" -- "$cur") )
        else
            COMPREPLY=()
        fi
    # Если это команда remove/edit/show, предлагаем только серверы
    elif [ "$prev" = "remove" ] || [ "$prev" = "rm" ] || [ "$prev" = "edit" ] || [ "$prev" = "show" ]; then
        local config_file="${{SSH_CONFIG_FILE:-$HOME/.config/sshgo/connections.conf}}"
        if [ -f "$config_file" ]; then
            local servers=$(grep -v '^#' "$config_file" | grep -v '^$' | cut -d'|' -f1 2>/dev/null | tr '\\n' ' ')
            COMPREPLY=( $(compgen -W "$servers" -- "$cur") )
        fi
    fi
    
    return 0
}}

# Регистрируем completion
# НЕ используем argcomplete, так как он показывает команды
# Используем только нашу функцию, которая показывает только серверы
complete -F _sshgo_completion sshgo
""")
        
        completion_script.chmod(0o644)
        return completion_script
    
    def _setup_shell_completion(self, shell_name: str, rc_file: Path, completion_script: Path):
        """Настраивает completion для конкретной оболочки"""
        if not rc_file.exists():
            return False
        
        try:
            with open(rc_file, 'r') as f:
                rc_content = f.read()
            
            completion_line = f"source {completion_script}"
            path_line = 'export PATH="$HOME/.local/bin:$PATH"'
            
            needs_update = False
            updates = []
            
            # Проверяем, нужно ли добавить PATH
            if path_line not in rc_content and "$HOME/.local/bin" not in rc_content:
                needs_update = True
                updates.append(f"# Add user bin to PATH\n{path_line}")
            
            # Проверяем, нужно ли добавить completion
            if completion_line not in rc_content:
                needs_update = True
                if shell_name == "zsh":
                    # Для ZSH нужен bashcompinit
                    updates.append(f"""# SSH Connection Manager - Auto-completion
# Enable bash completion compatibility for ZSH
autoload -U +X bashcompinit && bashcompinit
if [ -f {completion_script} ]; then
    source {completion_script}
fi""")
                else:
                    # Для Bash просто source
                    updates.append(f"# SSH Connection Manager - Auto-completion\nif [ -f {completion_script} ]; then\n    source {completion_script}\nfi")
            
            if needs_update:
                try:
                    with open(rc_file, 'a') as f:
                        f.write("\n")
                        for update in updates:
                            f.write(update + "\n")
                    print_colored(Colors.GREEN, f"✅ {rc_file.name} обновлен")
                    return True
                except (PermissionError, IOError) as e:
                    print_colored(Colors.YELLOW, f"⚠️  Не удалось автоматически обновить {rc_file.name}: {e}")
                    print_colored(Colors.BLUE, f"\n📝 Добавьте вручную в ~/{rc_file.name}:")
                    for update in updates:
                        print_colored(Colors.BLUE, f"   {update}")
                    return False
            else:
                print_colored(Colors.YELLOW, f"⚠️  Настройки уже присутствуют в {rc_file.name}")
                return True
        except (PermissionError, IOError) as e:
            print_colored(Colors.YELLOW, f"⚠️  Не удалось прочитать {rc_file.name}: {e}")
            return False
    
    def setup_completion(self):
        """Настраивает completion для текущей оболочки"""
        try:
            home = Path.home()
            completion_script = self._create_completion_script()
            
            # Определяем текущую оболочку
            current_shell = os.environ.get('SHELL', '')
            shell_name = "zsh" if 'zsh' in current_shell else "bash"
            
            # Настраиваем для текущей оболочки
            if shell_name == "zsh":
                rc_file = home / ".zshrc"
            else:
                rc_file = home / ".bashrc"
            
            if not rc_file.exists():
                print_colored(Colors.YELLOW, f"⚠️  {rc_file.name} не найден")
                print_colored(Colors.BLUE, f"   Создайте файл ~/{rc_file.name} и запустите команду снова")
                return
            
            print_colored(Colors.BLUE, f"🔧 Настраиваю completion для {shell_name.upper()}...")
            success = self._setup_shell_completion(shell_name, rc_file, completion_script)
            
            if success:
                print_colored(Colors.GREEN, f"✅ Completion настроен для {shell_name.upper()}!")
                print_colored(Colors.BLUE, f"💡 Выполните: source ~/{rc_file.name}")
            else:
                print_colored(Colors.YELLOW, f"⚠️  Не удалось настроить completion автоматически")
                print_colored(Colors.BLUE, f"   Добавьте вручную в ~/{rc_file.name}:")
                if shell_name == "zsh":
                    print_colored(Colors.BLUE, "   autoload -U +X bashcompinit && bashcompinit")
                print_colored(Colors.BLUE, f"   source {completion_script}")
        except Exception as e:
            print_colored(Colors.RED, f"❌ Ошибка при настройке completion: {e}")
            import traceback
            traceback.print_exc()
    
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


# Кэш для списка серверов (для автодополнения)
_server_names_cache = None
_server_names_cache_file = None

def get_server_names() -> List[str]:
    """Получает список имен серверов для автодополнения (с кэшированием)"""
    global _server_names_cache, _server_names_cache_file
    
    try:
        config_manager = ConfigManager()
        config_file = config_manager.config_file
        
        # Проверяем кэш
        if _server_names_cache is not None and _server_names_cache_file == str(config_file):
            # Проверяем, не изменился ли файл
            if config_file.exists():
                try:
                    mtime = config_file.stat().st_mtime
                    if hasattr(get_server_names, '_cache_mtime') and get_server_names._cache_mtime == mtime:
                        return _server_names_cache
                    get_server_names._cache_mtime = mtime
                except (OSError, AttributeError):
                    pass
        
        # Обновляем кэш
        _server_names_cache = config_manager.get_server_names()
        _server_names_cache_file = str(config_file)
        return _server_names_cache
    except Exception:
        return []


def server_completer(prefix, parsed_args, **kwargs):
    """Completer для автодополнения имен серверов"""
    try:
        server_names = get_server_names()
        # Фильтруем по префиксу если есть
        if prefix:
            return [s for s in server_names if s.startswith(prefix)]
        return server_names
    except Exception:
        return []


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

