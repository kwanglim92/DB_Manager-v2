"""
Check list 관리 다이얼로그

관리자가 Check list를 관리할 수 있는 UI를 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json


class ChecklistManagerDialog:
    """Check list 관리 다이얼로그"""

    def __init__(self, parent, db_schema, service_factory):
        """
        Args:
            parent: 부모 윈도우
            db_schema: DBSchema 인스턴스
            service_factory: ServiceFactory 인스턴스
        """
        self.parent = parent
        self.db_schema = db_schema
        self.service_factory = service_factory
        self.checklist_service = service_factory.get_checklist_service()

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Check list 관리")
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_ui()
        self._load_data()

    def _create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        title_label = ttk.Label(
            main_frame,
            text="Check list 관리 (관리자 전용)",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 탭 노트북
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 탭 생성
        self._create_common_checklist_tab()
        self._create_equipment_checklist_tab()
        self._create_audit_log_tab()

        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="닫기",
            command=self.dialog.destroy,
            width=15
        ).pack()

    def _create_common_checklist_tab(self):
        """공통 Check list 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="공통 Check list")

        # 상단 버튼 프레임
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="➕ 추가",
            command=self._add_checklist_item,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="✏️ 수정",
            command=self._edit_checklist_item,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="❌ 삭제",
            command=self._delete_checklist_item,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="🔄 새로고침",
            command=self._refresh_common_checklist,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # 트리뷰 프레임
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 트리뷰
        columns = ("ID", "항목명", "패턴", "공통", "심각도", "설명")
        self.common_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # 컬럼 설정
        self.common_tree.column("#0", width=0, stretch=False)
        self.common_tree.column("ID", width=50, anchor="center")
        self.common_tree.column("항목명", width=200)
        self.common_tree.column("패턴", width=250)
        self.common_tree.column("공통", width=60, anchor="center")
        self.common_tree.column("심각도", width=100, anchor="center")
        self.common_tree.column("설명", width=300)

        # 헤더 설정
        for col in columns:
            self.common_tree.heading(col, text=col, anchor="center")

        # 스크롤바
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.common_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.common_tree.xview)
        self.common_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 배치
        self.common_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # 더블클릭 이벤트
        self.common_tree.bind("<Double-1>", lambda e: self._edit_checklist_item())

    def _create_equipment_checklist_tab(self):
        """장비별 Check list 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="장비별 Check list")

        # 상단 프레임 - 장비 선택
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(top_frame, text="장비 유형:").pack(side=tk.LEFT, padx=5)

        self.equipment_combo = ttk.Combobox(top_frame, state="readonly", width=30)
        self.equipment_combo.pack(side=tk.LEFT, padx=5)
        self.equipment_combo.bind("<<ComboboxSelected>>", lambda e: self._load_equipment_checklist())

        ttk.Button(
            top_frame,
            text="🔄 새로고침",
            command=self._load_equipment_checklist,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        # 트리뷰 프레임
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 트리뷰
        columns = ("ID", "항목명", "심각도", "출처", "필수", "우선순위")
        self.equipment_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # 컬럼 설정
        self.equipment_tree.column("#0", width=0, stretch=False)
        self.equipment_tree.column("ID", width=50, anchor="center")
        self.equipment_tree.column("항목명", width=250)
        self.equipment_tree.column("심각도", width=100, anchor="center")
        self.equipment_tree.column("출처", width=100, anchor="center")
        self.equipment_tree.column("필수", width=80, anchor="center")
        self.equipment_tree.column("우선순위", width=100, anchor="center")

        # 헤더 설정
        for col in columns:
            self.equipment_tree.heading(col, text=col, anchor="center")

        # 스크롤바
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.equipment_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.equipment_tree.xview)
        self.equipment_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 배치
        self.equipment_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # 장비 목록 로드
        self._load_equipment_types()

    def _create_audit_log_tab(self):
        """Audit Log 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="변경 이력")

        # 상단 버튼 프레임
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="🔄 새로고침",
            command=self._refresh_audit_log,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # 트리뷰 프레임
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 트리뷰
        columns = ("ID", "작업", "대상 테이블", "사용자", "사유", "시간")
        self.audit_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # 컬럼 설정
        self.audit_tree.column("#0", width=0, stretch=False)
        self.audit_tree.column("ID", width=50, anchor="center")
        self.audit_tree.column("작업", width=100, anchor="center")
        self.audit_tree.column("대상 테이블", width=200)
        self.audit_tree.column("사용자", width=150)
        self.audit_tree.column("사유", width=300)
        self.audit_tree.column("시간", width=180)

        # 헤더 설정
        for col in columns:
            self.audit_tree.heading(col, text=col, anchor="center")

        # 스크롤바
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.audit_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.audit_tree.xview)
        self.audit_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 배치
        self.audit_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def _load_data(self):
        """초기 데이터 로드"""
        self._refresh_common_checklist()
        self._refresh_audit_log()

    def _refresh_common_checklist(self):
        """공통 Check list 새로고침"""
        # 기존 항목 제거
        for item in self.common_tree.get_children():
            self.common_tree.delete(item)

        # 데이터 로드
        try:
            items = self.checklist_service.get_common_checklist_items()

            for item in items:
                item_id = item[0]
                item_name = item[1]
                pattern = item[2]
                is_common = "공통" if item[3] else "장비별"
                severity = item[4]
                description = item[6] if len(item) > 6 else ""

                # 심각도별 태그
                tag = self._get_severity_tag(severity)

                self.common_tree.insert(
                    "",
                    tk.END,
                    values=(item_id, item_name, pattern, is_common, severity, description),
                    tags=(tag,)
                )

            # 태그 색상 설정
            self.common_tree.tag_configure("critical", background="#ffcccc")
            self.common_tree.tag_configure("high", background="#ffe6cc")
            self.common_tree.tag_configure("medium", background="#ffffcc")
            self.common_tree.tag_configure("low", background="#e6f7ff")

        except Exception as e:
            messagebox.showerror("오류", f"Check list 로드 실패:\n{str(e)}")

    def _load_equipment_types(self):
        """장비 유형 목록 로드"""
        try:
            equipment_types = self.db_schema.get_equipment_types()
            self.equipment_combo['values'] = [f"{et[0]}: {et[1]}" for et in equipment_types]
            if equipment_types:
                self.equipment_combo.current(0)
                self._load_equipment_checklist()
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 로드 실패:\n{str(e)}")

    def _load_equipment_checklist(self):
        """장비별 Check list 로드"""
        # 기존 항목 제거
        for item in self.equipment_tree.get_children():
            self.equipment_tree.delete(item)

        # 선택된 장비 ID 추출
        selected = self.equipment_combo.get()
        if not selected:
            return

        equipment_id = int(selected.split(":")[0])

        # 데이터 로드
        try:
            items = self.checklist_service.get_equipment_checklist(equipment_id)

            for item in items:
                item_id = item['id']
                item_name = item['item_name']
                severity = item['severity_level']
                source = item['source']
                is_required = "필수" if item.get('is_required') else "선택"
                priority = item.get('priority', '-')

                # 심각도별 태그
                tag = self._get_severity_tag(severity)

                self.equipment_tree.insert(
                    "",
                    tk.END,
                    values=(item_id, item_name, severity, source, is_required, priority),
                    tags=(tag,)
                )

            # 태그 색상 설정
            self.equipment_tree.tag_configure("critical", background="#ffcccc")
            self.equipment_tree.tag_configure("high", background="#ffe6cc")
            self.equipment_tree.tag_configure("medium", background="#ffffcc")
            self.equipment_tree.tag_configure("low", background="#e6f7ff")

        except Exception as e:
            messagebox.showerror("오류", f"장비별 Check list 로드 실패:\n{str(e)}")

    def _refresh_audit_log(self):
        """Audit Log 새로고침"""
        # 기존 항목 제거
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

        # 데이터 로드
        try:
            logs = self.checklist_service.get_audit_log(limit=100)

            for log in logs:
                log_id = log[0]
                action = log[1]
                target_table = log[2]
                user = log[7] if log[7] else "시스템"
                reason = log[6] if log[6] else "-"
                timestamp = log[8]

                self.audit_tree.insert(
                    "",
                    tk.END,
                    values=(log_id, action, target_table, user, reason, timestamp)
                )

        except Exception as e:
            messagebox.showerror("오류", f"Audit Log 로드 실패:\n{str(e)}")

    def _get_severity_tag(self, severity):
        """심각도에 따른 태그 반환"""
        severity_map = {
            'CRITICAL': 'critical',
            'HIGH': 'high',
            'MEDIUM': 'medium',
            'LOW': 'low'
        }
        return severity_map.get(severity, 'low')

    def _add_checklist_item(self):
        """Check list 항목 추가"""
        dialog = ChecklistItemDialog(self.dialog, self.checklist_service, mode="add")
        self.dialog.wait_window(dialog.dialog)

        if dialog.result:
            self._refresh_common_checklist()
            messagebox.showinfo("성공", "Check list 항목이 추가되었습니다.")

    def _edit_checklist_item(self):
        """Check list 항목 수정"""
        selected = self.common_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "수정할 항목을 선택하세요.")
            return

        # 선택된 항목 데이터 가져오기
        item_values = self.common_tree.item(selected[0], 'values')
        item_id = int(item_values[0])

        # TODO: 수정 다이얼로그 구현
        messagebox.showinfo("알림", "Check list 항목 수정 기능은 개발 중입니다.")

    def _delete_checklist_item(self):
        """Check list 항목 삭제"""
        selected = self.common_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "삭제할 항목을 선택하세요.")
            return

        # 확인
        if not messagebox.askyesno("확인", "선택한 Check list 항목을 삭제하시겠습니까?"):
            return

        # TODO: 삭제 기능 구현
        messagebox.showinfo("알림", "Check list 항목 삭제 기능은 개발 중입니다.")


class ChecklistItemDialog:
    """Check list 항목 추가/수정 다이얼로그"""

    def __init__(self, parent, checklist_service, mode="add", item_data=None):
        """
        Args:
            parent: 부모 윈도우
            checklist_service: ChecklistService 인스턴스
            mode: "add" 또는 "edit"
            item_data: 수정 모드일 때 기존 데이터
        """
        self.parent = parent
        self.checklist_service = checklist_service
        self.mode = mode
        self.item_data = item_data
        self.result = None

        # 다이얼로그 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Check list 항목 추가" if mode == "add" else "Check list 항목 수정")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_ui()

    def _create_ui(self):
        """UI 생성"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 항목명
        ttk.Label(main_frame, text="항목명:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(main_frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        # 파라미터 패턴
        ttk.Label(main_frame, text="파라미터 패턴:").grid(row=1, column=0, sticky="w", pady=5)
        self.pattern_entry = ttk.Entry(main_frame, width=50)
        self.pattern_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        # 심각도
        ttk.Label(main_frame, text="심각도:").grid(row=2, column=0, sticky="w", pady=5)
        self.severity_combo = ttk.Combobox(
            main_frame,
            values=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            state="readonly",
            width=47
        )
        self.severity_combo.current(2)  # MEDIUM 기본값
        self.severity_combo.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        # 설명
        ttk.Label(main_frame, text="설명:").grid(row=3, column=0, sticky="nw", pady=5)
        self.desc_text = tk.Text(main_frame, width=50, height=5)
        self.desc_text.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

        # 검증 규칙 (JSON)
        ttk.Label(main_frame, text="검증 규칙 (JSON):").grid(row=4, column=0, sticky="nw", pady=5)
        self.rule_text = tk.Text(main_frame, width=50, height=6)
        self.rule_text.grid(row=4, column=1, sticky="ew", pady=5, padx=(10, 0))

        # 기본값 설정
        default_rule = '''{
  "type": "range",
  "min": 0,
  "max": 100
}'''
        self.rule_text.insert("1.0", default_rule)

        # 버튼 프레임
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            btn_frame,
            text="저장",
            command=self._save,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="취소",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        main_frame.grid_columnconfigure(1, weight=1)

    def _save(self):
        """저장"""
        # 입력 값 가져오기
        item_name = self.name_entry.get().strip()
        pattern = self.pattern_entry.get().strip()
        severity = self.severity_combo.get()
        description = self.desc_text.get("1.0", tk.END).strip()
        validation_rule = self.rule_text.get("1.0", tk.END).strip()

        # 유효성 검사
        if not item_name:
            messagebox.showwarning("경고", "항목명을 입력하세요.")
            return

        if not pattern:
            messagebox.showwarning("경고", "파라미터 패턴을 입력하세요.")
            return

        # JSON 검증
        if validation_rule:
            try:
                json.loads(validation_rule)
            except json.JSONDecodeError as e:
                messagebox.showerror("오류", f"검증 규칙 JSON 형식 오류:\n{str(e)}")
                return

        # 저장
        try:
            result = self.checklist_service.add_checklist_item(
                item_name=item_name,
                parameter_pattern=pattern,
                is_common=True,
                severity_level=severity,
                validation_rule=validation_rule if validation_rule else None,
                description=description
            )

            if result:
                self.result = result
                self.dialog.destroy()
            else:
                messagebox.showerror("오류", "Check list 항목 추가 실패 (이미 존재하는 항목일 수 있습니다)")

        except Exception as e:
            messagebox.showerror("오류", f"저장 실패:\n{str(e)}")
