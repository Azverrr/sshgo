"""
Базовый класс для подключений
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..config import Server


class Connection(ABC):
    """Абстрактный базовый класс для всех типов подключений"""
    
    @abstractmethod
    def connect(self, server: Server) -> int:
        """
        Подключается к серверу
        
        Args:
            server: Объект Server с параметрами подключения
        
        Returns:
            Код возврата команды подключения
        """
        pass
    
    @abstractmethod
    def test_connection(self, server: Server, timeout: int = 5) -> bool:
        """
        Тестирует подключение к серверу
        
        Args:
            server: Объект Server
            timeout: Таймаут в секундах
        
        Returns:
            True если подключение успешно, False иначе
        """
        pass
    
    @staticmethod
    def create(server: Server) -> 'Connection':
        """
        Фабричный метод для создания нужного типа подключения
        
        Args:
            server: Объект Server с типом подключения
        
        Returns:
            Экземпляр соответствующего класса Connection
        """
        from .ssh import SSHConnection
        from .rdp import RDPConnection
        
        connection_type = server.type.lower() if server.type else 'ssh'
        
        if connection_type == 'rdp':
            return RDPConnection()
        else:  # По умолчанию SSH
            return SSHConnection()

