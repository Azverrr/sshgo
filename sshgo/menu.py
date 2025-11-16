"""
Модуль для интерактивного меню
"""

import os
import sys
import shutil
from typing import List, Optional, Dict, Tuple
from .config import Server, ConfigManager
from .utils import Colors, print_colored

# Попытка импортировать termios (доступен только на Unix-подобных системах)
try:
    import termios
    import tty
    TERMIOS_AVAILABLE = True
except ImportError:
    TERMIOS_AVAILABLE = False


class Menu:
    """Класс для интерактивного меню выбора сервера"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.search_query = ""
        self.selected_type = None  # Выбранный тип подключения
        self.selected_index = 0  # Индекс в выбранном типе
        self.filtered_servers: Dict[str, List[Server]] = {}
        self.scroll_offset = 0  # Смещение для прокрутки
    
    def clear_screen(self):
        """Очищает экран (безопасная версия)"""
        # Используем ANSI escape код вместо os.system
        print('\033[2J\033[H', end='')
    
    def _getch(self) -> str:
        """
        Читает один символ с клавиатуры без Enter
        Поддерживает специальные клавиши (стрелки, Escape и т.д.)
        """
        if not TERMIOS_AVAILABLE:
            return ''
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            
            # Обработка специальных клавиш (стрелки, Escape)
            if ch == '\x1b':  # Escape sequence
                ch = sys.stdin.read(1)
                if ch == '[':
                    ch = sys.stdin.read(1)
                    if ch == 'A':  # Стрелка вверх
                        return 'UP'
                    elif ch == 'B':  # Стрелка вниз
                        return 'DOWN'
                    elif ch == 'C':  # Стрелка вправо
                        return 'RIGHT'
                    elif ch == 'D':  # Стрелка влево
                        return 'LEFT'
            
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def _group_servers_by_type(self, servers: List[Server]) -> Dict[str, List[Server]]:
        """Группирует серверы по типам подключения"""
        grouped = {}
        for server in servers:
            server_type = server.type.lower() if server.type else 'ssh'
            if server_type not in grouped:
                grouped[server_type] = []
            grouped[server_type].append(server)
        return grouped
    
    def _filter_servers(self, servers: List[Server], query: str) -> Dict[str, List[Server]]:
        """Фильтрует серверы по поисковому запросу и группирует по типам"""
        if not query:
            return self._group_servers_by_type(servers)
        
        query_lower = query.lower()
        filtered = []
        for server in servers:
            # Поиск по имени, хосту, пользователю
            if (query_lower in server.name.lower() or
                query_lower in server.host.lower() or
                query_lower in server.username.lower()):
                filtered.append(server)
        return self._group_servers_by_type(filtered)
    
    def _get_flat_server_list(self, filtered_servers: Dict[str, List[Server]]) -> List[Server]:
        """
        Создает плоский список серверов в правильном порядке (SSH первый)
        
        Returns:
            Плоский список серверов
        """
        flat_list = []
        # SSH всегда первый
        all_types = sorted(filtered_servers.keys())
        types = []
        if 'ssh' in all_types:
            types.append('ssh')
        for t in all_types:
            if t != 'ssh':
                types.append(t)
        
        for server_type in types:
            flat_list.extend(filtered_servers[server_type])
        
        return flat_list
    
    def _handle_number_input(self, filtered_servers: Dict[str, List[Server]], first_digit: str) -> Optional[Server]:
        """
        Обрабатывает ввод номера для быстрого выбора сервера
        
        Args:
            filtered_servers: Отфильтрованные серверы по типам
            first_digit: Первая введенная цифра
        
        Returns:
            Выбранный Server или None
        """
        # Создаем плоский список для нумерации
        flat_list = self._get_flat_server_list(filtered_servers)
        
        if not flat_list:
            return None
        
        # Показываем список с номерами
        self.clear_screen()
        print("=" * 80)
        print("      МЕНЕДЖЕР ПОДКЛЮЧЕНИЙ - ВЫБОР ПО НОМЕРУ")
        print("=" * 80)
        print()
        print(f"🔍 Поиск: {self.search_query if self.search_query else '(введите для поиска)'}")
        print()
        print(f"Введите номер сервера (начали с {first_digit}):")
        print()
        
        # Показываем список с номерами
        # SSH всегда первый
        all_types = sorted(filtered_servers.keys())
        types = []
        if 'ssh' in all_types:
            types.append('ssh')
        for t in all_types:
            if t != 'ssh':
                types.append(t)
        
        current_num = 1
        for server_type in types:
            servers_in_type = filtered_servers[server_type]
            print_colored(Colors.CYAN, f"📁 {server_type.upper()} ({len(servers_in_type)}):")
            print()
            
            for idx, server in enumerate(servers_in_type, 1):
                print(f"{current_num}) {server.name}")
                print(f"   {server.username}@{server.host}:{server.port}")
                if server.password:
                    print_colored(Colors.YELLOW, "   [с паролем]")
                else:
                    print("   [без пароля]")
                print()
                current_num += 1
        
        print("0) Выход")
        print()
        
        # Собираем номер (может быть многоразрядным)
        number_str = first_digit
        
        # Читаем остальные цифры если есть (максимум еще 2 цифры для номеров до 999)
        for _ in range(2):
            try:
                if not TERMIOS_AVAILABLE:
                    break
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    ch = sys.stdin.read(1)
                    if ch.isdigit():
                        number_str += ch
                        # Обновляем отображение
                        self.clear_screen()
                        print("=" * 80)
                        print("      МЕНЕДЖЕР ПОДКЛЮЧЕНИЙ - ВЫБОР ПО НОМЕРУ")
                        print("=" * 80)
                        print()
                        print(f"🔍 Поиск: {self.search_query if self.search_query else '(введите для поиска)'}")
                        print()
                        print(f"Введите номер сервера: {number_str}")
                        print()
                        
                        # Показываем список снова
                        current_num = 1
                        for server_type in types:
                            servers_in_type = filtered_servers[server_type]
                            print_colored(Colors.CYAN, f"📁 {server_type.upper()} ({len(servers_in_type)}):")
                            print()
                            
                            for idx, server in enumerate(servers_in_type, 1):
                                print(f"{current_num}) {server.name}")
                                print(f"   {server.username}@{server.host}:{server.port}")
                                if server.password:
                                    print_colored(Colors.YELLOW, "   [с паролем]")
                                else:
                                    print("   [без пароля]")
                                print()
                                current_num += 1
                        
                        print("0) Выход")
                        print()
                    elif ch == '\r' or ch == '\n':  # Enter
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        break
                    elif ch == '\x1b' or ch == 'q':  # Escape
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        return None
                    elif ch == '\x7f' or ch == '\b':  # Backspace
                        if len(number_str) > 1:
                            number_str = number_str[:-1]
                        else:
                            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                            return None  # Отмена ввода номера
                    else:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        break
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except:
                break
        
        try:
            choice_num = int(number_str)
            if choice_num == 0:
                return None
            
            # Используем плоский список для выбора
            if 1 <= choice_num <= len(flat_list):
                return flat_list[choice_num - 1]  # Возвращаем сервер
        except ValueError:
            pass
        
        return None
    
    def _get_terminal_size(self) -> Tuple[int, int]:
        """
        Получает размер терминала
        
        Returns:
            (ширина, высота) в символах
        """
        try:
            size = shutil.get_terminal_size()
            return size.columns, size.lines
        except:
            # Fallback значения
            return 80, 24
    
    def _get_column_width(self, servers: List[Server]) -> int:
        """Вычисляет ширину колонки на основе самого длинного имени сервера"""
        if not servers:
            return 35
        max_name_len = max(len(s.name) for s in servers)
        max_host_len = max(len(f"{s.username}@{s.host}:{s.port}") for s in servers)
        # Учитываем маркер "▶ " и номер "1) "
        return max(max_name_len + 5, max_host_len + 3, 35)
    
    def _strip_ansi(self, text: str) -> str:
        """Удаляет ANSI коды из строки для правильного подсчета длины"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def _ljust_with_ansi(self, text: str, width: int) -> str:
        """Выравнивает строку по левому краю, учитывая ANSI коды"""
        text_len = len(self._strip_ansi(text))
        if text_len >= width:
            return text
        return text + ' ' * (width - text_len)
    
    def _display_menu(self, filtered_servers: Dict[str, List[Server]], 
                     selected_type: Optional[str], selected_index: int, 
                     search_query: str, scroll_offset: int = 0):
        """Отображает меню с группировкой по колонкам"""
        self.clear_screen()
        
        # Получаем размер терминала
        term_width, term_height = self._get_terminal_size()
        
        # Заголовок и подсказки занимают примерно 6 строк
        header_lines = 6
        # Оставляем место для индикатора прокрутки
        footer_lines = 2
        available_height = term_height - header_lines - footer_lines
        
        print("=" * min(term_width, 80))
        print("      МЕНЕДЖЕР ПОДКЛЮЧЕНИЙ")
        print("=" * min(term_width, 80))
        print()
        
        # Поиск
        print(f"🔍 Поиск: {search_query if search_query else '(введите для поиска)'}")
        print("   ↑↓ - навигация, ←→ - переключение типов, Enter - выбор, Esc - выход")
        print("   Или введите номер сервера для быстрого выбора")
        print()
        
        if not filtered_servers:
            print_colored(Colors.YELLOW, "❌ Нет серверов, соответствующих поисковому запросу")
            print()
            print("Нажмите Esc для выхода")
            return
        
        # Получаем список типов (SSH всегда первый)
        all_types = sorted(filtered_servers.keys())
        types = []
        if 'ssh' in all_types:
            types.append('ssh')
        # Добавляем остальные типы
        for t in all_types:
            if t != 'ssh':
                types.append(t)
        
        # Если тип не выбран, выбираем первый
        if selected_type is None or selected_type not in types:
            selected_type = types[0] if types else None
        
        if selected_type is None:
            return
        
        # Ограничиваем индекс выбранного элемента
        servers_in_type = filtered_servers[selected_type]
        if selected_index >= len(servers_in_type):
            selected_index = len(servers_in_type) - 1
        if selected_index < 0:
            selected_index = 0
        
        # Вычисляем ширину колонок
        column_widths = {}
        for server_type in types:
            column_widths[server_type] = self._get_column_width(filtered_servers[server_type])
        
        # Определяем максимальное количество серверов в любом типе
        max_servers = max(len(servers) for servers in filtered_servers.values()) if filtered_servers else 0
        
        # Вычисляем, сколько серверов можно показать (по 4 строки на сервер: номер, хост, пароль, пустая)
        lines_per_server = 4
        max_visible_servers = max(1, available_height // lines_per_server)
        
        # Вычисляем смещение прокрутки для выбранного типа
        servers_in_selected_type = filtered_servers[selected_type]
        if selected_index < scroll_offset:
            scroll_offset = selected_index
        elif selected_index >= scroll_offset + max_visible_servers:
            scroll_offset = selected_index - max_visible_servers + 1
        
        # Ограничиваем scroll_offset
        if scroll_offset < 0:
            scroll_offset = 0
        if scroll_offset > max(0, len(servers_in_selected_type) - max_visible_servers):
            scroll_offset = max(0, len(servers_in_selected_type) - max_visible_servers)
        
        # Отображаем заголовки колонок
        headers = []
        for server_type in types:
            type_name = server_type.upper()
            width = column_widths[server_type]
            is_selected = (server_type == selected_type)
            
            if is_selected:
                header = f"{Colors.GREEN}▶ {type_name} ({len(filtered_servers[server_type])}){Colors.NC}"
            else:
                header = f"{Colors.CYAN}  {type_name} ({len(filtered_servers[server_type])}){Colors.NC}"
            
            headers.append(self._ljust_with_ansi(header, width))
        
        print("  ".join(headers))
        total_width = sum(column_widths.values()) + (len(types) - 1) * 2
        print("-" * min(total_width, term_width))
        print()
        
        # Отображаем только видимую часть серверов
        start_row = scroll_offset
        end_row = min(start_row + max_visible_servers, max_servers)
        
        for row in range(start_row, end_row):
            # Строка 1: номер и имя
            line1_parts = []
            for server_type in types:
                servers_in_type = filtered_servers[server_type]
                width = column_widths[server_type]
                is_selected_type = (server_type == selected_type)
                
                if row < len(servers_in_type):
                    server = servers_in_type[row]
                    is_selected = (is_selected_type and row == selected_index)
                    
                    if is_selected:
                        marker = "▶"
                        color = Colors.GREEN
                    else:
                        marker = " "
                        color = Colors.NC
                    
                    server_num = row + 1  # Нумерация начинается с 1 для каждого типа
                    server_line = f"{color}{marker} {server_num}) {server.name}{Colors.NC}"
                    
                    # Обрезаем если слишком длинное (учитывая ANSI коды)
                    if len(self._strip_ansi(server_line)) > width:
                        # Оставляем место для "..."
                        max_len = width - 3
                        name_part = server.name[:max_len - len(f"{marker} {server_num}) ")]
                        server_line = f"{color}{marker} {server_num}) {name_part}...{Colors.NC}"
                    
                    line1_parts.append(self._ljust_with_ansi(server_line, width))
                else:
                    line1_parts.append("".ljust(width))
            
            print("  ".join(line1_parts))
            
            # Строка 2: хост и порт
            line2_parts = []
            for server_type in types:
                servers_in_type = filtered_servers[server_type]
                width = column_widths[server_type]
                
                if row < len(servers_in_type):
                    server = servers_in_type[row]
                    server_line = f"   {server.username}@{server.host}:{server.port}"
                    
                    if len(server_line) > width:
                        server_line = server_line[:width-3] + "..."
                    
                    line2_parts.append(server_line.ljust(width))
                else:
                    line2_parts.append("".ljust(width))
            
            print("  ".join(line2_parts))
            
            # Строка 3: пароль
            line3_parts = []
            for server_type in types:
                servers_in_type = filtered_servers[server_type]
                width = column_widths[server_type]
                
                if row < len(servers_in_type):
                    server = servers_in_type[row]
                    if server.password:
                        server_line = f"{Colors.YELLOW}   [с паролем]{Colors.NC}"
                    else:
                        server_line = "   [без пароля]"
                    
                    if len(self._strip_ansi(server_line)) > width:
                        server_line = server_line[:width-3] + "..."
                    
                    line3_parts.append(self._ljust_with_ansi(server_line, width))
                else:
                    line3_parts.append("".ljust(width))
            
            print("  ".join(line3_parts))
            print()  # Пустая строка между рядами
        
        # Показываем индикатор прокрутки если нужно
        servers_in_selected_type = filtered_servers[selected_type]
        if len(servers_in_selected_type) > max_visible_servers:
            visible_start = scroll_offset + 1
            visible_end = min(scroll_offset + max_visible_servers, len(servers_in_selected_type))
            total_in_type = len(servers_in_selected_type)
            print()
            if scroll_offset > 0 and visible_end < total_in_type:
                print_colored(Colors.YELLOW, f"   ↑↓ Показано {visible_start}-{visible_end} из {total_in_type} (прокрутите ↑↓)")
            elif scroll_offset > 0:
                print_colored(Colors.YELLOW, f"   ↑ Показано {visible_start}-{visible_end} из {total_in_type} (прокрутите вверх)")
            elif visible_end < total_in_type:
                print_colored(Colors.YELLOW, f"   ↓ Показано {visible_start}-{visible_end} из {total_in_type} (прокрутите вниз)")
            else:
                print_colored(Colors.CYAN, f"   Показано {visible_start}-{visible_end} из {total_in_type}")
        else:
            print()
        
        print("Нажмите Esc или 'q' для выхода")
        
        # Обновляем scroll_offset в классе
        self.scroll_offset = scroll_offset
    
    def show_menu(self) -> Optional[Server]:
        """
        Показывает интерактивное меню и возвращает выбранный сервер
        
        Returns:
            Выбранный Server или None если выход
        """
        all_servers = self.config_manager.get_servers()
        
        if not all_servers:
            print("❌ Нет подключений в конфиге!")
            return None
        
        self.search_query = ""
        self.selected_type = None
        self.selected_index = 0
        self.scroll_offset = 0
        self.filtered_servers = self._group_servers_by_type(all_servers)
        
        # Проверяем, поддерживается ли терминал для навигации
        use_arrows = TERMIOS_AVAILABLE
        if use_arrows:
            try:
                # Тестируем getch
                test_fd = sys.stdin.fileno()
                test_settings = termios.tcgetattr(test_fd)
            except (termios.error, AttributeError, OSError):
                # Fallback на старый режим, если терминал не поддерживает
                use_arrows = False
        
        if not use_arrows:
            print_colored(Colors.YELLOW, "⚠️  Ваш терминал не поддерживает навигацию стрелками.")
            print_colored(Colors.BLUE, "   Используйте ввод номера сервера для выбора.")
            input("Нажмите Enter для продолжения...")
            # Fallback на простой режим
            return self._show_simple_menu(all_servers)
        
        while True:
            # Обновляем отфильтрованные серверы
            self.filtered_servers = self._filter_servers(all_servers, self.search_query)
            
            if not self.filtered_servers:
                self._display_menu(self.filtered_servers, self.selected_type, self.selected_index, self.search_query)
                try:
                    key = self._getch()
                    
                    if key == '\x1b' or key == 'q':  # Escape или 'q'
                        return None
                    elif key == '\x7f' or key == '\b':  # Backspace
                        if self.search_query:
                            self.search_query = self.search_query[:-1]
                            # Продолжаем цикл, чтобы обновить фильтрацию
                            continue
                    elif key.isprintable() and ord(key) >= 32:  # Печатаемые символы
                        self.search_query += key
                        # Продолжаем цикл, чтобы обновить фильтрацию
                        continue
                    # Игнорируем другие клавиши (стрелки и т.д.)
                except KeyboardInterrupt:
                    return None
                continue
            
            # Убеждаемся, что выбранный тип существует
            # SSH всегда первый
            all_types = sorted(self.filtered_servers.keys())
            types = []
            if 'ssh' in all_types:
                types.append('ssh')
            for t in all_types:
                if t != 'ssh':
                    types.append(t)
            
            if self.selected_type is None or self.selected_type not in types:
                self.selected_type = types[0] if types else None
                self.selected_index = 0
            
            if self.selected_type is None:
                return None
            
            # Ограничиваем индекс
            servers_in_type = self.filtered_servers[self.selected_type]
            if self.selected_index >= len(servers_in_type):
                self.selected_index = len(servers_in_type) - 1
            if self.selected_index < 0:
                self.selected_index = 0
            
            self._display_menu(self.filtered_servers, self.selected_type, self.selected_index, self.search_query, self.scroll_offset)
            
            try:
                key = self._getch()
                
                if key == 'UP':
                    if self.selected_index > 0:
                        self.selected_index -= 1
                        # Автоматическая прокрутка вверх
                        term_width, term_height = self._get_terminal_size()
                        available_height = term_height - 6 - 2
                        lines_per_server = 4
                        max_visible_servers = max(1, available_height // lines_per_server)
                        if self.selected_index < self.scroll_offset:
                            self.scroll_offset = self.selected_index
                elif key == 'DOWN':
                    servers_in_type = self.filtered_servers[self.selected_type]
                    if self.selected_index < len(servers_in_type) - 1:
                        self.selected_index += 1
                        # Автоматическая прокрутка вниз
                        term_width, term_height = self._get_terminal_size()
                        available_height = term_height - 6 - 2
                        lines_per_server = 4
                        max_visible_servers = max(1, available_height // lines_per_server)
                        if self.selected_index >= self.scroll_offset + max_visible_servers:
                            self.scroll_offset = self.selected_index - max_visible_servers + 1
                elif key == 'LEFT':
                    # Переключение на предыдущий тип
                    current_idx = types.index(self.selected_type)
                    if current_idx > 0:
                        self.selected_type = types[current_idx - 1]
                        self.selected_index = 0
                        self.scroll_offset = 0  # Сбрасываем прокрутку при смене типа
                elif key == 'RIGHT':
                    # Переключение на следующий тип
                    current_idx = types.index(self.selected_type)
                    if current_idx < len(types) - 1:
                        self.selected_type = types[current_idx + 1]
                        self.selected_index = 0
                        self.scroll_offset = 0  # Сбрасываем прокрутку при смене типа
                elif key == '\r' or key == '\n':  # Enter
                    if self.filtered_servers and self.selected_type:
                        servers_in_type = self.filtered_servers[self.selected_type]
                        if servers_in_type and 0 <= self.selected_index < len(servers_in_type):
                            return servers_in_type[self.selected_index]
                elif key == '\x1b' or key == 'q':  # Escape или 'q'
                    return None
                elif key == '\x7f' or key == '\b':  # Backspace
                    if self.search_query:
                        self.search_query = self.search_query[:-1]
                        self.selected_index = 0
                        self.scroll_offset = 0  # Сбрасываем прокрутку при изменении поиска
                elif key.isdigit():  # Цифра - быстрый выбор по номеру
                    # Переключаемся в режим ввода номера
                    result = self._handle_number_input(self.filtered_servers, key)
                    if result is not None:
                        return result
                    # Если вернулся None (отмена), продолжаем обычный цикл
                elif key.isprintable() and ord(key) >= 32:  # Печатаемые символы
                    self.search_query += key
                    self.selected_index = 0  # Сбрасываем на первый элемент после поиска
                    self.scroll_offset = 0  # Сбрасываем прокрутку при изменении поиска
                # Игнорируем другие клавиши
            except KeyboardInterrupt:
                return None
    
    def _show_simple_menu(self, all_servers: List[Server]) -> Optional[Server]:
        """Простое меню для терминалов без поддержки стрелок"""
        grouped = self._group_servers_by_type(all_servers)
        
        while True:
            self.clear_screen()
            print("=" * 80)
            print("      МЕНЕДЖЕР ПОДКЛЮЧЕНИЙ")
            print("=" * 80)
            print()
            print_colored(Colors.YELLOW, "⚠️  Используйте простой режим (ввод номера)")
            print()
            
            flat_servers = []
            item_number = 1
            
            # SSH всегда первый
            all_types = sorted(grouped.keys())
            types = []
            if 'ssh' in all_types:
                types.append('ssh')
            for t in all_types:
                if t != 'ssh':
                    types.append(t)
            
            for server_type in types:
                type_name = server_type.upper()
                servers_in_group = grouped[server_type]
                
                print_colored(Colors.CYAN, f"📁 {type_name} ({len(servers_in_group)}):")
                print()
                
                for server in servers_in_group:
                    print(f"{item_number}) {server.name}")
                    print(f"   {server.username}@{server.host}:{server.port}")
                    if server.password:
                        print_colored(Colors.YELLOW, "   [с паролем]")
                    else:
                        print("   [без пароля]")
                    print()
                    flat_servers.append(server)
                    item_number += 1
            
            print("0) Выход")
            print()
            
            try:
                choice = input(f"Ваш выбор (0-{len(flat_servers)}): ").strip()
                
                if choice == "0":
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(flat_servers):
                    return flat_servers[choice_num - 1]
                else:
                    print_colored(Colors.RED, "❌ Неверный выбор!")
                    input("Нажмите Enter для продолжения...")
            except ValueError:
                print_colored(Colors.RED, "❌ Введите число!")
                input("Нажмите Enter для продолжения...")
            except KeyboardInterrupt:
                print("\nВыход...")
                return None
