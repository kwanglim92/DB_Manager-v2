#!/usr/bin/env python3
"""
Method analyzer for manager.py
Identifies methods by line count and complexity
"""

import re
import os
import sys

def analyze_methods(file_path):
    """Analyze methods in a Python file and return statistics."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    methods = []
    current_method = None
    indent_stack = []

    for i, line in enumerate(lines, 1):
        # Skip blank lines and comments
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            if current_method:
                current_method['lines'].append(line)
            continue

        # Detect method definition
        match = re.match(r'^(\s*)def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line)
        if match:
            # Save previous method
            if current_method:
                current_method['end_line'] = i - 1
                methods.append(current_method)

            indent = len(match.group(1))
            method_name = match.group(2)

            current_method = {
                'name': method_name,
                'start_line': i,
                'end_line': None,
                'indent': indent,
                'lines': [line]
            }
        elif current_method:
            # Check if we're still in the method
            stripped_line = line.lstrip()
            if stripped_line and not line.startswith(' ' * (current_method['indent'] + 1)):
                # We've exited the method
                current_method['end_line'] = i - 1
                methods.append(current_method)
                current_method = None
            else:
                current_method['lines'].append(line)

    # Handle last method
    if current_method:
        current_method['end_line'] = len(lines)
        methods.append(current_method)

    # Calculate line counts
    for method in methods:
        method['line_count'] = len(method['lines'])

    return methods

def main():
    file_path = '/home/user/DB_Manager-v2/src/app/manager.py'

    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return

    methods = analyze_methods(file_path)

    # Sort by line count (descending)
    methods_sorted = sorted(methods, key=lambda m: m['line_count'], reverse=True)

    # Print statistics
    print("=" * 80)
    print("MANAGER.PY METHOD ANALYSIS")
    print("=" * 80)
    print(f"\nTotal methods: {len(methods)}")
    print(f"Total file size: {os.path.getsize(file_path) / 1024:.2f} KB")

    # Categorize by size
    very_large = [m for m in methods if m['line_count'] > 200]
    large = [m for m in methods if 150 <= m['line_count'] <= 200]
    medium = [m for m in methods if 100 <= m['line_count'] < 150]
    small = [m for m in methods if 50 <= m['line_count'] < 100]
    tiny = [m for m in methods if m['line_count'] < 50]

    print(f"\nMethod size distribution:")
    print(f"  Very Large (>200 lines):    {len(very_large)}")
    print(f"  Large (150-200 lines):      {len(large)}")
    print(f"  Medium (100-150 lines):     {len(medium)}")
    print(f"  Small (50-100 lines):       {len(small)}")
    print(f"  Tiny (<50 lines):           {len(tiny)}")

    # Print top 20 largest methods
    print("\n" + "=" * 80)
    print("TOP 20 LARGEST METHODS")
    print("=" * 80)
    print(f"{'Rank':<6} {'Lines':<8} {'Start':<8} {'End':<8} {'Method Name'}")
    print("-" * 80)

    for i, method in enumerate(methods_sorted[:20], 1):
        print(f"{i:<6} {method['line_count']:<8} {method['start_line']:<8} "
              f"{method['end_line']:<8} {method['name']}")

    # Print 150-200 line methods (target for Task 1)
    print("\n" + "=" * 80)
    print("TARGET METHODS FOR TASK 1 (150-200 lines)")
    print("=" * 80)
    print(f"{'Lines':<8} {'Start':<8} {'End':<8} {'Method Name'}")
    print("-" * 80)

    if large:
        for method in sorted(large, key=lambda m: m['line_count'], reverse=True):
            print(f"{method['line_count']:<8} {method['start_line']:<8} "
                  f"{method['end_line']:<8} {method['name']}")
    else:
        print("No methods in 150-200 line range found!")

    # Print 100-150 line methods (potential targets)
    print("\n" + "=" * 80)
    print("POTENTIAL TARGETS (100-150 lines)")
    print("=" * 80)
    print(f"{'Lines':<8} {'Start':<8} {'End':<8} {'Method Name'}")
    print("-" * 80)

    if medium:
        for method in sorted(medium, key=lambda m: m['line_count'], reverse=True)[:10]:
            print(f"{method['line_count']:<8} {method['start_line']:<8} "
                  f"{method['end_line']:<8} {method['name']}")

if __name__ == '__main__':
    main()
