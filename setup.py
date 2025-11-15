"""
Setup script for SSH Connection Manager
"""

from setuptools import setup, find_packages
from pathlib import Path

# Читаем README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="sshgo",
    version="2.0.0",
    description="Удобный менеджер SSH подключений с интерактивным меню",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SSH Connection Manager",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "argcomplete>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "sshgo=sshgo.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
)

