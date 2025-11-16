"""
Модуль для интерактивного меню
"""

import os
from typing import List, Optional
from .config import Server, ConfigManager


class Menu:
    """Класс для интерактивного меню выбора сервера"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def clear_screen(self):
        """Очищает экран (безопасная версия)"""
        # Используем ANSI escape код вместо os.system
        print('\033[2J\033[H', end='')
    
    def show_menu(self) -> Optional[Server]:
        """
        Показывает интерактивное меню и возвращает выбранный сервер
        
        Returns:
            Выбранный Server или None если выход
        """
        servers = self.config_manager.get_servers()
        
        if not servers:
            print("❌ Нет подключений в конфиге!")
            return None
        
        while True:
            self.clear_screen()
            print("=" * 40)
            print("      МЕНЕДЖЕР ПОДКЛЮЧЕНИЙ")
            print("=" * 40)
            print()
            
            # Показываем список серверов
            for i, server in enumerate(servers, 1):
                print(f"{i}) {server.name} [{server.type.upper()}]")
                print(f"   {server.username}@{server.host}:{server.port}")
                if server.password:
                    print("   [с паролем]")
                else:
                    print("   [без пароля]")
                print()
            
            print("0) Выход")
            print()
            
            try:
                choice = input(f"Ваш выбор (0-{len(servers)}): ").strip()
                
                if choice == "0":
                    print("Выход...")
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(servers):
                    return servers[choice_num - 1]
                else:
                    print("❌ Неверный выбор!")
                    input("Нажмите Enter для продолжения...")
            except ValueError:
                print("❌ Введите число!")
                input("Нажмите Enter для продолжения...")
            except KeyboardInterrupt:
                print("\nВыход...")
                return None

