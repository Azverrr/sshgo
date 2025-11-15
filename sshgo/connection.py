"""
Модуль для SSH подключений
"""

import subprocess
import shutil
from typing import Optional
from .config import Server


class SSHConnection:
    """Класс для управления SSH подключениями"""
    
    @staticmethod
    def connect(server: Server) -> int:
        """
        Подключается к серверу через SSH
        
        Args:
            server: Объект Server с параметрами подключения
        
        Returns:
            Код возврата SSH команды
        """
        # Формируем команду SSH
        cmd = ['ssh']
        
        # Добавляем опции
        cmd.extend(['-o', 'StrictHostKeyChecking=no'])
        cmd.extend(['-p', str(server.port)])
        
        # Парсим дополнительные параметры
        if server.extra_params:
            # Используем shlex для безопасного парсинга (учитывает кавычки)
            import shlex
            try:
                extra_parts = shlex.split(server.extra_params)
                for i, part in enumerate(extra_parts):
                    if part == '-o' and i + 1 < len(extra_parts):
                        cmd.extend(['-o', extra_parts[i + 1]])
                    elif part.startswith('-'):
                        cmd.append(part)
            except ValueError:
                # Fallback на простой парсинг если shlex не справился
                extra_parts = server.extra_params.strip().split()
                for i, part in enumerate(extra_parts):
                    if part == '-o' and i + 1 < len(extra_parts):
                        cmd.extend(['-o', extra_parts[i + 1]])
                    elif part.startswith('-'):
                        cmd.append(part)
        
        # Формируем строку подключения
        connection_string = f"{server.username}@{server.host}"
        cmd.append(connection_string)
        
        # Если есть пароль, используем sshpass
        if server.password:
            if not shutil.which('sshpass'):
                print("⚠️  sshpass не установлен. Пароль не будет использован.")
                print("   Установите: sudo apt-get install sshpass")
                # Подключаемся без пароля
                return subprocess.call(cmd)
            
            # Используем sshpass
            sshpass_cmd = ['sshpass', '-p', server.password] + cmd
            return subprocess.call(sshpass_cmd)
        else:
            # Подключаемся без пароля (используем SSH ключи)
            return subprocess.call(cmd)
    
    @staticmethod
    def test_connection(server: Server, timeout: int = 5) -> bool:
        """
        Тестирует подключение к серверу
        
        Args:
            server: Объект Server
            timeout: Таймаут в секундах
        
        Returns:
            True если подключение успешно, False иначе
        """
        cmd = [
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=' + str(timeout),
            '-p', str(server.port),
            '-o', 'BatchMode=yes',  # Не запрашивать пароль
            f"{server.username}@{server.host}",
            'echo "test"'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

