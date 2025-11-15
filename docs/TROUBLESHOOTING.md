# Решение проблем

## 🔧 Автодополнение не работает

### Проблема: При нажатии Tab показываются файлы вместо серверов

**Причина:** Скрипт автодополнения не загружен или не зарегистрирован.

**Решение:**

1. **Проверьте наличие скрипта:**
   ```bash
   ls -la ~/.bash_completion.d/sshgo-completion.sh
   ```
   Если файла нет, переустановите: `cd sshgo_python && python3 install.py`

2. **Используйте команду для автоматической настройки:**
   ```bash
   sshgo setup-completion
   ```
   Команда автоматически определит оболочку и настроит completion.

3. **Или настройте вручную:**

   **Для Bash:**
   ```bash
   # Перезагрузите completion
   source ~/.bash_completion.d/sshgo-completion.sh
   
   # Проверьте регистрацию
   complete -p | grep sshgo
   # Должно показать: complete -F _sshgo_completion sshgo
   
   # Проверьте, что скрипт подключен в .bashrc
   grep sshgo-completion ~/.bashrc
   # Должна быть строка: source ~/.bash_completion.d/sshgo-completion.sh
   
   # Если нет - добавьте вручную
   echo 'if [ -f ~/.bash_completion.d/sshgo-completion.sh ]; then' >> ~/.bashrc
   echo '    source ~/.bash_completion.d/sshgo-completion.sh' >> ~/.bashrc
   echo 'fi' >> ~/.bashrc
   source ~/.bashrc
   ```

   **Для ZSH:**
   ```bash
   # Перезагрузите completion
   autoload -U +X bashcompinit && bashcompinit
   source ~/.bash_completion.d/sshgo-completion.sh
   
   # Проверьте регистрацию
   complete -p | grep sshgo
   # Должно показать: complete -F _sshgo_completion sshgo
   
   # Проверьте, что скрипт подключен в .zshrc
   grep sshgo-completion ~/.zshrc
   # Должны быть строки:
   # autoload -U +X bashcompinit && bashcompinit
   # source ~/.bash_completion.d/sshgo-completion.sh
   
   # Если нет - добавьте вручную
   echo 'autoload -U +X bashcompinit && bashcompinit' >> ~/.zshrc
   echo 'if [ -f ~/.bash_completion.d/sshgo-completion.sh ]; then' >> ~/.zshrc
   echo '    source ~/.bash_completion.d/sshgo-completion.sh' >> ~/.zshrc
   echo 'fi' >> ~/.zshrc
   source ~/.zshrc
   ```

### Проблема: Показываются команды вместе с серверами

**Причина:** Используется старая регистрация или конфликт с argcomplete.

**Решение:**

1. **Удалите старую регистрацию:**
   ```bash
   complete -r sshgo
   ```

2. **Загрузите правильный скрипт:**
   ```bash
   source ~/.bash_completion.d/sshgo-completion.sh
   ```

3. **Проверьте регистрацию:**
   ```bash
   complete -p | grep sshgo
   ```
   Должно быть: `complete -F _sshgo_completion sshgo`  
   Не должно быть: `_python_argcomplete` или других функций

4. **Если проблема осталась, переустановите:**
   ```bash
   cd sshgo_python
   python3 install.py uninstall
   python3 install.py
   # Для Bash:
   source ~/.bashrc
   # Для ZSH:
   source ~/.zshrc
   ```

### Проблема: Автодополнение не работает в ZSH

**Причина:** В ZSH не включен `bashcompinit` или скрипт не загружен.

**Решение:**

1. **Проверьте наличие `bashcompinit` в `.zshrc`:**
   ```bash
   grep bashcompinit ~/.zshrc
   ```
   Должна быть строка: `autoload -U +X bashcompinit && bashcompinit`

2. **Если нет - используйте команду:**
   ```bash
   sshgo setup-completion
   ```

3. **Или добавьте вручную:**
   ```bash
   echo 'autoload -U +X bashcompinit && bashcompinit' >> ~/.zshrc
   echo 'if [ -f ~/.bash_completion.d/sshgo-completion.sh ]; then' >> ~/.zshrc
   echo '    source ~/.bash_completion.d/sshgo-completion.sh' >> ~/.zshrc
   echo 'fi' >> ~/.zshrc
   source ~/.zshrc
   ```

4. **Проверьте, что completion загружен:**
   ```bash
   complete -p | grep sshgo
   ```
   Должно показать: `complete -F _sshgo_completion sshgo`

## 📁 Проблемы с правами доступа

### Проблема: Нет прав на запись в `.bashrc` или `.zshrc`

**Решение:**

**Для Bash:**
```bash
sudo chown $USER:$USER ~/.bashrc
sudo chmod 644 ~/.bashrc
```

**Для ZSH:**
```bash
sudo chown $USER:$USER ~/.zshrc
sudo chmod 644 ~/.zshrc
```

### Проблема: Нет прав на конфиг

**Решение:**

```bash
chmod 600 ~/.config/sshgo/connections.conf
```

## 🚫 Команда sshgo не найдена

### Проблема: `command not found: sshgo`

**Решение:**

1. Проверьте установку:
   ```bash
   pip3 show sshgo
   ```

2. Проверьте PATH:
   ```bash
   echo $PATH | grep ".local/bin"
   ```

3. Добавьте в PATH:

   **Для Bash:**
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

   **Для ZSH:**
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

4. Проверьте наличие команды:
   ```bash
   ls -la ~/.local/bin/sshgo
   ```

## ❌ Ошибки подключения

### Проблема: `sshpass не установлен`

**Решение:**

```bash
sudo apt-get install sshpass  # Debian/Ubuntu
sudo dnf install sshpass      # Fedora/RHEL
```

### Проблема: Ошибка подключения

**Решение:**

1. Проверьте подключение вручную:
   ```bash
   ssh -v user@host -p port
   ```

2. Проверьте SSH ключи:
   ```bash
   ssh-add -l
   ```

3. Проверьте конфиг:
   ```bash
   sshgo show server1
   ```

## 📝 Проблемы с конфигурацией

### Проблема: Сервер не найден

**Решение:**

1. Проверьте имя в конфиге:
   ```bash
   grep "^server-name|" ~/.config/sshgo/connections.conf
   ```

2. Проверьте формат:
   ```bash
   cat ~/.config/sshgo/connections.conf
   ```

3. Проверьте права:
   ```bash
   ls -la ~/.config/sshgo/connections.conf
   ```

### Проблема: Неправильный формат конфига

**Решение:**

Формат должен быть:
```
name|type|host|port|username|password|extra_params
```

Все поля обязательны (даже если пустые), разделитель - `|`.

## 🔄 Переустановка

Если ничего не помогает:

```bash
# Удаление
cd sshgo_python
python3 install.py uninstall

# Переустановка
python3 install.py
# Для Bash:
source ~/.bashrc
# Для ZSH:
source ~/.zshrc
```

## 🐚 Проблемы с оболочками

### Проблема: Переключился с Bash на ZSH, автодополнение не работает

**Решение:**

1. **Используйте команду для автоматической настройки:**
   ```bash
   sshgo setup-completion
   ```
   Команда определит текущую оболочку (ZSH) и настроит completion.

2. **Или проверьте, что настройки есть в `.zshrc`:**
   ```bash
   grep sshgo-completion ~/.zshrc
   ```
   Если нет - запустите `sshgo setup-completion`

### Проблема: Алиасы не работают после переключения оболочки

**Решение:**

1. **Проверьте, что алиасы есть в текущей оболочке:**
   ```bash
   # Для Bash:
   grep "alias sshl" ~/.bashrc
   
   # Для ZSH:
   grep "alias sshl" ~/.zshrc
   ```

2. **Если нет - переустановите:**
   ```bash
   cd sshgo_python
   python3 install.py
   ```
   Установщик автоматически добавит алиасы в обе оболочки (если файлы существуют).

3. **Перезагрузите конфигурацию:**
   ```bash
   # Для Bash:
   source ~/.bashrc
   
   # Для ZSH:
   source ~/.zshrc
   ```

## 📞 Дополнительная помощь

1. Проверьте логи ошибок
2. Убедитесь в корректности конфигурации
3. Проверьте права доступа к файлам
4. Попробуйте переустановить

