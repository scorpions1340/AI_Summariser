#!/usr/bin/env python3
"""
Скрипт проверки проекта AI Summariser перед публикацией
"""

import os
import sys
import importlib
import ast
from pathlib import Path
from typing import List, Dict, Any

def check_imports(file_path: str) -> List[str]:
    """Проверить импорты в файле"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Проверяем стандартные библиотеки
        stdlib_modules = {
            'asyncio', 'logging', 'json', 'datetime', 'typing', 
            'pathlib', 'os', 'sys', 'argparse'
        }
        
        for imp in imports:
            if imp in stdlib_modules:
                continue
            try:
                importlib.import_module(imp)
            except ImportError:
                issues.append(f"Не найден модуль: {imp}")
                
    except Exception as e:
        issues.append(f"Ошибка парсинга {file_path}: {e}")
    
    return issues

def check_syntax(file_path: str) -> List[str]:
    """Проверить синтаксис файла"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
    except SyntaxError as e:
        issues.append(f"Синтаксическая ошибка: {e}")
    except Exception as e:
        issues.append(f"Ошибка чтения файла: {e}")
    return issues

def check_file_structure() -> Dict[str, Any]:
    """Проверить структуру файлов проекта"""
    required_files = [
        'README.md',
        'setup.py',
        'requirements.txt',
        'LICENSE',
        '.gitignore',
        'ai_summariser/__init__.py',
        'ai_summariser/cli.py',
        'ai_summariser/core/__init__.py',
        'ai_summariser/core/database.py',
        'ai_summariser/core/summariser.py',
        'ai_summariser/core/ai_client.py',
        'ai_summariser/models/__init__.py',
        'ai_summariser/models/schemas.py',
        'ai_summariser/utils/__init__.py',
        'ai_summariser/utils/helpers.py',
        'tests/__init__.py',
        'tests/test_summariser.py',
        'tests/test_ai_client.py',
        'examples/basic_usage.py',
        'examples/advanced_analysis.py'
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    return {
        'missing': missing_files,
        'existing': existing_files,
        'total_required': len(required_files),
        'total_existing': len(existing_files)
    }

def check_python_files() -> Dict[str, List[str]]:
    """Проверить все Python файлы"""
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Игнорируем внешние папки и системные директории
        if any(skip in root for skip in ['venv', '.venv', '__pycache__', 'FreeGPT-Portable', '.git']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    all_issues = {}
    
    for file_path in python_files:
        issues = []
        issues.extend(check_syntax(file_path))
        issues.extend(check_imports(file_path))
        
        if issues:
            all_issues[file_path] = issues
    
    return all_issues

def check_readme() -> List[str]:
    """Проверить README.md"""
    issues = []
    
    if not Path('README.md').exists():
        issues.append("README.md не найден")
        return issues
    
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_sections = [
        '# AI Summariser',
        '## 📋 Описание',
        '## 🚀 Быстрый старт',
        '## 📁 Структура проекта',
        '## 📝 Лицензия'
    ]
    
    for section in required_sections:
        if section not in content:
            issues.append(f"Отсутствует раздел: {section}")
    
    return issues

def main():
    """Основная функция проверки"""
    print("🔍 Проверка проекта AI Summariser")
    print("=" * 50)
    
    # Проверка структуры файлов
    print("\n📁 Проверка структуры файлов...")
    structure = check_file_structure()
    
    print(f"   Всего файлов: {structure['total_existing']}/{structure['total_required']}")
    
    if structure['missing']:
        print("   ❌ Отсутствующие файлы:")
        for file in structure['missing']:
            print(f"      - {file}")
    else:
        print("   ✅ Все файлы на месте")
    
    # Проверка Python файлов
    print("\n🐍 Проверка Python файлов...")
    python_issues = check_python_files()
    
    if python_issues:
        print("   ❌ Найдены проблемы:")
        for file_path, issues in python_issues.items():
            print(f"      {file_path}:")
            for issue in issues:
                print(f"        - {issue}")
    else:
        print("   ✅ Все Python файлы корректны")
    
    # Проверка README
    print("\n📖 Проверка README.md...")
    readme_issues = check_readme()
    
    if readme_issues:
        print("   ❌ Проблемы в README:")
        for issue in readme_issues:
            print(f"      - {issue}")
    else:
        print("   ✅ README.md корректен")
    
    # Итоговая оценка
    print("\n📊 Итоговая оценка:")
    
    total_issues = len(structure['missing']) + len(python_issues) + len(readme_issues)
    
    if total_issues == 0:
        print("   🎉 Проект готов к публикации!")
        return True
    else:
        print(f"   ⚠️  Найдено {total_issues} проблем")
        print("   Исправьте их перед публикацией")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 