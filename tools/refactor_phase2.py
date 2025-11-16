#!/usr/bin/env python3
"""
Phase 2 Refactoring Script
Splits long methods in manager.py into smaller, more maintainable pieces.
"""

import re
import sys


def refactor_add_to_default_db(content):
    """
    Refactor add_to_default_db method by extracting helper methods.
    """

    # Define helper method 1: _collect_selected_comparison_items
    helper1 = '''    def _collect_selected_comparison_items(self):
        """
        비교 뷰에서 선택된 항목들을 수집합니다.
        체크박스 또는 트리뷰 선택을 기반으로 항목을 수집합니다.

        Returns:
            list: 선택된 트리뷰 항목 ID 리스트, 선택 없으면 None
        """
        selected_items = []

        if any(self.item_checkboxes.values()):
            # 체크박스가 하나라도 선택된 경우
            for item_key, is_checked in self.item_checkboxes.items():
                if is_checked:
                    # item_key에서 module, part, item_name 분리
                    parts = item_key.split('_')
                    if len(parts) >= 3:
                        module, part, item_name = parts[0], parts[1], '_'.join(parts[2:])

                        # 트리뷰에서 해당 항목 찾기
                        for child_id in self.comparison_tree.get_children():
                            values = self.comparison_tree.item(child_id, 'values')
                            if len(values) >= 4 and values[1] == module and values[2] == part and values[3] == item_name:
                                selected_items.append(child_id)
                                break
        else:
            # 체크박스가 선택되지 않은 경우, 트리뷰에서 직접 선택된 항목 사용
            selected_items = self.comparison_tree.selection()

        if not selected_items:
            self._show_warning("선택 필요", "Default DB에 추가할 항목을 먼저 선택해주세요.")
            return None

        return selected_items

'''

    # Define helper method 2: _create_equipment_type_selection_frame
    helper2 = '''    def _create_equipment_type_selection_frame(self, parent, equipment_types, type_names):
        """
        장비 유형 선택 UI 프레임을 생성합니다.

        Args:
            parent: 부모 위젯
            equipment_types: 장비 유형 리스트
            type_names: 장비 유형 이름 리스트

        Returns:
            tuple: (selected_type_var, new_type_var) StringVar 튜플
        """
        type_frame = ttk.LabelFrame(parent, text="🔧 장비 유형 선택", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(type_frame, text="기존 장비 유형:").grid(row=0, column=0, sticky="w", padx=5, pady=5)

        selected_type = tk.StringVar()
        combo = ttk.Combobox(type_frame, textvariable=selected_type, values=type_names, state="readonly", width=40)
        combo.grid(row=0, column=1, padx=5, pady=5)
        if type_names:
            combo.set(type_names[0])

        ttk.Label(type_frame, text="또는 새 장비 유형:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        new_type_var = tk.StringVar()
        new_type_entry = ttk.Entry(type_frame, textvariable=new_type_var, width=40)
        new_type_entry.grid(row=1, column=1, padx=5, pady=5)

        return selected_type, new_type_var

'''

    # Define helper method 3: _create_statistics_settings_frame
    helper3 = '''    def _create_statistics_settings_frame(self, parent):
        """
        통계 분석 설정 UI 프레임을 생성합니다.

        Args:
            parent: 부모 위젯

        Returns:
            tuple: (analyze_var, confidence_var, confidence_label, confidence_scale)
        """
        stats_frame = ttk.LabelFrame(parent, text="📊 통계 분석 설정 (중복도 기반 기준값 도출)", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        analyze_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(stats_frame, text="✓ 값의 중복도 분석 수행 (권장)", variable=analyze_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

        ttk.Label(stats_frame, text="신뢰도 임계값:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        confidence_var = tk.DoubleVar(value=50.0)
        confidence_scale = ttk.Scale(stats_frame, from_=0, to=100, variable=confidence_var, orient="horizontal", length=200)
        confidence_scale.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        confidence_label = ttk.Label(stats_frame, text="50.0% (과반수 이상)")
        confidence_label.grid(row=1, column=2, sticky="w", padx=5, pady=5)

        def update_confidence_label(event=None):
            val = confidence_var.get()
            if val >= 80:
                desc = "매우 높음"
            elif val >= 60:
                desc = "높음"
            elif val >= 40:
                desc = "보통"
            else:
                desc = "낮음"
            confidence_label.config(text=f"{val:.1f}% ({desc})")

        confidence_scale.configure(command=update_confidence_label)

        return analyze_var, confidence_var, confidence_label, confidence_scale

'''

    # Define helper method 4: _create_preview_frame
    helper4 = '''    def _create_preview_frame(self, parent):
        """
        미리보기 텍스트 위젯을 생성합니다.

        Args:
            parent: 부모 위젯

        Returns:
            tk.Text: 미리보기 텍스트 위젯
        """
        preview_frame = ttk.LabelFrame(parent, text="📋 추가될 항목 미리보기 및 통계", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        preview_text = tk.Text(preview_frame, height=12, wrap=tk.WORD, font=("Consolas", 9))
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
        preview_text.configure(yscrollcommand=preview_scroll.set)

        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        preview_text.pack(fill=tk.BOTH, expand=True)

        return preview_text

'''

    # Insert helper methods before add_to_default_db
    pattern = r'(\n    def add_to_default_db\(self\):)'
    replacement = '\n' + helper1 + helper2 + helper3 + helper4 + r'\1'
    content = re.sub(pattern, replacement, content, count=1)

    # Now modify the beginning of add_to_default_db to use helpers
    old_start = '''    def add_to_default_db(self):
        """체크된 항목들을 Default DB로 전송 - 중복도 기반 통계 분석"""
        if not self._require_maintenance_mode("Default DB 항목 추가"):
            return

        # 체크된 항목들 수집
        selected_items = []
        if any(self.item_checkboxes.values()):
            # 체크박스가 하나라도 선택된 경우
            for item_key, is_checked in self.item_checkboxes.items():
                if is_checked:
                    # item_key에서 module, part, item_name 분리
                    parts = item_key.split('_')
                    if len(parts) >= 3:
                        module, part, item_name = parts[0], parts[1], '_'.join(parts[2:])

                        # 트리뷰에서 해당 항목 찾기
                        for child_id in self.comparison_tree.get_children():
                            values = self.comparison_tree.item(child_id, 'values')
                            if len(values) >= 4 and values[1] == module and values[2] == part and values[3] == item_name:
                                selected_items.append(child_id)
                                break
        else:
            # 체크박스가 선택되지 않은 경우, 트리뷰에서 직접 선택된 항목 사용
            selected_items = self.comparison_tree.selection()

        if not selected_items:
            self._show_warning("선택 필요", "Default DB에 추가할 항목을 먼저 선택해주세요.")
            return

        # 장비 유형 선택 또는 새로 생성
        equipment_types = self.db_schema.get_equipment_types()
        type_names = [f"{name} (ID: {type_id})" for type_id, name, _ in equipment_types]

        # 고급 선택 다이얼로그
        dlg = self._create_modal_dialog("Default DB 추가 - 통계 기반 기준값 설정", "700x600")

        # 장비 유형 선택 프레임
        type_frame = ttk.LabelFrame(dlg, text="🔧 장비 유형 선택", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(type_frame, text="기존 장비 유형:").grid(row=0, column=0, sticky="w", padx=5, pady=5)

        selected_type = tk.StringVar()
        combo = ttk.Combobox(type_frame, textvariable=selected_type, values=type_names, state="readonly", width=40)
        combo.grid(row=0, column=1, padx=5, pady=5)
        if type_names:
            combo.set(type_names[0])

        ttk.Label(type_frame, text="또는 새 장비 유형:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        new_type_var = tk.StringVar()
        new_type_entry = ttk.Entry(type_frame, textvariable=new_type_var, width=40)
        new_type_entry.grid(row=1, column=1, padx=5, pady=5)

        # 통계 분석 설정
        stats_frame = ttk.LabelFrame(dlg, text="📊 통계 분석 설정 (중복도 기반 기준값 도출)", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        analyze_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(stats_frame, text="✓ 값의 중복도 분석 수행 (권장)", variable=analyze_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

        ttk.Label(stats_frame, text="신뢰도 임계값:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        confidence_var = tk.DoubleVar(value=50.0)
        confidence_scale = ttk.Scale(stats_frame, from_=0, to=100, variable=confidence_var, orient="horizontal", length=200)
        confidence_scale.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        confidence_label = ttk.Label(stats_frame, text="50.0% (과반수 이상)")
        confidence_label.grid(row=1, column=2, sticky="w", padx=5, pady=5)

        def update_confidence_label(event=None):
            val = confidence_var.get()
            if val >= 80:
                desc = "매우 높음"
            elif val >= 60:
                desc = "높음"
            elif val >= 40:
                desc = "보통"
            else:
                desc = "낮음"
            confidence_label.config(text=f"{val:.1f}% ({desc})")
        confidence_scale.configure(command=update_confidence_label)

        # 미리보기 영역
        preview_frame = ttk.LabelFrame(dlg, text="📋 추가될 항목 미리보기 및 통계", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        preview_text = tk.Text(preview_frame, height=12, wrap=tk.WORD, font=("Consolas", 9))
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
        preview_text.configure(yscrollcommand=preview_scroll.set)

        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        preview_text.pack(fill=tk.BOTH, expand=True)'''

    new_start = '''    def add_to_default_db(self):
        """체크된 항목들을 Default DB로 전송 - 중복도 기반 통계 분석"""
        if not self._require_maintenance_mode("Default DB 항목 추가"):
            return

        # 선택된 항목 수집
        selected_items = self._collect_selected_comparison_items()
        if selected_items is None:
            return

        # 장비 유형 선택 또는 새로 생성
        equipment_types = self.db_schema.get_equipment_types()
        type_names = [f"{name} (ID: {type_id})" for type_id, name, _ in equipment_types]

        # 고급 선택 다이얼로그
        dlg = self._create_modal_dialog("Default DB 추가 - 통계 기반 기준값 설정", "700x600")

        # 장비 유형 선택 프레임 생성
        selected_type, new_type_var = self._create_equipment_type_selection_frame(dlg, equipment_types, type_names)

        # 통계 분석 설정 프레임 생성
        analyze_var, confidence_var, confidence_label, confidence_scale = self._create_statistics_settings_frame(dlg)

        # 미리보기 영역 생성
        preview_text = self._create_preview_frame(dlg)'''

    content = content.replace(old_start, new_start)

    return content


def main():
    input_file = '/home/user/DB_Manager-v2/src/app/manager.py'

    # Read the file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Perform refactoring
    print("Refactoring add_to_default_db method...")
    content = refactor_add_to_default_db(content)

    # Write back
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Refactoring complete!")
    print("  - Added 4 new helper methods")
    print("  - Simplified add_to_default_db method")


if __name__ == '__main__':
    main()
