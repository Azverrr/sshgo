%define name sshgo
%define version 2.0.0
%define release 1
%define python_version %(python3 -c "import sys; print(sys.version_info.major + sys.version_info.minor/10)")

Summary: SSH Connection Manager - удобный менеджер SSH подключений
Name: %{name}
Version: %{version}
Release: %{release}
License: MIT
Group: Applications/System
Source0: %{name}-%{version}.tar.gz
BuildArch: noarch
BuildRequires: python3-devel
Requires: python3 >= 3.6
Requires: python3-argcomplete

%description
SSH Connection Manager (sshgo) - удобный менеджер SSH подключений 
с интерактивным меню и автодополнением для bash.

Позволяет быстро подключаться к серверам по имени, управлять 
списком серверов и использовать интерактивное меню для выбора.

%prep
%setup -q

%build
# Python пакет не требует компиляции
# Но можно проверить синтаксис
python3 -m py_compile sshgo/*.py

%install
# Создаем директории
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{python3_sitelib}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/bash_completion.d
mkdir -p %{buildroot}%{_sysconfdir}/%{name}

# Копируем Python модули
cp -r sshgo/*.py %{buildroot}%{python3_sitelib}/%{name}/
# Копируем __init__.py если есть
[ -f sshgo/__init__.py ] && cp sshgo/__init__.py %{buildroot}%{python3_sitelib}/%{name}/ || true

# Создаем исполняемый скрипт
cat > %{buildroot}%{_bindir}/sshgo << 'EOF'
#!/usr/bin/env python3
# SSH Connection Manager
import sys
from sshgo.cli import main

if __name__ == "__main__":
    main()
EOF
chmod 755 %{buildroot}%{_bindir}/sshgo

# Создаем bash completion (кастомный скрипт, показывает только серверы)
cat > %{buildroot}%{_sysconfdir}/bash_completion.d/sshgo << 'EOF'
# SSH Connection Manager - Auto-completion
# Функция автодополнения (показывает только серверы, не команды)
_sshgo_completion() {
    local cur prev
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Если это первый аргумент после sshgo, предлагаем только серверы
    if [ $COMP_CWORD -eq 1 ]; then
        local config_file="${SSH_CONFIG_FILE:-$HOME/.config/sshgo/connections.conf}"
        
        if [ -f "$config_file" ]; then
            local servers=$(grep -v '^#' "$config_file" | grep -v '^$' | cut -d'|' -f1 2>/dev/null | tr '\n' ' ')
            COMPREPLY=( $(compgen -W "$servers" -- "$cur") )
        else
            COMPREPLY=()
        fi
    # Если это команда remove/edit/show, предлагаем только серверы
    elif [ "$prev" = "remove" ] || [ "$prev" = "rm" ] || [ "$prev" = "edit" ] || [ "$prev" = "show" ]; then
        local config_file="${SSH_CONFIG_FILE:-$HOME/.config/sshgo/connections.conf}"
        if [ -f "$config_file" ]; then
            local servers=$(grep -v '^#' "$config_file" | grep -v '^$' | cut -d'|' -f1 2>/dev/null | tr '\n' ' ')
            COMPREPLY=( $(compgen -W "$servers" -- "$cur") )
        fi
    fi
    
    return 0
}

# Регистрируем completion
# НЕ используем argcomplete, так как он показывает команды
# Используем только нашу функцию, которая показывает только серверы
complete -F _sshgo_completion sshgo
EOF
chmod 644 %{buildroot}%{_sysconfdir}/bash_completion.d/sshgo

# Создаем пример конфига
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
cat > %{buildroot}%{_sysconfdir}/%{name}/connections.conf.example << 'EOF'
# SSH Connections Configuration
# Format: name|type|host|port|username|password|extra_params
# Lines starting with # are comments
#
# Examples:
# server1|ssh|192.168.1.10|22|user|mypassword|
# server2|ssh|example.com|2222|admin||
# local|ssh|localhost|22|user||
#
EOF
chmod 644 %{buildroot}%{_sysconfdir}/%{name}/connections.conf.example

%post
# Создаем пользовательский конфиг если не существует
if [ ! -f "$HOME/.config/sshgo/connections.conf" ]; then
    mkdir -p "$HOME/.config/sshgo"
    cp %{_sysconfdir}/%{name}/connections.conf.example "$HOME/.config/sshgo/connections.conf"
    chmod 600 "$HOME/.config/sshgo/connections.conf"
fi

# Добавляем в /etc/bashrc если еще не добавлено
if [ -f /etc/bashrc ]; then
    if ! grep -q "bash_completion.d/sshgo" /etc/bashrc 2>/dev/null; then
        echo "" >> /etc/bashrc
        echo "# SSH Connection Manager - Auto-completion" >> /etc/bashrc
        echo "if [ -f /etc/bash_completion.d/sshgo ]; then" >> /etc/bashrc
        echo "    source /etc/bash_completion.d/sshgo" >> /etc/bashrc
        echo "fi" >> /etc/bashrc
    fi
fi

# Также для /etc/bash.bashrc (Debian/Ubuntu стиль)
if [ -f /etc/bash.bashrc ]; then
    if ! grep -q "bash_completion.d/sshgo" /etc/bash.bashrc 2>/dev/null; then
        echo "" >> /etc/bash.bashrc
        echo "# SSH Connection Manager - Auto-completion" >> /etc/bash.bashrc
        echo "if [ -f /etc/bash_completion.d/sshgo ]; then" >> /etc/bash.bashrc
        echo "    source /etc/bash_completion.d/sshgo" >> /etc/bash.bashrc
        echo "fi" >> /etc/bash.bashrc
    fi
fi

%preun
# Удаление не требуется, но можно добавить очистку

%files
%defattr(-,root,root,-)
%{_bindir}/sshgo
%{python3_sitelib}/%{name}/
%{_sysconfdir}/bash_completion.d/sshgo
%config(noreplace) %{_sysconfdir}/%{name}/connections.conf.example

%changelog
* Wed Dec 18 2024 SSH Connection Manager <sshgo@example.com> - 2.0.0-1
- Initial RPM package for Python version
- SSH Connection Manager with interactive menu
- Bash completion support
- Server management (add, edit, remove, list)

