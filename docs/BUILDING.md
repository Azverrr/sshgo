# Сборка пакетов

Это руководство поможет вам собрать DEB или RPM пакеты для распространения SSH Connection Manager.

## 📦 DEB пакет (Debian/Ubuntu)

### Требования

```bash
sudo apt-get install build-essential devscripts debhelper dh-python python3-all
```

### Сборка

```bash
cd sshgo_python
make -f Makefile.build deb
```

Результат: `../sshgo_2.0.0-1_all.deb`

### Установка

```bash
sudo dpkg -i ../sshgo_2.0.0-1_all.deb
sudo apt-get install -f  # Если есть проблемы с зависимостями
```

Подробнее: см. раздел "DEB пакет" ниже.

## 📦 RPM пакет (Fedora/RHEL/CentOS)

### Требования

```bash
sudo dnf install rpm-build python3-devel
```

### Сборка

```bash
cd sshgo_python
make rpm
```

Результат: `~/rpmbuild/RPMS/noarch/sshgo-2.0.0-1.noarch.rpm`

### Установка

```bash
sudo rpm -ivh ~/rpmbuild/RPMS/noarch/sshgo-2.0.0-1.noarch.rpm
```

Подробнее: см. раздел "RPM пакет" ниже.

## 📤 Распространение пакетов

### Передача другому пользователю

1. Соберите пакет (`make deb` или `make rpm`)
2. Передайте файл `.deb` или `.rpm` пользователю
3. Пользователь устанавливает: `sudo dpkg -i` или `sudo rpm -ivh`

### Создание репозитория

См. разделы "Создание репозитория" в соответствующих секциях.

---

## DEB пакет (подробно)

### Быстрая сборка

```bash
cd sshgo_python
make -f Makefile.build deb
```

### Ручная сборка (без Makefile)

Если хотите собрать вручную без Makefile:

```bash
cd sshgo_python
dpkg-buildpackage -b -uc -us
```

**Результат:** `../sshgo_2.0.0-1_all.deb` (в родительской директории)

### Проверка пакета

```bash
dpkg -I ../sshgo_2.0.0-1_all.deb
dpkg -c ../sshgo_2.0.0-1_all.deb
```

### Удаление

```bash
sudo apt remove sshgo
```

---

## RPM пакет (подробно)

### Быстрая сборка

```bash
cd sshgo_python
make rpm
```

### Ручная сборка (без Makefile)

Если хотите собрать вручную без Makefile:

```bash
# 1. Создайте директории для сборки
mkdir -p ~/rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

# 2. Создайте архив исходников (из родительской директории)
# Замените PROJECT_DIR на имя вашей директории проекта
cd ..
PROJECT_DIR=$(basename $(pwd)/sshgo_python)  # или просто имя директории
tar -czf ~/rpmbuild/SOURCES/sshgo-2.0.0.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    $PROJECT_DIR/

# 3. Скопируйте spec файл
cp $PROJECT_DIR/rpm/sshgo.spec ~/rpmbuild/SPECS/

# 4. Соберите пакет
rpmbuild -ba ~/rpmbuild/SPECS/sshgo.spec
```

**Результат:** `~/rpmbuild/RPMS/noarch/sshgo-2.0.0-1.noarch.rpm`

### Проверка пакета

```bash
rpm -qip ~/rpmbuild/RPMS/noarch/sshgo-2.0.0-1.noarch.rpm
rpm -qlp ~/rpmbuild/RPMS/noarch/sshgo-2.0.0-1.noarch.rpm
```

### Удаление

```bash
sudo rpm -e sshgo
```

---

## 📚 Дополнительная информация

- [Debian Policy Manual](https://www.debian.org/doc/debian-policy/)
- [RPM Packaging Guide](https://rpm-packaging-guide.github.io/)

