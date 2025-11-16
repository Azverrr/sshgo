"""
Модуль для подключений к серверам
"""

from .base import Connection
from .ssh import SSHConnection
from .rdp import RDPConnection

__all__ = ['Connection', 'SSHConnection', 'RDPConnection']

