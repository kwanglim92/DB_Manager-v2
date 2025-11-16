#!/usr/bin/env python3
"""
Refactor create_default_db_tab method
Splits into helper methods for better organization
"""

import re


def create_helper_methods():
    """Generate helper method code"""

    helper1 = '''    def _initialize_default_db_tab_frame(self):
        """
        Default DB 탭 프레임을 초기화합니다.
        중복 탭 검사 및 프레임 생성을 수행합니다.

        Returns:
            bool: 성공 시 True, 실패 또는 중복 시 False
        """
        # 기존 탭 중복 검사 강화
        if hasattr(self, 'main_notebook') and self.main_notebook:
            for tab_id in range(self.main_notebook.index('end')):
                try:
                    tab_text = self.main_notebook.tab(tab_id, 'text')
                    if "Default DB 관리" in tab_text or tab_text == "Default DB 관리":
                        self.update_log("⚠️ Default DB 관리 탭이 이미 존재함 - 기존 탭으로 이동")
                        self.main_notebook.select(tab_id)
                        return False
                except tk.TclError:
                    continue

        # 프레임 참조 체크
        if self.default_db_frame is not None:
            self.update_log("⚠️ Default DB 프레임 참조가 남아있음 - 초기화 후 재생성")
            self.default_db_frame = None

        # DBSchema 확인
        if not self.db_schema:
            self.update_log("❌ DBSchema가 초기화되지 않음 - 탭 생성 취소")
            return False

        self.default_db_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.default_db_frame, text="Default DB 관리")
        self.update_log("✅ Default DB 탭 프레임 생성 완료")
        return True

'''

    helper2 = '''    def _create_equipment_type_management_section(self, control_frame):
        """
        Equipment Type 관리 섹션을 생성합니다.
        Equipment Type 선택 및 Configuration 선택 UI를 포함합니다.

        Args:
            control_frame: 부모 제어 프레임
        """
        equipment_frame = ttk.LabelFrame(control_frame, text="Equipment Type Management", padding=12)
        equipment_frame.pack(fill=tk.X, pady=(0, 8))

        # 장비 유형 선택
        type_select_frame = ttk.Frame(equipment_frame)
        type_select_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(type_select_frame, text="Equipment Type:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
        self.equipment_type_var = tk.StringVar()
        self.equipment_type_combo = ttk.Combobox(type_select_frame, textvariable=self.equipment_type_var,
                                               state="readonly", width=40, font=("Segoe UI", 9))
        self.equipment_type_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.equipment_type_combo.bind("<<ComboboxSelected>>", self.on_equipment_type_selected)
        self.update_log("✅ 장비 유형 콤보박스 생성 완료")

        # 장비 유형 관리 버튼들
        type_buttons_frame = ttk.Frame(equipment_frame)
        type_buttons_frame.pack(fill=tk.X)

        add_type_btn = ttk.Button(type_buttons_frame, text="Add Equipment Type",
                                command=self.add_equipment_type_dialog, width=18)
        add_type_btn.pack(side=tk.LEFT, padx=(0, 6))

        delete_type_btn = ttk.Button(type_buttons_frame, text="Delete",
                                   command=self.delete_equipment_type, width=10)
        delete_type_btn.pack(side=tk.LEFT, padx=(0, 6))

        refresh_btn = ttk.Button(type_buttons_frame, text="Refresh",
                               command=self.refresh_equipment_types, width=10)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 6))

        # Configuration 선택 (Phase 1.5 Week 2 Day 4)
        config_select_frame = ttk.Frame(equipment_frame)
        config_select_frame.pack(fill=tk.X, pady=(8, 0))

        ttk.Label(config_select_frame, text="Configuration:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
        self.configuration_var = tk.StringVar()
        self.configuration_combo = ttk.Combobox(config_select_frame, textvariable=self.configuration_var,
                                               state="readonly", width=40, font=("Segoe UI", 9))
        self.configuration_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.configuration_combo.bind("<<ComboboxSelected>>", self.on_configuration_selected)

        # "All (Type Common)" 옵션 표시 레이블
        self.config_mode_label = ttk.Label(config_select_frame, text="", font=("Segoe UI", 9, "italic"), foreground="gray")
        self.config_mode_label.pack(side=tk.LEFT, padx=(0, 8))

        self.update_log("✅ Configuration 콤보박스 생성 완료")

'''

    helper3 = '''    def _create_parameter_management_section(self, control_frame):
        """
        Parameter 관리 섹션을 생성합니다.
        Parameter 추가/삭제/가져오기/내보내기 버튼을 포함합니다.

        Args:
            control_frame: 부모 제어 프레임
        """
        param_frame = ttk.LabelFrame(control_frame, text="Parameter Management", padding=12)
        param_frame.pack(fill=tk.X, pady=(0, 8))

        # 모든 관리 버튼들을 한 행에 배치
        mgmt_buttons_frame = ttk.Frame(param_frame)
        mgmt_buttons_frame.pack(fill=tk.X)

        # 4개 버튼을 한 행에 배치 - 버튼 크기 개선
        add_param_btn = ttk.Button(mgmt_buttons_frame, text="Add Parameter",
                                 command=self.add_parameter_dialog, width=13)
        add_param_btn.pack(side=tk.LEFT, padx=(0, 6))

        delete_param_btn = ttk.Button(mgmt_buttons_frame, text="Delete Selected",
                                    command=self.delete_selected_parameters, width=13)
        delete_param_btn.pack(side=tk.LEFT, padx=(0, 6))

        import_btn = ttk.Button(mgmt_buttons_frame, text="Import from Text File",
                              command=self.import_from_text_file, width=18)
        import_btn.pack(side=tk.LEFT, padx=(0, 6))

        export_btn = ttk.Button(mgmt_buttons_frame, text="Export to Text File",
                              command=self.export_to_text_file, width=16)
        export_btn.pack(side=tk.LEFT)

'''

    helper4 = '''    def _create_parameter_list_treeview(self):
        """
        Parameter List Treeview를 생성하고 설정합니다.
        컬럼 정의, 헤더, 스크롤바 및 이벤트 바인딩을 포함합니다.
        """
        # 파라미터 목록 트리뷰
        tree_container = ttk.LabelFrame(self.default_db_frame, text="Parameter List", padding=10)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 8))

        # 🔍 필터 패널 추가 (기존 메서드 사용)
        self._create_parameter_filter_panel(tree_container)

        tree_frame = ttk.Frame(tree_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 트리뷰 컬럼 정의 (Phase 1.5: Scope 컬럼 추가)
        columns = ("no", "parameter_name", "scope", "module", "part", "item_type", "default_value", "min_spec", "max_spec",
                  "is_performance", "description")

        self.default_db_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        self.update_log("✅ Default DB 트리뷰 생성 완료")

        # 컬럼 헤더 설정
        headers = {
            "no": "No.",
            "parameter_name": "ItemName",
            "scope": "Scope",
            "module": "Module",
            "part": "Part",
            "item_type": "Data Type",
            "default_value": "Default Value",
            "min_spec": "Min Spec",
            "max_spec": "Max Spec",
            "is_performance": "Check list",
            "description": "Description"
        }

        # 컬럼 너비 최적화
        column_widths = {
            "no": 50,
            "parameter_name": 200,
            "scope": 100,
            "module": 80,
            "part": 100,
            "item_type": 85,
            "default_value": 100,
            "min_spec": 80,
            "max_spec": 80,
            "is_performance": 90,
            "description": 150
        }

        for col in columns:
            self.default_db_tree.heading(col, text=headers[col])
            self.default_db_tree.column(col, width=column_widths[col], minwidth=50)

        # 스크롤바 추가
        db_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.default_db_tree.yview)
        self.default_db_tree.configure(yscrollcommand=db_scrollbar.set)

        db_h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.default_db_tree.xview)
        self.default_db_tree.configure(xscrollcommand=db_h_scrollbar.set)

        # 배치
        self.default_db_tree.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=(0, 2))
        db_scrollbar.grid(row=0, column=1, sticky="ns", pady=(0, 2))
        db_h_scrollbar.grid(row=1, column=0, sticky="ew", padx=(0, 2))

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # 더블클릭으로 편집
        self.default_db_tree.bind("<Double-1>", self.edit_parameter_dialog)

        # 우클릭 메뉴
        self.create_default_db_context_menu()
        self.default_db_tree.bind("<Button-3>", self.show_default_db_context_menu)

        # 필터 기능 초기화
        self._initialize_parameter_filter_functionality()

'''

    helper5 = '''    def _create_default_db_status_bar(self):
        """
        Default DB 탭 하단 상태 표시줄을 생성합니다.
        """
        status_container = ttk.LabelFrame(self.default_db_frame, text="Status Information", padding=10)
        status_container.pack(fill=tk.X, padx=15, pady=(0, 8))

        status_frame = ttk.Frame(status_container)
        status_frame.pack(fill=tk.X)

        # 상태 메시지
        self.default_db_status_label = ttk.Label(status_frame, text="Please select an equipment type.",
                                               font=("Segoe UI", 9))
        self.default_db_status_label.pack(side=tk.LEFT)

        # Performance 통계 표시
        self.performance_stats_label = ttk.Label(status_frame, text="",
                                               foreground="#2E5BBA", font=("Segoe UI", 9, "bold"))
        self.performance_stats_label.pack(side=tk.RIGHT)

        self.update_log("✅ Default DB 상태 표시줄 생성 완료")

'''

    return helper1 + helper2 + helper3 + helper4 + helper5


def refactor_create_default_db_tab(content):
    """
    Refactor create_default_db_tab method
    """

    # Insert helper methods before create_default_db_tab
    helpers = create_helper_methods()
    pattern = r'(\n    def create_default_db_tab\(self\):)'
    content = re.sub(pattern, '\n' + helpers + r'\1', content, count=1)

    # Find and replace the method body
    # Read the old method first
    old_method_start = '''    def create_default_db_tab(self):
        """Default DB 관리 탭 생성 - 중복 생성 방지 강화"""
        try:
            self.update_log("🔧 Default DB 관리 탭 생성 시작...")

            # 기존 탭 중복 검사 강화
            if hasattr(self, 'main_notebook') and self.main_notebook:
                for tab_id in range(self.main_notebook.index('end')):
                    try:
                        tab_text = self.main_notebook.tab(tab_id, 'text')
                        if "Default DB 관리" in tab_text or tab_text == "Default DB 관리":
                            self.update_log("⚠️ Default DB 관리 탭이 이미 존재함 - 기존 탭으로 이동")
                            self.main_notebook.select(tab_id)
                            return
                    except tk.TclError:
                        continue

            # 프레임 참조 체크
            if self.default_db_frame is not None:
                self.update_log("⚠️ Default DB 프레임 참조가 남아있음 - 초기화 후 재생성")
                self.default_db_frame = None

            # DBSchema 확인
            if not self.db_schema:
                self.update_log("❌ DBSchema가 초기화되지 않음 - 탭 생성 취소")
                return

            self.default_db_frame = ttk.Frame(self.main_notebook)
            self.main_notebook.add(self.default_db_frame, text="Default DB 관리")
            self.update_log("✅ Default DB 탭 프레임 생성 완료")

            # 상단 제어 패널 - 배경색과 패딩 개선
            control_frame = ttk.Frame(self.default_db_frame, style="Control.TFrame")
            control_frame.pack(fill=tk.X, padx=15, pady=10)

            # 장비 유형 관리 섹션
            equipment_frame = ttk.LabelFrame(control_frame, text="Equipment Type Management", padding=12)
            equipment_frame.pack(fill=tk.X, pady=(0, 8))

            # 장비 유형 선택
            type_select_frame = ttk.Frame(equipment_frame)
            type_select_frame.pack(fill=tk.X, pady=(0, 8))

            ttk.Label(type_select_frame, text="Equipment Type:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
            self.equipment_type_var = tk.StringVar()
            self.equipment_type_combo = ttk.Combobox(type_select_frame, textvariable=self.equipment_type_var,
                                                   state="readonly", width=40, font=("Segoe UI", 9))
            self.equipment_type_combo.pack(side=tk.LEFT, padx=(0, 12))
            self.equipment_type_combo.bind("<<ComboboxSelected>>", self.on_equipment_type_selected)
            self.update_log("✅ 장비 유형 콤보박스 생성 완료")

            # 장비 유형 관리 버튼들
            type_buttons_frame = ttk.Frame(equipment_frame)
            type_buttons_frame.pack(fill=tk.X)

            add_type_btn = ttk.Button(type_buttons_frame, text="Add Equipment Type",
                                    command=self.add_equipment_type_dialog, width=18)
            add_type_btn.pack(side=tk.LEFT, padx=(0, 6))

            delete_type_btn = ttk.Button(type_buttons_frame, text="Delete",
                                       command=self.delete_equipment_type, width=10)
            delete_type_btn.pack(side=tk.LEFT, padx=(0, 6))

            refresh_btn = ttk.Button(type_buttons_frame, text="Refresh",
                                   command=self.refresh_equipment_types, width=10)
            refresh_btn.pack(side=tk.LEFT, padx=(0, 6))

            # Configuration 선택 (Phase 1.5 Week 2 Day 4)
            config_select_frame = ttk.Frame(equipment_frame)
            config_select_frame.pack(fill=tk.X, pady=(8, 0))

            ttk.Label(config_select_frame, text="Configuration:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
            self.configuration_var = tk.StringVar()
            self.configuration_combo = ttk.Combobox(config_select_frame, textvariable=self.configuration_var,
                                                   state="readonly", width=40, font=("Segoe UI", 9))
            self.configuration_combo.pack(side=tk.LEFT, padx=(0, 12))
            self.configuration_combo.bind("<<ComboboxSelected>>", self.on_configuration_selected)

            # "All (Type Common)" 옵션 표시 레이블
            self.config_mode_label = ttk.Label(config_select_frame, text="", font=("Segoe UI", 9, "italic"), foreground="gray")
            self.config_mode_label.pack(side=tk.LEFT, padx=(0, 8))

            self.update_log("✅ Configuration 콤보박스 생성 완료")

            # 파라미터 관리 섹션
            param_frame = ttk.LabelFrame(control_frame, text="Parameter Management", padding=12)
            param_frame.pack(fill=tk.X, pady=(0, 8))

            # 모든 관리 버튼들을 한 행에 배치
            mgmt_buttons_frame = ttk.Frame(param_frame)
            mgmt_buttons_frame.pack(fill=tk.X)

            # 4개 버튼을 한 행에 배치 - 버튼 크기 개선
            add_param_btn = ttk.Button(mgmt_buttons_frame, text="Add Parameter",
                                     command=self.add_parameter_dialog, width=13)
            add_param_btn.pack(side=tk.LEFT, padx=(0, 6))

            delete_param_btn = ttk.Button(mgmt_buttons_frame, text="Delete Selected",
                                        command=self.delete_selected_parameters, width=13)
            delete_param_btn.pack(side=tk.LEFT, padx=(0, 6))

            import_btn = ttk.Button(mgmt_buttons_frame, text="Import from Text File",
                                  command=self.import_from_text_file, width=18)
            import_btn.pack(side=tk.LEFT, padx=(0, 6))

            export_btn = ttk.Button(mgmt_buttons_frame, text="Export to Text File",
                                  command=self.export_to_text_file, width=16)
            export_btn.pack(side=tk.LEFT)

            # Excel 기능 제거됨

            # 파라미터 목록 트리뷰
            tree_container = ttk.LabelFrame(self.default_db_frame, text="Parameter List", padding=10)
            tree_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 8))

            # 🔍 필터 패널 추가 (새로운 기능)
            self._create_parameter_filter_panel(tree_container)

            tree_frame = ttk.Frame(tree_container)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            # 트리뷰 컬럼 정의 (Phase 1.5: Scope 컬럼 추가)
            columns = ("no", "parameter_name", "scope", "module", "part", "item_type", "default_value", "min_spec", "max_spec",
                      "is_performance", "description")

            self.default_db_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
            self.update_log("✅ Default DB 트리뷰 생성 완료")

            # 컬럼 헤더 설정
            headers = {
                "no": "No.",  # 순차 번호 컬럼
                "parameter_name": "ItemName",
                "scope": "Scope",  # Phase 1.5: Type Common vs Configuration
                "module": "Module",
                "part": "Part",
                "item_type": "Data Type",
                "default_value": "Default Value",
                "min_spec": "Min Spec",
                "max_spec": "Max Spec",
                "is_performance": "Check list",
                "description": "Description"
            }

            # 컬럼 너비 최적화
            column_widths = {
                "no": 50,  # 순차 번호 컬럼 너비
                "parameter_name": 200,  # 약간 줄임
                "scope": 100,  # Scope 컬럼
                "module": 80,
                "part": 100,
                "item_type": 85,
                "default_value": 100,
                "min_spec": 80,
                "max_spec": 80,
                "is_performance": 90,
                "description": 150
            }

            for col in columns:
                self.default_db_tree.heading(col, text=headers[col])
                self.default_db_tree.column(col, width=column_widths[col], minwidth=50)

            # 스크롤바 추가 - 스타일 개선
            db_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.default_db_tree.yview)
            self.default_db_tree.configure(yscrollcommand=db_scrollbar.set)

            db_h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.default_db_tree.xview)
            self.default_db_tree.configure(xscrollcommand=db_h_scrollbar.set)

            # 배치 - 간격 조정
            self.default_db_tree.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=(0, 2))
            db_scrollbar.grid(row=0, column=1, sticky="ns", pady=(0, 2))
            db_h_scrollbar.grid(row=1, column=0, sticky="ew", padx=(0, 2))

            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # 더블클릭으로 편집
            self.default_db_tree.bind("<Double-1>", self.edit_parameter_dialog)

            # 🆕 우클릭 메뉴 추가
            self.create_default_db_context_menu()
            self.default_db_tree.bind("<Button-3>", self.show_default_db_context_menu)

            # 🔍 필터 기능 초기화 (새로운 기능)
            self._initialize_parameter_filter_functionality()

            # 상태 표시줄
            status_container = ttk.LabelFrame(self.default_db_frame, text="Status Information", padding=10)
            status_container.pack(fill=tk.X, padx=15, pady=(0, 8))

            status_frame = ttk.Frame(status_container)
            status_frame.pack(fill=tk.X)

            # 상태 메시지
            self.default_db_status_label = ttk.Label(status_frame, text="Please select an equipment type.",
                                                   font=("Segoe UI", 9))
            self.default_db_status_label.pack(side=tk.LEFT)

            # Performance 통계 표시
            self.performance_stats_label = ttk.Label(status_frame, text="",
                                                   foreground="#2E5BBA", font=("Segoe UI", 9, "bold"))
            self.performance_stats_label.pack(side=tk.RIGHT)

            self.update_log("✅ Default DB 상태 표시줄 생성 완료")

            # 초기 데이터 로드 (UI 초기화 완료 후 실행)
            self.window.after(200, self.refresh_equipment_types)

            # 디버깅을 위한 로그 추가
            self.update_log("✅ Default DB 관리 탭이 완전히 생성되었습니다.")'''

    new_method = '''    def create_default_db_tab(self):
        """Default DB 관리 탭 생성 - 중복 생성 방지 강화"""
        try:
            self.update_log("🔧 Default DB 관리 탭 생성 시작...")

            # 탭 프레임 초기화
            if not self._initialize_default_db_tab_frame():
                return

            # 상단 제어 패널
            control_frame = ttk.Frame(self.default_db_frame, style="Control.TFrame")
            control_frame.pack(fill=tk.X, padx=15, pady=10)

            # Equipment Type 관리 섹션 생성
            self._create_equipment_type_management_section(control_frame)

            # Parameter 관리 섹션 생성
            self._create_parameter_management_section(control_frame)

            # Parameter List Treeview 생성
            self._create_parameter_list_treeview()

            # 상태 표시줄 생성
            self._create_default_db_status_bar()

            # 초기 데이터 로드 (UI 초기화 완료 후 실행)
            self.window.after(200, self.refresh_equipment_types)

            self.update_log("✅ Default DB 관리 탭이 완전히 생성되었습니다.")'''

    content = content.replace(old_method_start, new_method)

    return content


def main():
    input_file = '/home/user/DB_Manager-v2/src/app/manager.py'

    # Read the file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Perform refactoring
    print("Refactoring create_default_db_tab method...")
    content = refactor_create_default_db_tab(content)

    # Write back
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Refactoring complete!")
    print("  - Added 5 new helper methods")
    print("  - Simplified create_default_db_tab method")


if __name__ == '__main__':
    main()
