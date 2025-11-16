#!/usr/bin/env python3
"""
Apply messagebox helper methods across manager.py
Replaces ~103 direct messagebox calls with helper methods
"""

import re
import sys

def apply_helpers(file_path):
    """Apply helper method transformations to manager.py"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = []

    # Pattern 1: messagebox.showerror + logging.error
    # Before: messagebox.showerror("Title", "message")\n        logging.error("...")
    # After: self._show_error("Title", "message")

    # Simple replacement patterns (most common cases)
    replacements = [
        # showerror with title and message
        (r'messagebox\.showerror\("([^"]+)",\s*"([^"]+)"\)',
         r'self._show_error("\1", "\2")'),
        (r'messagebox\.showerror\("([^"]+)",\s*f"([^"]+)"\)',
         r'self._show_error("\1", f"\2")'),

        # showwarning with title and message
        (r'messagebox\.showwarning\("([^"]+)",\s*"([^"]+)"\)',
         r'self._show_warning("\1", "\2")'),
        (r'messagebox\.showwarning\("([^"]+)",\s*f"([^"]+)"\)',
         r'self._show_warning("\1", f"\2")'),

        # showinfo with title and message
        (r'messagebox\.showinfo\("([^"]+)",\s*"([^"]+)"\)',
         r'self._show_info("\1", "\2")'),
        (r'messagebox\.showinfo\("([^"]+)",\s*f"([^"]+)"\)',
         r'self._show_info("\1", f"\2")'),
    ]

    for pattern, replacement in replacements:
        matches = re.findall(pattern, content)
        if matches:
            changes.append(f"Pattern '{pattern[:50]}...': {len(matches)} matches")
            content = re.sub(pattern, replacement, content)

    # Pattern 2: Permission checks
    # Before: if not self.maint_mode:\n    messagebox.showerror(...)\n    return
    # After: if not self._require_maintenance_mode():\n    return

    permission_pattern = r'if not self\.maint_mode:\s*\n\s*messagebox\.showerror\([^)]+\)\s*\n\s*return'
    permission_matches = re.findall(permission_pattern, content)
    if permission_matches:
        changes.append(f"Permission checks: {len(permission_matches)} matches")
        content = re.sub(
            permission_pattern,
            'if not self._require_maintenance_mode():\n            return',
            content
        )

    # Pattern 3: Treeview clearing
    # Before: for item in tree.get_children():\n    tree.delete(item)
    # After: self._clear_treeview(tree)

    treeview_pattern = r'for item in (\w+)\.get_children\(\):\s*\n\s*\1\.delete\(item\)'
    treeview_matches = re.findall(treeview_pattern, content)
    if treeview_matches:
        changes.append(f"Treeview clears: {len(treeview_matches)} matches")
        for tree_name in set(treeview_matches):
            content = re.sub(
                f'for item in {tree_name}\.get_children\(\):\s*\n\s*{tree_name}\.delete\(item\)',
                f'self._clear_treeview({tree_name})',
                content
            )

    # Calculate statistics
    total_changes = content != original_content

    if total_changes:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Helper methods applied successfully!")
        print("\nChanges made:")
        for change in changes:
            print(f"  - {change}")

        return True
    else:
        print("ℹ️ No changes needed")
        return False

if __name__ == '__main__':
    file_path = 'src/app/manager.py'
    success = apply_helpers(file_path)
    sys.exit(0 if success else 1)
