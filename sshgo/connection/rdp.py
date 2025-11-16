"""
Модуль для RDP подключений
"""

import subprocess
import shutil
import socket
from typing import Optional
from .base import Connection
from ..config import Server


class RDPConnection(Connection):
    """Класс для управления RDP подключениями"""
    
    def __init__(self):
        """Определяет доступный RDP клиент"""
        self.rdp_client = self._find_rdp_client()
    
    def _find_rdp_client(self) -> Optional[str]:
        """
        Находит доступный RDP клиент
        
        Returns:
            Имя команды клиента или None
        """
        # Приоритет клиентов: xfreerdp предпочтительнее
        clients = ['xfreerdp', 'rdesktop']
        
        for client in clients:
            if shutil.which(client):
                return client
        
        return None
    
    def connect(self, server: Server) -> int:
        """
        Подключается к серверу через RDP
        
        Args:
            server: Объект Server с параметрами подключения
        
        Returns:
            Код возврата RDP команды
        """
        if not self.rdp_client:
            print("❌ RDP клиент не найден!")
            print("   Установите один из:")
            print("   • xfreerdp: sudo apt-get install freerdp2-x11")
            print("   • rdesktop: sudo apt-get install rdesktop")
            return 1
        
        # Формируем команду в зависимости от клиента
        if self.rdp_client == 'xfreerdp':
            return self._connect_xfreerdp(server)
        elif self.rdp_client == 'rdesktop':
            return self._connect_rdesktop(server)
        
        return 1
    
    def _connect_xfreerdp(self, server: Server) -> int:
        """Подключение через xfreerdp"""
        cmd = ['xfreerdp']
        
        # Базовые параметры (xfreerdp требует параметры как один аргумент)
        cmd.append(f'/v:{server.host}:{server.port}')
        cmd.append(f'/u:{server.username}')
        
        # Пароль
        if server.password:
            cmd.append(f'/p:{server.password}')
        
        # Дополнительные параметры
        if server.extra_params:
            import shlex
            try:
                extra_parts = shlex.split(server.extra_params)
                cmd.extend(extra_parts)
            except ValueError:
                extra_parts = server.extra_params.strip().split()
                cmd.extend(extra_parts)
        else:
            # Параметры по умолчанию для xfreerdp
            cmd.extend(['/cert:ignore', '/dynamic-resolution'])
        
        # Запускаем xfreerdp в фоновом режиме, чтобы не блокировать консоль
        # Для GUI приложений нужно запускать независимо от терминала
        with open('/dev/null', 'w') as devnull:
            process = subprocess.Popen(
                cmd,
                stdout=devnull,
                stderr=devnull,
                stdin=devnull,
                start_new_session=True  # Создаем новую сессию, независимую от терминала
            )
            # Не ждем завершения - возвращаем управление консоли сразу
            return 0
    
    def _connect_rdesktop(self, server: Server) -> int:
        """Подключение через rdesktop"""
        cmd = ['rdesktop']
        
        # Базовые параметры
        cmd.extend(['-g', '1024x768'])  # Разрешение по умолчанию
        cmd.extend(['-u', server.username])
        
        # Пароль
        if server.password:
            cmd.extend(['-p', server.password])
        
        # Хост и порт
        cmd.append(f"{server.host}:{server.port}")
        
        # Дополнительные параметры
        if server.extra_params:
            import shlex
            try:
                extra_parts = shlex.split(server.extra_params)
                cmd.extend(extra_parts)
            except ValueError:
                extra_parts = server.extra_params.strip().split()
                cmd.extend(extra_parts)
        
        # Запускаем rdesktop в фоновом режиме, чтобы не блокировать консоль
        # Для GUI приложений нужно запускать независимо от терминала
        with open('/dev/null', 'w') as devnull:
            process = subprocess.Popen(
                cmd,
                stdout=devnull,
                stderr=devnull,
                stdin=devnull,
                start_new_session=True  # Создаем новую сессию, независимую от терминала
            )
            # Не ждем завершения - возвращаем управление консоли сразу
            return 0
    
    def test_connection(self, server: Server, timeout: int = 5) -> bool:
        """
        Тестирует подключение к RDP серверу
        
        Args:
            server: Объект Server
            timeout: Таймаут в секундах
        
        Returns:
            True если подключение успешно, False иначе
        """
        # Для RDP тестирование - проверка доступности порта
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((server.host, server.port))
            sock.close()
            return result == 0
        except Exception:
            return False

