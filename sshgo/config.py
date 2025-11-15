"""
Модуль для работы с конфигурацией серверов
"""

import os
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class Server:
    """Класс для представления сервера"""
    name: str
    type: str = "ssh"
    host: str = ""
    port: int = 22
    username: str = ""
    password: str = ""
    extra_params: str = ""
    
    def __str__(self) -> str:
        return f"{self.name}|{self.type}|{self.host}|{self.port}|{self.username}|{self.password}|{self.extra_params}"
    
    @classmethod
    def from_string(cls, line: str) -> Optional['Server']:
        """Создает Server из строки конфига"""
        parts = line.strip().split('|')
        
        # Минимум нужно 6 полей (name, type, host, port, username, password)
        # extra_params может быть пустым
        if len(parts) < 6:
            return None
        
        # Дополняем до 7 полей если нужно
        while len(parts) < 7:
            parts.append("")
        
        try:
            port = int(parts[3]) if parts[3] else 22
        except ValueError:
            port = 22
        
        return cls(
            name=parts[0],
            type=parts[1] if parts[1] else "ssh",
            host=parts[2],
            port=port,
            username=parts[4],
            password=parts[5] if len(parts) > 5 else "",
            extra_params=parts[6] if len(parts) > 6 else ""
        )


class ConfigManager:
    """Менеджер конфигурации серверов"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Инициализация менеджера конфигурации
        
        Args:
            config_file: Путь к файлу конфигурации. 
                        Если None, используется значение из SSH_CONFIG_FILE 
                        или ~/.config/sshgo/connections.conf
        """
        if config_file:
            self.config_file = Path(config_file)
        else:
            config_path = os.environ.get('SSH_CONFIG_FILE')
            if config_path:
                self.config_file = Path(config_path)
            else:
                self.config_file = Path.home() / '.config' / 'sshgo' / 'connections.conf'
        
        # Создаем директорию если не существует
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _read_config(self) -> List[str]:
        """Читает конфиг и возвращает список строк"""
        if not self.config_file.exists():
            return []
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return f.readlines()
    
    def _write_config(self, lines: List[str]):
        """Записывает конфиг"""
        # Устанавливаем правильные права доступа
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Записываем во временный файл, затем переименовываем (атомарная операция)
        temp_file = self.config_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # Устанавливаем права 600
            os.chmod(temp_file, 0o600)
            
            # Атомарная замена
            temp_file.replace(self.config_file)
        except (IOError, OSError) as e:
            # Если ошибка, удаляем временный файл
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def get_servers(self) -> List[Server]:
        """Получает список всех серверов из конфига"""
        servers = []
        lines = self._read_config()
        
        for line in lines:
            line = line.strip()
            # Пропускаем комментарии и пустые строки
            if not line or line.startswith('#'):
                continue
            
            server = Server.from_string(line)
            if server:
                servers.append(server)
        
        return servers
    
    def get_server(self, name: str) -> Optional[Server]:
        """Получает сервер по имени (оптимизированная версия)"""
        if not self.config_file.exists():
            return None
        
        # Читаем построчно до нахождения нужного сервера
        with open(self.config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем комментарии и пустые строки
                if not line or line.startswith('#'):
                    continue
                
                # Проверяем имя сервера без полного парсинга
                if '|' in line:
                    first_part = line.split('|')[0]
                    if first_part == name:
                        # Нашли нужный сервер - парсим его
                        server = Server.from_string(line)
                        if server:
                            return server
        
        return None
    
    def server_exists(self, name: str) -> bool:
        """Проверяет существование сервера (оптимизированная версия)"""
        if not self.config_file.exists():
            return False
        
        # Быстрая проверка по первой части строки
        with open(self.config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '|' in line:
                    first_part = line.split('|')[0]
                    if first_part == name:
                        return True
        
        return False
    
    def add_server(self, server: Server) -> bool:
        """Добавляет сервер в конфиг"""
        if self.server_exists(server.name):
            return False
        
        lines = self._read_config()
        lines.append(f"{server}\n")
        self._write_config(lines)
        return True
    
    def remove_server(self, name: str) -> bool:
        """Удаляет сервер из конфига"""
        if not self.server_exists(name):
            return False
        
        lines = self._read_config()
        new_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            # Пропускаем комментарии и пустые строки
            if not line_stripped or line_stripped.startswith('#'):
                new_lines.append(line)
                continue
            
            server = Server.from_string(line_stripped)
            if server and server.name != name:
                new_lines.append(line)
        
        self._write_config(new_lines)
        return True
    
    def update_server(self, old_name: str, new_server: Server) -> bool:
        """Обновляет сервер в конфиге"""
        if not self.server_exists(old_name):
            return False
        
        # Если имя изменилось, проверяем что новое имя не занято
        if old_name != new_server.name and self.server_exists(new_server.name):
            return False
        
        lines = self._read_config()
        new_lines = []
        updated = False
        
        for line in lines:
            line_stripped = line.strip()
            # Пропускаем комментарии и пустые строки
            if not line_stripped or line_stripped.startswith('#'):
                new_lines.append(line)
                continue
            
            server = Server.from_string(line_stripped)
            if server and server.name == old_name:
                new_lines.append(f"{new_server}\n")
                updated = True
            else:
                new_lines.append(line)
        
        if updated:
            self._write_config(new_lines)
        
        return updated
    
    def get_server_names(self) -> List[str]:
        """Получает список имен серверов (оптимизированная версия)"""
        if not self.config_file.exists():
            return []
        
        names = []
        # Читаем только первую часть строки (имя сервера)
        with open(self.config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '|' in line:
                    name = line.split('|')[0]
                    if name:  # Проверяем что имя не пустое
                        names.append(name)
        
        return names

