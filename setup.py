#!/usr/bin/env python3
"""
Setup script for AI Summariser
"""

from setuptools import setup, find_packages
import os

# Читаем README для описания
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Читаем requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-summariser",
    version="1.0.0",
    author="AI Assistant",
    author_email="support@ai-summariser.com",
    description="Асинхронный сервис для интеллектуальной суммаризации Telegram постов с FreeGPT",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/ai-summariser",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-summariser=ai_summariser.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai summarization telegram freegpt async",
    project_urls={
        "Bug Reports": "https://github.com/your-username/ai-summariser/issues",
        "Source": "https://github.com/your-username/ai-summariser",
        "Documentation": "https://ai-summariser.readthedocs.io/",
    },
) 