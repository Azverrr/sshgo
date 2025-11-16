"""
Модуль для настройки shell completion
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional

from .config import ConfigManager
from .utils import Colors, print_colored


class CompletionManager:
    """Управление настройкой shell completion"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def get_sshgo_path(self) -> Path:
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
    
    def create_completion_script(self) -> Path:
        """
        Создает скрипт completion для bash/zsh в системной директории
        
        Требует прав sudo для записи в /usr/share/bash-completion/completions/
        """
        # Используем только системную директорию
        system_completion_dir = Path("/usr/share/bash-completion/completions")
        completion_script = system_completion_dir / "sshgo"
        
        # Проверяем права на запись
        if not system_completion_dir.exists():
            raise PermissionError(f"Директория {system_completion_dir} не существует. Установите bash-completion.")
        
        if not os.access(system_completion_dir, os.W_OK):
            raise PermissionError(
                f"Нет прав на запись в {system_completion_dir}.\n"
                f"Запустите с sudo: sudo sshgo setup-completion"
            )
        
        sshgo_path = self.get_sshgo_path()
        
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
    
    def setup_shell_completion(self, shell_name: str, completion_script: Path) -> bool:
        """
        Настраивает completion для конкретной оболочки
        
        Args:
            shell_name: Имя оболочки ('bash' или 'zsh')
            completion_script: Путь к скрипту completion
        
        Returns:
            True если настройка успешна, False иначе
        """
        # Completion в системной директории - автоматическая загрузка
        print_colored(Colors.GREEN, f"✅ Completion скрипт создан: {completion_script}")
        print_colored(Colors.BLUE, "   Он автоматически загружается в Bash и ZSH")
        
        if shell_name == "zsh":
            print_colored(Colors.YELLOW, "\n💡 Для ZSH убедитесь, что включен bashcompinit:")
            print_colored(Colors.CYAN, "   autoload -U +X bashcompinit && bashcompinit")
            print_colored(Colors.BLUE, "   (обычно уже включен в Oh My Zsh и других конфигах)")
        
        print_colored(Colors.YELLOW, "\n💡 Перезапустите терминал для активации")
        
        return True
    
    def setup_completion(self, setup_all_shells: bool = False) -> bool:
        """
        Настраивает completion для текущей оболочки или всех доступных
        
        Args:
            setup_all_shells: Если True, настраивает для всех доступных оболочек (Bash и ZSH)
        
        Returns:
            True если настройка успешна, False иначе
        """
        # Проверяем, установлен ли пакет (системная установка)
        system_completion = Path("/usr/share/bash-completion/completions/sshgo")
        if system_completion.exists():
            print_colored(Colors.GREEN, "✅ Автодополнение уже настроено автоматически (пакетная установка)")
            print_colored(Colors.BLUE, "   Completion скрипт находится в: /usr/share/bash-completion/completions/sshgo")
            print_colored(Colors.BLUE, "   Он автоматически загружается в Bash и ZSH (через bashcompinit)")
            print_colored(Colors.YELLOW, "   Если автодополнение не работает, перезапустите терминал")
            return True
        
        # Создаем completion скрипт в системной директории (требует sudo)
        try:
            completion_script = self.create_completion_script()
            
            # Определяем текущую оболочку для информационных сообщений
            current_shell = os.environ.get('SHELL', '')
            shell_name = "zsh" if 'zsh' in current_shell else "bash"
            
            if setup_all_shells:
                print_colored(Colors.BLUE, "🔧 Настраиваю автодополнение...")
                # Показываем информацию для всех оболочек
                self.setup_shell_completion("bash", completion_script)
                print()
                self.setup_shell_completion("zsh", completion_script)
            else:
                print_colored(Colors.BLUE, f"🔧 Настраиваю completion для {shell_name.upper()}...")
                self.setup_shell_completion(shell_name, completion_script)
            
            return True
        except Exception as e:
            print_colored(Colors.RED, f"❌ Ошибка при настройке completion: {e}")
            import traceback
            traceback.print_exc()
            return False


# Кэш для списка серверов (для автодополнения)
_server_names_cache: Optional[List[str]] = None
_server_names_cache_file: Optional[str] = None


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

