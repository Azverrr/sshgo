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
        """Создает скрипт completion для bash/zsh"""
        home = Path.home()
        bash_completion_dir = home / ".bash_completion.d"
        bash_completion_dir.mkdir(exist_ok=True)
        
        completion_script = bash_completion_dir / "sshgo-completion.sh"
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
    
    def setup_shell_completion(self, shell_name: str, rc_file: Path, completion_script: Path) -> bool:
        """
        Настраивает completion для конкретной оболочки
        
        Args:
            shell_name: Имя оболочки ('bash' или 'zsh')
            rc_file: Путь к файлу конфигурации (.bashrc или .zshrc)
            completion_script: Путь к скрипту completion
        
        Returns:
            True если настройка успешна, False иначе
        """
        if not rc_file.exists():
            return False
        
        try:
            with open(rc_file, 'r') as f:
                lines = f.readlines()
            
            completion_line = f"source {completion_script}"
            path_line = 'export PATH="$HOME/.local/bin:$PATH"'
            
            # Проверяем наличие настроек более точно
            has_path = False
            has_completion = False
            has_sshgo_comment = False
            completion_block_start = -1
            completion_block_end = -1
            
            for i, line in enumerate(lines):
                # Проверяем PATH
                if path_line in line or ("$HOME/.local/bin" in line and "PATH" in line):
                    has_path = True
                
                # Проверяем наличие блока SSH Connection Manager
                if "SSH Connection Manager" in line:
                    has_sshgo_comment = True
                    completion_block_start = i
                
                # Проверяем completion
                if completion_line in line or ("sshgo-completion" in line and "source" in line):
                    has_completion = True
                    if completion_block_start == -1:
                        completion_block_start = i
                    completion_block_end = i
            
            # Если найден блок, проверяем его полностью
            if completion_block_start >= 0:
                # Проверяем, что блок содержит правильный путь к скрипту
                block_lines = lines[completion_block_start:completion_block_end + 1]
                block_content = ''.join(block_lines)
                if completion_script.name in block_content or "sshgo-completion" in block_content:
                    has_completion = True
            
            needs_update = False
            updates = []
            
            # Проверяем, нужно ли добавить PATH
            if not has_path:
                needs_update = True
                updates.append(f"# Add user bin to PATH\n{path_line}")
            
            # Проверяем, нужно ли добавить completion
            if not has_completion:
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
                    updates.append(f"""# SSH Connection Manager - Auto-completion
if [ -f {completion_script} ]; then
    source {completion_script}
fi""")
            
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
    
    def setup_completion(self, setup_all_shells: bool = False) -> bool:
        """
        Настраивает completion для текущей оболочки или всех доступных
        
        Args:
            setup_all_shells: Если True, настраивает для всех доступных оболочек (Bash и ZSH)
        
        Returns:
            True если настройка успешна, False иначе
        """
        try:
            home = Path.home()
            completion_script = self.create_completion_script()
            
            if setup_all_shells:
                # Настраиваем для всех доступных оболочек
                print_colored(Colors.BLUE, "🔧 Настраиваю автодополнение...")
                print_colored(Colors.GREEN, f"✅ Completion скрипт создан: {completion_script}")
                
                # Настраиваем для Bash
                bashrc = home / ".bashrc"
                if bashrc.exists():
                    print_colored(Colors.BLUE, "   Настраиваю для Bash...")
                    self.setup_shell_completion("bash", bashrc, completion_script)
                else:
                    print_colored(Colors.YELLOW, "   .bashrc не найден, пропускаю настройку для Bash")
                
                # Настраиваем для ZSH
                zshrc = home / ".zshrc"
                if zshrc.exists():
                    print_colored(Colors.BLUE, "   Настраиваю для ZSH...")
                    self.setup_shell_completion("zsh", zshrc, completion_script)
                else:
                    print_colored(Colors.YELLOW, "   .zshrc не найден, пропускаю настройку для ZSH")
                
                # Если ни одна оболочка не настроена, выводим инструкции
                if not bashrc.exists() and not zshrc.exists():
                    print_colored(Colors.YELLOW, "⚠️  Не найдены файлы конфигурации оболочек")
                    print_colored(Colors.BLUE, "\n📝 Добавьте вручную в ваш ~/.bashrc или ~/.zshrc:")
                    print_colored(Colors.BLUE, f"   export PATH=\"$HOME/.local/bin:$PATH\"")
                    if os.environ.get('SHELL', '').endswith('zsh'):
                        print_colored(Colors.BLUE, "   autoload -U +X bashcompinit && bashcompinit")
                    print_colored(Colors.BLUE, f"   source {completion_script}")
                
                return True
            else:
                # Настраиваем только для текущей оболочки
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
                    return False
                
                print_colored(Colors.BLUE, f"🔧 Настраиваю completion для {shell_name.upper()}...")
                success = self.setup_shell_completion(shell_name, rc_file, completion_script)
                
                if success:
                    print_colored(Colors.GREEN, f"✅ Completion настроен для {shell_name.upper()}!")
                    print_colored(Colors.BLUE, f"💡 Выполните: source ~/{rc_file.name}")
                else:
                    print_colored(Colors.YELLOW, f"⚠️  Не удалось настроить completion автоматически")
                    print_colored(Colors.BLUE, f"   Добавьте вручную в ~/{rc_file.name}:")
                    if shell_name == "zsh":
                        print_colored(Colors.BLUE, "   autoload -U +X bashcompinit && bashcompinit")
                    print_colored(Colors.BLUE, f"   source {completion_script}")
                
                return success
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

