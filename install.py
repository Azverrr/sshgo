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


def check_sudo():
    """Проверяет наличие прав sudo"""
    if os.geteuid() != 0:
        print_colored(Colors.RED, "❌ Для установки требуются права root (sudo)")
        print_colored(Colors.BLUE, "   Запустите: sudo python3 install.py")
        print_colored(Colors.YELLOW, "\n💡 Альтернатива: используйте пакетную установку (DEB/RPM)")
        sys.exit(1)


def check_python_version():
    """Проверяет версию Python"""
    if sys.version_info < (3, 6):
        print_colored(Colors.RED, "❌ Требуется Python 3.6 или выше")
        sys.exit(1)
    print_colored(Colors.GREEN, f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")


def find_pth_files():
    """Находит .pth файлы, содержащие путь к проекту"""
    pth_files = []
    home = Path.home()
    project_dir = Path(__file__).parent.absolute()
    
    # Проверяем пользовательские site-packages
    for site_packages in home.glob(".local/lib/python*/site-packages"):
        for pth_file in site_packages.glob("*.pth"):
            try:
                content = pth_file.read_text()
                if str(project_dir) in content:
                    pth_files.append(pth_file)
            except (IOError, PermissionError):
                pass
    
    return pth_files


def check_existing_installation():
    """Проверяет наличие существующих установок"""
    conflicts = []
    warnings = []
    
    # Проверяем системную установку через пакетный менеджер
    system_sshgo = Path("/usr/bin/sshgo")
    if system_sshgo.exists():
        conflicts.append({
            "type": "DEB/RPM package",
            "path": str(system_sshgo),
            "severity": "high"
        })
    
    # Проверяем системную установку через install.py (старая версия могла установить в ~/.local/bin)
    user_sshgo = Path.home() / ".local" / "bin" / "sshgo"
    if user_sshgo.exists():
        warnings.append(f"Обнаружена старая пользовательская установка: {user_sshgo}")
        warnings.append("Рекомендуется удалить её перед системной установкой")
    
    # Проверяем .pth файлы (режим разработки)
    pth_files = find_pth_files()
    if pth_files:
        conflicts.append({
            "type": "development mode (.pth)",
            "path": ", ".join(str(p) for p in pth_files),
            "severity": "high"
        })
    
    # Проверяем наличие completion скрипта в системной директории
    system_completion = Path("/usr/share/bash-completion/completions/sshgo")
    if system_completion.exists():
        # Completion скрипт уже установлен - это нормально
        pass
    
    return conflicts, warnings


def check_version_conflict():
    """Проверяет версию существующей установки"""
    try:
        # Читаем версию из setup.py
        setup_file = Path(__file__).parent / "setup.py"
        if not setup_file.exists():
            return None, None
        
        content = setup_file.read_text()
        import re
        match = re.search(r'version=["\']([^"\']+)["\']', content)
        if not match:
            return None, None
        
        new_version = match.group(1)
        
        # Пробуем получить версию из установленного пакета через pip
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "sshgo"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Ищем строку Version: в выводе pip show
                for line in result.stdout.splitlines():
                    if line.startswith("Version:"):
                        installed_version = line.split(":", 1)[1].strip()
                        if installed_version != new_version:
                            return installed_version, new_version
                        break
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # Пробуем получить версию из установленного модуля
        try:
            import importlib.util
            # Пробуем загрузить установленный модуль
            spec = importlib.util.find_spec("sshgo")
            if spec and spec.origin:
                # Пробуем прочитать версию из __init__.py или PKG-INFO
                pkg_dir = Path(spec.origin).parent
                pkg_info = pkg_dir.parent / f"sshgo-{new_version}.egg-info" / "PKG-INFO"
                if not pkg_info.exists():
                    # Ищем в dist-packages
                    for dist_dir in Path("/usr/lib/python3").glob("*/dist-packages/sshgo*.egg-info"):
                        pkg_info = dist_dir / "PKG-INFO"
                        if pkg_info.exists():
                            break
                
                if pkg_info.exists():
                    content = pkg_info.read_text()
                    match = re.search(r'^Version:\s*(.+)$', content, re.MULTILINE)
                    if match:
                        installed_version = match.group(1).strip()
                        if installed_version != new_version:
                            return installed_version, new_version
        except (ImportError, AttributeError, IOError):
            pass
            
    except (IOError, PermissionError):
        pass
    
    return None, None


def install_package():
    """Устанавливает пакет через pip (системная установка, требует sudo)"""
    print_colored(Colors.BLUE, "📦 Устанавливаю SSH Connection Manager (системная установка)...")
    
    # Пробуем разные методы установки (все системные, без --user)
    methods = [
        # Метод 1: pip с --break-system-packages (системная установка)
        {
            "name": "pip (системная установка)",
            "cmd": [sys.executable, "-m", "pip", "install", "--break-system-packages", "."],
            "check": lambda: True
        },
        # Метод 2: pip без флагов (если система позволяет)
        {
            "name": "pip (системная установка)",
            "cmd": [sys.executable, "-m", "pip", "install", "."],
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
            system_bin = Path("/usr/local/bin/sshgo")
            if system_bin.exists():
                print_colored(Colors.GREEN, f"✅ Команда sshgo установлена в {system_bin}")
            elif shutil.which("sshgo"):
                print_colored(Colors.GREEN, f"✅ Команда sshgo доступна в PATH")
            return
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # Если все методы не сработали, пробуем прямую установку
    print_colored(Colors.YELLOW, "   Все стандартные методы не сработали, использую прямую установку")
    install_direct()


def install_direct():
    """Устанавливает скрипт напрямую без pip (системная установка)"""
    print_colored(Colors.BLUE, "📦 Устанавливаю напрямую (системная установка)...")
    
    system_bin = Path("/usr/local/bin")
    system_bin.mkdir(parents=True, exist_ok=True)
    
    # Создаем обертку-скрипт
    sshgo_script = system_bin / "sshgo"
    
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


def setup_completion():
    """Настраивает completion в системной директории (автоматически при установке)"""
    print_colored(Colors.BLUE, "🔧 Настраиваю автодополнение...")
    try:
        from sshgo.completion import CompletionManager
        manager = CompletionManager()
        success = manager.setup_completion(setup_all_shells=True)
        if success:
            print_colored(Colors.GREEN, "✅ Автодополнение настроено автоматически!")
        return success
    except ImportError:
        print_colored(Colors.YELLOW, "⚠️  Модуль sshgo не установлен, пропускаю настройку completion")
        print_colored(Colors.BLUE, "   Запустите после установки: sudo sshgo setup-completion")
        return False
    except PermissionError as e:
        print_colored(Colors.RED, f"❌ Ошибка: {e}")
        print_colored(Colors.BLUE, "   Запустите установку с sudo: sudo python3 install.py")
        return False
    except Exception as e:
        print_colored(Colors.YELLOW, f"⚠️  Ошибка при настройке completion: {e}")
        print_colored(Colors.BLUE, "   Запустите после установки: sudo sshgo setup-completion")
        return False


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


def show_usage():
    """Показывает инструкции по использованию"""
    config_file = Path.home() / ".config" / "sshgo" / "connections.conf"
    
    print_colored(Colors.GREEN, "\n🎉 Установка завершена!")
    print_colored(Colors.BLUE, "\n🚀 Готово к использованию!")
    print("• sshgo [Tab Tab]         - быстрое подключение к серверу")
    print("• sshgo                   - интерактивное меню")
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
        print_colored(Colors.YELLOW, "💡 Перезапустите терминал для активации")
    else:
        print_colored(Colors.YELLOW, "💡 Перезапустите терминал для активации")


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
    
    # Проверяем наличие системной установки
    system_sshgo = Path("/usr/bin/sshgo")
    if system_sshgo.exists():
        print_colored(Colors.YELLOW, "⚠️  Обнаружена системная установка через пакетный менеджер")
        print_colored(Colors.BLUE, "   Для удаления используйте: sudo apt remove sshgo (или sudo rpm -e sshgo)")
        print_colored(Colors.BLUE, "   Продолжаю удаление только пользовательской установки...")
    
    # Удаляем egg-link и другие файлы
    import glob
    egg_links = list(Path(home / ".local" / "lib").glob("python*/site-packages/sshgo.egg-link"))
    for egg_link in egg_links:
        egg_link.unlink()
        print_colored(Colors.GREEN, f"✅ Egg-link удален: {egg_link}")
    
    # Удаляем .pth файлы (режим разработки)
    pth_files = find_pth_files()
    for pth_file in pth_files:
        try:
            # Удаляем строку с путем к проекту из .pth файла
            content = pth_file.read_text()
            project_dir = Path(__file__).parent.absolute()
            lines = content.splitlines()
            new_lines = [line for line in lines if str(project_dir) not in line]
            
            if new_lines:
                # Если остались другие строки, обновляем файл
                pth_file.write_text('\n'.join(new_lines) + '\n')
                print_colored(Colors.GREEN, f"✅ Обновлен .pth файл: {pth_file}")
            else:
                # Если файл пустой, удаляем его
                pth_file.unlink()
                print_colored(Colors.GREEN, f"✅ Удален пустой .pth файл: {pth_file}")
        except (IOError, PermissionError) as e:
            print_colored(Colors.YELLOW, f"⚠️  Не удалось обработать .pth файл {pth_file}: {e}")
    
    # Удаляем директории пакета
    site_packages_dirs = list(Path(home / ".local" / "lib").glob("python*/site-packages/sshgo*"))
    for pkg_dir in site_packages_dirs:
        if pkg_dir.is_dir():
            import shutil
            shutil.rmtree(pkg_dir, ignore_errors=True)
            print_colored(Colors.GREEN, f"✅ Директория пакета удалена: {pkg_dir}")
    
    if not removed:
        print_colored(Colors.YELLOW, "⚠️  Пакет удален вручную (pip не смог удалить)")
    
    # Удаляем completion скрипт из системной директории
    system_completion = Path("/usr/share/bash-completion/completions/sshgo")
    if system_completion.exists():
        try:
            system_completion.unlink()
            print_colored(Colors.GREEN, "✅ Completion скрипт удален")
        except PermissionError:
            print_colored(Colors.YELLOW, "⚠️  Не удалось удалить completion скрипт (требуется sudo)")
            print_colored(Colors.BLUE, "   Удалите вручную: sudo rm /usr/share/bash-completion/completions/sshgo")
    
    # Очистка завершена (не требуется очистка конфигов оболочек)
    
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
    check_sudo()  # Проверяем права sudo
    
    # Проверяем наличие существующих установок
    conflicts, warnings = check_existing_installation()
    if conflicts:
        print_colored(Colors.YELLOW, "\n⚠️  Обнаружены существующие установки:")
        for conflict in conflicts:
            print_colored(Colors.YELLOW, f"   • {conflict['type']}: {conflict['path']}")
        
        print_colored(Colors.BLUE, "\n💡 Рекомендации:")
        for conflict in conflicts:
            if conflict['type'] == "DEB/RPM package":
                print_colored(Colors.BLUE, "   • Удалите пакет: sudo apt remove sshgo (или sudo rpm -e sshgo)")
            elif conflict['type'] == "development mode (.pth)":
                print_colored(Colors.BLUE, "   • Удалите .pth файлы вручную или используйте: python3 install.py uninstall")
        
        print()
        response = input("Продолжить установку? (y/N): ").strip().lower()
        if response != 'y':
            print_colored(Colors.YELLOW, "❌ Установка отменена")
            sys.exit(0)
        print()
    
    if warnings:
        for warning in warnings:
            print_colored(Colors.YELLOW, f"⚠️  {warning}")
        print()
    
    # Проверяем версию
    installed_version, new_version = check_version_conflict()
    if installed_version and new_version:
        print_colored(Colors.YELLOW, f"⚠️  Обнаружена установленная версия: {installed_version}")
        print_colored(Colors.BLUE, f"   Устанавливаемая версия: {new_version}")
        if installed_version > new_version:
            print_colored(Colors.YELLOW, "   ⚠️  ВНИМАНИЕ: Вы устанавливаете более старую версию!")
            response = input("Продолжить? (y/N): ").strip().lower()
            if response != 'y':
                print_colored(Colors.YELLOW, "❌ Установка отменена")
                sys.exit(0)
        print()
    
    install_package()
    setup_completion()
    create_config()
    show_usage()


if __name__ == "__main__":
    main()

