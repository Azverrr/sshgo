#!/usr/bin/env python3
"""
Скрипт установки SSH Connection Manager (Python версия)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


# Цвета для вывода
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'


def print_colored(color: str, message: str):
    """Печатает цветное сообщение"""
    print(f"{color}{message}{Colors.NC}")


def check_python_version():
    """Проверяет версию Python"""
    if sys.version_info < (3, 6):
        print_colored(Colors.RED, "❌ Требуется Python 3.6 или выше")
        sys.exit(1)
    print_colored(Colors.GREEN, f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")


def install_package():
    """Устанавливает пакет через pip или напрямую"""
    print_colored(Colors.BLUE, "📦 Устанавливаю SSH Connection Manager...")
    
    # Пробуем разные методы установки
    methods = [
        # Метод 1: pipx (лучший вариант для CLI приложений)
        {
            "name": "pipx",
            "cmd": ["pipx", "install", "-e", "."],
            "check": lambda: shutil.which("pipx") is not None
        },
        # Метод 2: pip с --break-system-packages (если пользователь согласен)
        {
            "name": "pip --break-system-packages",
            "cmd": [sys.executable, "-m", "pip", "install", "--break-system-packages", "--user", "-e", "."],
            "check": lambda: True
        },
        # Метод 3: Прямая установка скрипта (без pip)
        {
            "name": "прямая установка",
            "cmd": None,  # Специальная обработка
            "check": lambda: True
        }
    ]
    
    for method in methods:
        if not method["check"]():
            continue
        
        try:
            if method["name"] == "прямая установка":
                # Устанавливаем напрямую без pip
                return install_direct()
            
            print_colored(Colors.YELLOW, f"   Пробую метод: {method['name']}")
            subprocess.check_call(
                method["cmd"],
                cwd=Path.cwd(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print_colored(Colors.GREEN, f"✅ Пакет установлен через {method['name']}")
            
            # Проверяем, что команда доступна
            user_bin = Path.home() / ".local" / "bin"
            if (user_bin / "sshgo").exists():
                print_colored(Colors.GREEN, f"✅ Команда sshgo установлена в {user_bin}/sshgo")
            return
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # Если все методы не сработали, пробуем прямую установку
    print_colored(Colors.YELLOW, "   Все стандартные методы не сработали, использую прямую установку")
    install_direct()


def install_direct():
    """Устанавливает скрипт напрямую без pip"""
    print_colored(Colors.BLUE, "📦 Устанавливаю напрямую (без pip)...")
    
    user_bin = Path.home() / ".local" / "bin"
    user_bin.mkdir(parents=True, exist_ok=True)
    
    # Создаем обертку-скрипт
    sshgo_script = user_bin / "sshgo"
    
    # Определяем путь к модулю
    project_dir = Path(__file__).parent.absolute()
    python_exec = sys.executable
    
    with open(sshgo_script, 'w') as f:
        f.write(f"""#!/usr/bin/env python3
# SSH Connection Manager - Direct installation wrapper
import sys
from pathlib import Path

# Добавляем путь к проекту
project_dir = Path("{project_dir}")
sys.path.insert(0, str(project_dir))

# Запускаем CLI
from sshgo.cli import main
if __name__ == "__main__":
    main()
""")
    
    sshgo_script.chmod(0o755)
    print_colored(Colors.GREEN, f"✅ Скрипт установлен в {sshgo_script}")
    
    # Убеждаемся, что ~/.local/bin в PATH
    if str(user_bin) not in os.environ.get("PATH", ""):
        print_colored(Colors.YELLOW, f"⚠️  Добавьте {user_bin} в PATH")
        print_colored(Colors.BLUE, f"   Добавьте в ~/.bashrc: export PATH=\"$HOME/.local/bin:$PATH\"")


def get_sshgo_path():
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


def create_completion_script():
    """Создает скрипт completion для bash/zsh"""
    home = Path.home()
    bash_completion_dir = home / ".bash_completion.d"
    bash_completion_dir.mkdir(exist_ok=True)
    
    completion_script = bash_completion_dir / "sshgo-completion.sh"
    sshgo_path = get_sshgo_path()
    
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


def setup_shell_completion(shell_name: str, rc_file: Path, completion_script: Path):
    """
    Настраивает completion для конкретной оболочки
    
    Args:
        shell_name: Имя оболочки ('bash' или 'zsh')
        rc_file: Путь к файлу конфигурации (.bashrc или .zshrc)
        completion_script: Путь к скрипту completion
    """
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


def setup_completion():
    """Настраивает completion для всех доступных оболочек"""
    print_colored(Colors.BLUE, "🔧 Настраиваю автодополнение...")
    
    home = Path.home()
    completion_script = create_completion_script()
    print_colored(Colors.GREEN, f"✅ Completion скрипт создан: {completion_script}")
    
    # Настраиваем для Bash
    bashrc = home / ".bashrc"
    if bashrc.exists():
        print_colored(Colors.BLUE, "   Настраиваю для Bash...")
        setup_shell_completion("bash", bashrc, completion_script)
    else:
        print_colored(Colors.YELLOW, "   .bashrc не найден, пропускаю настройку для Bash")
    
    # Настраиваем для ZSH
    zshrc = home / ".zshrc"
    if zshrc.exists():
        print_colored(Colors.BLUE, "   Настраиваю для ZSH...")
        setup_shell_completion("zsh", zshrc, completion_script)
    else:
        print_colored(Colors.YELLOW, "   .zshrc не найден, пропускаю настройку для ZSH")
    
    # Если ни одна оболочка не настроена, выводим инструкции
    if not bashrc.exists() and not zshrc.exists():
        print_colored(Colors.YELLOW, "⚠️  Не найдены файлы конфигурации оболочек")
        print_colored(Colors.BLUE, "\n📝 Добавьте вручную в ваш ~/.bashrc или ~/.zshrc:")
        print_colored(Colors.BLUE, f"   export PATH=\"$HOME/.local/bin:$PATH\"")
        if zshrc.exists() or os.environ.get('SHELL', '').endswith('zsh'):
            print_colored(Colors.BLUE, "   autoload -U +X bashcompinit && bashcompinit")
        print_colored(Colors.BLUE, f"   source {completion_script}")


def create_config():
    """Создает конфигурационный файл если не существует"""
    config_file = Path.home() / ".config" / "sshgo" / "connections.conf"
    
    if config_file.exists():
        print_colored(Colors.YELLOW, f"⚠️  Конфиг уже существует: {config_file}")
        return
    
    print_colored(Colors.BLUE, "📝 Создаю конфигурационный файл...")
    
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write("""# SSH Connections Configuration
# Format: name|type|host|port|username|password|extra_params
# Lines starting with # are comments
#
# Examples:
# server1|ssh|192.168.1.10|22|user|mypassword|
# server2|ssh|example.com|2222|admin||
# local|ssh|localhost|22|user||
#
""")
    
    # Устанавливаем права 600
    os.chmod(config_file, 0o600)
    print_colored(Colors.GREEN, f"✅ Конфиг создан: {config_file}")


def create_aliases_in_rc(rc_file: Path):
    """Создает алиасы в файле конфигурации оболочки"""
    if not rc_file.exists():
        return False
    
    try:
        with open(rc_file, 'r') as f:
            rc_content = f.read()
        
        if "# SSH Connection Manager alias" in rc_content:
            return True  # Алиасы уже есть
        
        try:
            with open(rc_file, 'a') as f:
                f.write("\n# SSH Connection Manager alias\n")
                f.write("alias sshl='sshgo list'\n")
                f.write("alias sshm='sshgo'\n")
                f.write("alias sshctl='sshgo'\n")
            
            return True
        except (PermissionError, IOError) as e:
            print_colored(Colors.YELLOW, f"⚠️  Не удалось создать алиасы в {rc_file.name}: {e}")
            return False
    except (PermissionError, IOError) as e:
        print_colored(Colors.YELLOW, f"⚠️  Не удалось прочитать {rc_file.name}: {e}")
        return False


def create_aliases():
    """Создает алиасы в .bashrc и .zshrc"""
    home = Path.home()
    bashrc = home / ".bashrc"
    zshrc = home / ".zshrc"
    
    aliases_created = False
    
    # Создаем алиасы в Bash
    if bashrc.exists():
        if create_aliases_in_rc(bashrc):
            aliases_created = True
    
    # Создаем алиасы в ZSH
    if zshrc.exists():
        if create_aliases_in_rc(zshrc):
            aliases_created = True
    
    if aliases_created:
        print_colored(Colors.BLUE, "🔗 Создаю удобные алиасы...")
        print_colored(Colors.GREEN, "✅ Алиасы созданы:")
        print_colored(Colors.BLUE, "   • sshl   - показать список серверов")
        print_colored(Colors.BLUE, "   • sshm   - открыть меню")
        print_colored(Colors.BLUE, "   • sshctl - управление серверами")
    elif not bashrc.exists() and not zshrc.exists():
        print_colored(Colors.YELLOW, "⚠️  Не найдены файлы конфигурации оболочек, алиасы не созданы")
        print_colored(Colors.BLUE, "   Добавьте вручную в ~/.bashrc или ~/.zshrc:")
        print_colored(Colors.BLUE, "   alias sshl='sshgo list'")
        print_colored(Colors.BLUE, "   alias sshm='sshgo'")
        print_colored(Colors.BLUE, "   alias sshctl='sshgo'")


def show_usage():
    """Показывает инструкции по использованию"""
    config_file = Path.home() / ".config" / "sshgo" / "connections.conf"
    
    print_colored(Colors.GREEN, "\n🎉 Установка завершена!")
    print_colored(Colors.BLUE, "\n🚀 Готово к использованию!")
    print("• sshgo [Tab Tab]         - быстрое подключение к серверу")
    print("• sshgo                   - интерактивное меню")
    print("• sshl / sshm             - короткие алиасы")
    print()
    print_colored(Colors.BLUE, "📋 Для начала работы:")
    print(f"1. Отредактируйте конфиг: nano {config_file}")
    print("2. Добавьте свои серверы в формате:")
    print("   server1|ssh|192.168.1.10|22|user|password|")
    print("3. Используйте: sshgo list для просмотра списка")
    print()
    # Определяем текущую оболочку
    current_shell = os.environ.get('SHELL', '')
    if 'zsh' in current_shell:
        print_colored(Colors.YELLOW, "💡 Перезагрузите терминал или выполните: source ~/.zshrc")
    else:
        print_colored(Colors.YELLOW, "💡 Перезагрузите терминал или выполните: source ~/.bashrc")


def uninstall():
    """Удаляет установку"""
    print_colored(Colors.YELLOW, "🗑️  Удаляю SSH Connection Manager...")
    
    home = Path.home()
    
    # Удаляем пакет
    removed = False
    try:
        # Пробуем удалить из пользовательской директории
        subprocess.check_call([
            sys.executable, "-m", "pip", "uninstall", "-y", "sshgo"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        removed = True
        print_colored(Colors.GREEN, "✅ Пакет удален через pip")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Удаляем файлы вручную (на случай если pip не справился)
    user_bin = home / ".local" / "bin" / "sshgo"
    if user_bin.exists():
        user_bin.unlink()
        print_colored(Colors.GREEN, "✅ Команда sshgo удалена")
    
    # Удаляем egg-link и другие файлы
    import glob
    egg_links = list(Path(home / ".local" / "lib").glob("python*/site-packages/sshgo.egg-link"))
    for egg_link in egg_links:
        egg_link.unlink()
        print_colored(Colors.GREEN, f"✅ Egg-link удален: {egg_link}")
    
    # Удаляем директории пакета
    site_packages_dirs = list(Path(home / ".local" / "lib").glob("python*/site-packages/sshgo*"))
    for pkg_dir in site_packages_dirs:
        if pkg_dir.is_dir():
            import shutil
            shutil.rmtree(pkg_dir, ignore_errors=True)
            print_colored(Colors.GREEN, f"✅ Директория пакета удалена: {pkg_dir}")
    
    if not removed:
        print_colored(Colors.YELLOW, "⚠️  Пакет удален вручную (pip не смог удалить)")
    
    # Удаляем completion
    completion_script = home / ".bash_completion.d" / "sshgo-completion.sh"
    if completion_script.exists():
        completion_script.unlink()
        print_colored(Colors.GREEN, "✅ Completion скрипт удален")
    
    # Удаляем строки из .bashrc и .zshrc
    def clean_rc_file(rc_file: Path):
        """Очищает файл конфигурации оболочки от настроек sshgo"""
        if not rc_file.exists():
            return False
        
        try:
            with open(rc_file, 'r') as f:
                lines = f.readlines()
            
            new_lines = []
            skip_block = False
            completion_patterns = [
                "sshgo-completion",
                "SSH Connection Manager",
                "alias sshl",
                "alias sshm",
                "alias sshctl",
                "bashcompinit"  # Для ZSH
            ]
            
            for i, line in enumerate(lines):
                # Пропускаем строки, связанные с sshgo
                should_skip = False
                for pattern in completion_patterns:
                    if pattern in line:
                        should_skip = True
                        skip_block = True
                        break
                
                # Пропускаем пустые строки после блока sshgo
                if skip_block and line.strip() == "":
                    continue
                
                # Пропускаем лишние fi после блока sshgo
                if skip_block and line.strip() == "fi" and i > 0:
                    # Проверяем, есть ли соответствующий if выше
                    prev_lines = [l.strip() for l in lines[max(0, i-10):i]]
                    if "if" not in " ".join(prev_lines) or prev_lines.count("if") <= prev_lines.count("fi"):
                        skip_block = False
                        continue
                
                # Завершаем пропуск блока при встрече обычной строки
                if skip_block and line.strip() and not any(p in line for p in completion_patterns):
                    if not line.strip().startswith("fi"):
                        skip_block = False
                
                if not should_skip and not (skip_block and line.strip() == "fi"):
                    new_lines.append(line)
            
            with open(rc_file, 'w') as f:
                f.writelines(new_lines)
            
            return True
        except (PermissionError, IOError) as e:
            print_colored(Colors.YELLOW, f"⚠️  Не удалось очистить {rc_file.name}: {e}")
            return False
    
    # Очищаем .bashrc
    bashrc = home / ".bashrc"
    if bashrc.exists() and clean_rc_file(bashrc):
        print_colored(Colors.GREEN, "✅ .bashrc очищен")
    
    # Очищаем .zshrc
    zshrc = home / ".zshrc"
    if zshrc.exists() and clean_rc_file(zshrc):
        print_colored(Colors.GREEN, "✅ .zshrc очищен")
    
    config_file = home / ".config" / "sshgo" / "connections.conf"
    print_colored(Colors.BLUE, f"📁 Конфиг сохранен: {config_file}")


def main():
    """Главная функция"""
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall()
        return
    
    print_colored(Colors.BLUE, "🚀 Установка SSH Connection Manager (Python версия)")
    print()
    
    check_python_version()
    install_package()
    setup_completion()
    create_config()
    create_aliases()
    show_usage()


if __name__ == "__main__":
    main()

