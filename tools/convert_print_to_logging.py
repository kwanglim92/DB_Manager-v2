#!/usr/bin/env python3
"""
Convert print() statements to logging calls in manager.py
"""

import re
import sys

def convert_print_to_logging(file_path):
    """Convert print() statements to appropriate logging calls"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    conversion_count = 0

    # Define conversion patterns with their logging levels
    conversions = [
        # DEBUG patterns (most specific first)
        (r'print\(f"DEBUG - ([^"]+)"\)', r'logging.debug(f"\1")', 'DEBUG'),
        (r'print\(f"DEBUG: ([^"]+)"\)', r'logging.debug(f"\1")', 'DEBUG'),
        (r'print\("DEBUG: ([^"]+)"\)', r'logging.debug("\1")', 'DEBUG'),

        # Error patterns
        (r'print\(f"DB 스키마 초기화 실패: ([^"]+)"\)', r'logging.error(f"DB 스키마 초기화 실패: \1")', 'ERROR'),
        (r'print\(f"아이콘 로드 실패: ([^"]+)"\)', r'logging.warning(f"아이콘 로드 실패: \1")', 'WARNING'),
        (r'print\(f"Service layer initialization failed: ([^"]+)"\)', r'logging.error(f"Service layer initialization failed: \1")', 'ERROR'),
        (r'print\(f"([^"]*오류[^"]*): ([^"]+)"\)', r'logging.error(f"\1: \2")', 'ERROR'),
        (r'print\(f"([^"]*error[^"]*): ([^"]+)"\)', r'logging.error(f"\1: \2")', 'ERROR'),

        # Info patterns
        (r'print\("사용 설명서가 호출되었습니다\.([^"]+)"\)', r'logging.info("사용 설명서가 호출되었습니다.\1")', 'INFO'),
        (r'print\("Filter panel created - ([^"]+)"\)', r'logging.debug("Filter panel created - \1")', 'DEBUG'),
        (r'print\(f"Filter ([^"]+)"\)', r'logging.debug(f"Filter \1")', 'DEBUG'),
        (r'print\(f"Toggle ([^"]+)"\)', r'logging.debug(f"Toggle \1")', 'DEBUG'),
        (r'print\(f"Comparison ([^"]+)"\)', r'logging.debug(f"Comparison \1")', 'DEBUG'),
        (r'print\("Hiding ([^"]+)"\)', r'logging.debug("Hiding \1")', 'DEBUG'),
        (r'print\("Showing ([^"]+)"\)', r'logging.debug("Showing \1")', 'DEBUG'),
    ]

    # Apply conversions
    for pattern, replacement, level in conversions:
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            print(f"  [{level}] Converted {count} statements: {pattern[:50]}...")
            conversion_count += count
            content = new_content

    # Check if logging is imported
    if 'import logging' not in content:
        # Find the right place to add import (after other imports, before class definition)
        # Look for the line with "from app.dialog_helpers import"
        import_section_end = content.find('from app.dialog_helpers import')
        if import_section_end != -1:
            # Find the end of this line
            line_end = content.find('\n', import_section_end)
            if line_end != -1:
                # Insert "import logging" after this line
                content = content[:line_end+1] + 'import logging\n' + content[line_end+1:]
                print("  [IMPORT] Added 'import logging'")
                conversion_count += 1

    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ Successfully converted {conversion_count} items in {file_path}")
        return conversion_count
    else:
        print(f"\n⚠️  No changes needed in {file_path}")
        return 0

if __name__ == '__main__':
    file_path = '/home/user/DB_Manager-v2/src/app/manager.py'

    print(f"Converting print() statements in {file_path}...")
    print("=" * 70)

    count = convert_print_to_logging(file_path)

    print("=" * 70)
    print(f"Total conversions: {count}")
