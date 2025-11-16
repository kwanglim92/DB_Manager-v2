"""
Comparison Tab - UI 컴포넌트

이 모듈은 manager.py에서 비교 관련 UI를 분리한 것입니다.
3개의 서브 탭을 관리합니다:
- Grid View Tab (메인 비교) - 계층 구조 트리뷰
- Full List Tab (전체 목록) - 플랫 리스트 + 필터/검색
- Diff Only Tab (차이점 분석) - 차이점만 표시

Phase: 중기 계획 Week 1-2 (UI/로직 분리)
Status: 🚧 진행중 - 스켈레톤 구현 완료, 점진적 마이그레이션 필요
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, List, Dict, Any


class ComparisonTab:
    """
    비교 탭 UI 컴포넌트

    책임:
    - 3개 비교 서브 탭 관리 (Grid View, Full List, Diff Only)
    - 파일 비교 결과 시각화
    - 검색 및 필터링 기능
    - Context 메뉴 관리
    - Default DB로 전송 기능 (관리자 모드)

    의존성:
    - DBManager: 부모 컨트롤러 (데이터 및 설정 접근)
    - merged_df: 병합된 비교 데이터
    - file_names: 비교 중인 파일 목록
    - maint_mode: 관리자 모드 플래그
    """

    def __init__(self, parent_manager, notebook: ttk.Notebook):
        """
        초기화

        Args:
            parent_manager: DBManager 인스턴스 (부모 컨트롤러)
            notebook: 탭을 추가할 Notebook 위젯
        """
        self.manager = parent_manager
        self.notebook = notebook
        self.logger = logging.getLogger(self.__class__.__name__)

        # UI 변수들
        self.search_var = tk.StringVar()
        self.search_result_label = None
        self.comparison_advanced_filter_visible = tk.BooleanVar(value=False)
        self.select_all_var = tk.BooleanVar(value=False)

        # Filter variables
        self.comparison_module_filter_var = tk.StringVar()
        self.comparison_part_filter_var = tk.StringVar()

        # Tree view widgets
        self.comparison_tree = None
        self.grid_tree = None
        self.diff_only_tree = None

        # Labels
        self.diff_count_label = None
        self.selected_count_label = None
        self.comparison_filter_result_label = None

        # Buttons
        self.send_to_default_btn = None
        self.comparison_toggle_advanced_btn = None

        # Context menu
        self.context_menu = None

        # Item checkboxes (for maintenance mode)
        self.item_checkboxes = {}

        # Create all tabs
        self._create_all_tabs()

        self.logger.info("ComparisonTab initialized successfully")

    def _create_all_tabs(self):
        """모든 비교 서브 탭 생성"""
        self.create_grid_view_tab()
        self.create_full_list_tab()
        self.create_diff_only_tab()

        # Context 메뉴 생성 (Full List Tab에서 사용)
        self.create_comparison_context_menu()

    # ==================== Grid View Tab (메인 비교) ====================

    def create_grid_view_tab(self):
        """
        격자뷰 탭 생성 - 트리뷰 구조

        계층 구조: Module → Part → ItemName
        각 레벨별로 통계 정보 표시 (total params, diff count)

        TODO: manager.py:1380-1630 코드 이관 필요 (약 250 lines)
        - _configure_grid_view_tags()
        - _build_grid_hierarchy_data()
        - _populate_grid_tree()
        - update_grid_view()
        """
        grid_frame = ttk.Frame(self.notebook)
        self.notebook.add(grid_frame, text="📊 메인 비교")

        # 상단 정보 패널
        info_frame = ttk.Frame(grid_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        # 통계 정보 라벨들
        self.grid_total_label = ttk.Label(info_frame, text="총 파라미터: 0")
        self.grid_total_label.pack(side=tk.LEFT, padx=10)

        self.grid_modules_label = ttk.Label(info_frame, text="모듈 수: 0")
        self.grid_modules_label.pack(side=tk.LEFT, padx=10)

        self.grid_parts_label = ttk.Label(info_frame, text="파트 수: 0")
        self.grid_parts_label.pack(side=tk.LEFT, padx=10)

        self.grid_diff_label = ttk.Label(info_frame, text="값이 다른 항목: 0", foreground="red")
        self.grid_diff_label.pack(side=tk.RIGHT, padx=10)

        # 메인 트리뷰 생성
        self.grid_tree = ttk.Treeview(grid_frame, selectmode="extended")

        # 동적 컬럼 설정
        file_names = getattr(self.manager, 'file_names', [])
        if file_names:
            columns = tuple(file_names)
        else:
            columns = ("값",)

        self.grid_tree["columns"] = columns
        self.grid_tree.heading("#0", text="구조", anchor="w")
        self.grid_tree.column("#0", width=250, anchor="w")

        for col in columns:
            self.grid_tree.heading(col, text=col, anchor="center")
            self.grid_tree.column(col, width=150, anchor="center")

        # 스크롤바 추가
        v_scroll = ttk.Scrollbar(grid_frame, orient="vertical", command=self.grid_tree.yview)
        h_scroll = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.grid_tree.xview)
        self.grid_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.grid_tree.pack(expand=True, fill=tk.BOTH)

        self.logger.info("Grid View Tab created")

    # ==================== Full List Tab (전체 목록) ====================

    def create_full_list_tab(self):
        """
        전체 목록 탭 생성 - 플랫 리스트 + 필터/검색

        manager.py:1632-1741에서 이관
        """
        comparison_frame = ttk.Frame(self.notebook)
        self.notebook.add(comparison_frame, text="📋 전체 목록")

        # 스타일 설정
        style = ttk.Style()
        style.configure("Custom.Treeview", rowheight=22)

        # 상단 검색 및 제어 패널
        top_frame = ttk.Frame(comparison_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        # 검색 기능 (좌측)
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(search_frame, text="🔎 Search:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 5))

        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self.on_search_changed)

        self.search_clear_btn = ttk.Button(search_frame, text="Clear", command=self.clear_search, width=8)
        self.search_clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.search_result_label = ttk.Label(search_frame, text="", foreground="#1976D2", font=('Segoe UI', 8))
        self.search_result_label.pack(side=tk.LEFT, padx=(5, 0))

        # 필터 컨트롤 영역
        self.comparison_advanced_filter_visible = tk.BooleanVar(value=False)

        control_frame = ttk.Frame(search_frame)
        control_frame.pack(side=tk.RIGHT, padx=(10, 0))

        # 결과 표시 레이블
        self.comparison_filter_result_label = ttk.Label(control_frame, text="", foreground="#1976D2", font=('Segoe UI', 8))
        self.comparison_filter_result_label.pack(side=tk.LEFT, padx=(0, 10))

        # Advanced Filter 토글 버튼
        self.comparison_toggle_advanced_btn = ttk.Button(
            control_frame,
            text="▼ Filters",
            command=self._toggle_comparison_advanced_filters
        )
        self.comparison_toggle_advanced_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Reset 버튼
        filter_reset_btn = ttk.Button(control_frame, text="Reset", command=self._reset_comparison_filters)
        filter_reset_btn.pack(side=tk.LEFT)

        # 고급 필터 패널 생성
        self._create_comparison_filter_panel(comparison_frame)

        # 제어 프레임
        control_frame = ttk.Frame(comparison_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        maint_mode = getattr(self.manager, 'maint_mode', False)

        if maint_mode:
            self.select_all_var = tk.BooleanVar(value=False)
            self.select_all_cb = ttk.Checkbutton(
                control_frame,
                text="모두 선택",
                variable=self.select_all_var,
                command=self.toggle_select_all_checkboxes
            )
            self.select_all_cb.pack(side=tk.LEFT, padx=5)

        if maint_mode:
            self.selected_count_label = ttk.Label(control_frame, text="선택된 항목: 0개")
            self.selected_count_label.pack(side=tk.RIGHT, padx=10)
            self.send_to_default_btn = ttk.Button(
                control_frame,
                text="Default DB로 전송",
                command=self.add_to_default_db
            )
            self.send_to_default_btn.pack(side=tk.RIGHT, padx=10)
        else:
            self.diff_count_label = ttk.Label(control_frame, text="값이 다른 항목: 0개")
            self.diff_count_label.pack(side=tk.RIGHT, padx=10)

        # 트리뷰 생성
        file_names = getattr(self.manager, 'file_names', [])
        if maint_mode:
            columns = ["Checkbox", "Module", "Part", "ItemName"] + file_names
        else:
            columns = ["Module", "Part", "ItemName"] + file_names

        self.comparison_tree = ttk.Treeview(comparison_frame, selectmode="extended", style="Custom.Treeview")
        self.comparison_tree["columns"] = columns
        self.comparison_tree.heading("#0", text="", anchor="w")
        self.comparison_tree.column("#0", width=0, stretch=False)

        col_offset = 0
        if maint_mode:
            self.comparison_tree.heading("Checkbox", text="선택")
            self.comparison_tree.column("Checkbox", width=50, anchor="center")
            col_offset = 1

        for col in ["Module", "Part", "ItemName"]:
            self.comparison_tree.heading(col, text=col, anchor="w")
            self.comparison_tree.column(col, width=100)

        for model in file_names:
            self.comparison_tree.heading(model, text=model, anchor="w")
            self.comparison_tree.column(model, width=150)

        # 스크롤바
        v_scroll = ttk.Scrollbar(comparison_frame, orient="vertical", command=self.comparison_tree.yview)
        h_scroll = ttk.Scrollbar(comparison_frame, orient="horizontal", command=self.comparison_tree.xview)
        self.comparison_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.comparison_tree.pack(expand=True, fill=tk.BOTH)

        # 이벤트 바인딩
        self.comparison_tree.bind("<<TreeviewSelect>>", self.update_selected_count)

        # TODO: Context 메뉴 추가 (Day 4)

        self.logger.info("Full List Tab created")

    # ==================== Diff Only Tab (차이점 분석) ====================

    def create_diff_only_tab(self):
        """
        차이점만 보기 탭 생성

        값이 다른 항목만 필터링하여 표시

        TODO: manager.py:1128-1215 코드 이관 필요 (약 90 lines)
        - update_diff_only_view()
        """
        diff_tab = ttk.Frame(self.notebook)
        self.notebook.add(diff_tab, text="🔍 차이점 분석")

        # 상단 정보 패널
        control_frame = ttk.Frame(diff_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.diff_only_count_label = ttk.Label(control_frame, text="값이 다른 항목: 0개")
        self.diff_only_count_label.pack(side=tk.RIGHT, padx=10)

        # 트리뷰 생성
        file_names = getattr(self.manager, 'file_names', [])
        if file_names:
            columns = ["Module", "Part", "ItemName"] + file_names
        else:
            columns = ["Module", "Part", "ItemName"]

        self.diff_only_tree = ttk.Treeview(diff_tab, columns=columns, show="headings", selectmode="extended")

        # 헤딩 설정
        for col in columns:
            self.diff_only_tree.heading(col, text=col)
            if col in ["Module", "Part", "ItemName"]:
                self.diff_only_tree.column(col, width=120)
            else:
                self.diff_only_tree.column(col, width=150)

        # 스크롤바
        v_scroll = ttk.Scrollbar(diff_tab, orient="vertical", command=self.diff_only_tree.yview)
        h_scroll = ttk.Scrollbar(diff_tab, orient="horizontal", command=self.diff_only_tree.xview)
        self.diff_only_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.diff_only_tree.pack(expand=True, fill=tk.BOTH)

        self.logger.info("Diff Only Tab created")

    # ==================== Grid View Update Methods ====================

    def update_grid_view(self):
        """격자뷰 데이터 업데이트 - 트리뷰 구조

        manager.py:1598-1630에서 이관
        """
        if not hasattr(self, 'grid_tree') or self.grid_tree is None:
            return

        # 기존 데이터 삭제
        self._clear_treeview(self.grid_tree)

        merged_df = getattr(self.manager, 'merged_df', None)
        if merged_df is None or merged_df.empty:
            # 통계 정보 초기화
            if hasattr(self, 'grid_total_label'):
                self.grid_total_label.config(text="총 파라미터: 0")
                self.grid_modules_label.config(text="모듈 수: 0")
                self.grid_parts_label.config(text="파트 수: 0")
                self.grid_diff_label.config(text="값이 다른 항목: 0")
            return

        # 동적 컬럼 업데이트
        file_names = getattr(self.manager, 'file_names', [])
        columns = tuple(file_names) if file_names else ("값",)
        self.grid_tree["columns"] = columns

        # 컬럼 헤딩 업데이트
        for col in columns:
            self.grid_tree.heading(col, text=col, anchor="center")
            self.grid_tree.column(col, width=150, anchor="center")

        # 계층별 스타일 태그 설정
        self._configure_grid_view_tags()

        # 계층 구조 데이터 구성
        modules_data, total_params, diff_count = self._build_grid_hierarchy_data(columns)

        # 트리뷰에 계층 구조로 데이터 추가 및 통계 업데이트
        self._populate_grid_tree(modules_data, columns, diff_count)

        self.logger.debug(f"Grid view updated: {total_params} params, {diff_count} diffs")

    def _configure_grid_view_tags(self):
        """계층별 스타일 태그 설정 (Grid View)

        manager.py:1438-1480에서 이관
        """
        # 모듈 레벨 - 가장 크고 굵게 (기본 파란색)
        self.grid_tree.tag_configure("module",
                                    font=("Arial", 11, "bold"),
                                    background="#F5F5F5",
                                    foreground="#1565C0")

        # 모듈 레벨 - 차이 있음 (빨간색 강조)
        self.grid_tree.tag_configure("module_diff",
                                    font=("Arial", 11, "bold"),
                                    background="#F5F5F5",
                                    foreground="#D32F2F")

        # 파트 레벨 - 중간 크기, 볼드
        self.grid_tree.tag_configure("part",
                                    font=("Arial", 10, "bold"),
                                    background="#FAFAFA",
                                    foreground="#424242")

        # 파트 레벨 - 모든 값 동일 (초록색)
        self.grid_tree.tag_configure("part_clean",
                                    font=("Arial", 10, "bold"),
                                    background="#FAFAFA",
                                    foreground="#2E7D32")

        # 파트 레벨 - 차이 있음 (빨간색 강조)
        self.grid_tree.tag_configure("part_diff",
                                    font=("Arial", 10, "bold"),
                                    background="#FAFAFA",
                                    foreground="#D32F2F")

        # 파라미터 레벨 - 기본 크기
        self.grid_tree.tag_configure("parameter_same",
                                    font=("Arial", 9),
                                    background="white",
                                    foreground="black")

        # 차이점이 있는 파라미터
        self.grid_tree.tag_configure("parameter_different",
                                    font=("Arial", 9),
                                    background="#FFECB3",
                                    foreground="#E65100")

    def _build_grid_hierarchy_data(self, columns):
        """계층 구조 데이터 구성 (Grid View)

        manager.py:1482-1521에서 이관

        Returns:
            tuple: (modules_data, total_params, diff_count)
        """
        modules_data = {}
        total_params = 0
        diff_count = 0

        merged_df = getattr(self.manager, 'merged_df', None)
        file_names = getattr(self.manager, 'file_names', [])

        if merged_df is None or merged_df.empty:
            return modules_data, total_params, diff_count

        grouped = merged_df.groupby(["Module", "Part", "ItemName"])

        for (module, part, item_name), group in grouped:
            if module not in modules_data:
                modules_data[module] = {}
            if part not in modules_data[module]:
                modules_data[module][part] = {}

            # 각 파일별 값 수집
            values = []
            for model in file_names:
                model_data = group[group["Model"] == model]
                if not model_data.empty:
                    values.append(str(model_data["ItemValue"].iloc[0]))
                else:
                    values.append("-")

            # 값 차이 확인 (빈 값 제외)
            non_empty_values = [v for v in values if v != "-"]
            has_difference = len(set(non_empty_values)) > 1 if len(non_empty_values) > 1 else False

            modules_data[module][part][item_name] = {
                "values": values,
                "has_difference": has_difference
            }
            total_params += 1
            if has_difference:
                diff_count += 1

        return modules_data, total_params, diff_count

    def _populate_grid_tree(self, modules_data, columns, diff_count):
        """트리뷰에 계층 구조로 데이터 추가 및 통계 업데이트

        manager.py:1523-1596에서 이관
        """
        # 트리뷰에 계층 구조로 데이터 추가
        for module_name in sorted(modules_data.keys()):
            # 모듈 레벨 통계 계산
            module_total = sum(len(modules_data[module_name][part]) for part in modules_data[module_name])
            module_diff = sum(1 for part in modules_data[module_name]
                            for item in modules_data[module_name][part]
                            if modules_data[module_name][part][item]["has_difference"])

            # 모듈 표시
            if module_diff == 0:
                module_text = f"📁 {module_name} ({module_total})"
            else:
                module_text = f"📁 {module_name} ({module_total}) Diff: {module_diff}"
            module_tag = "module"

            # 모듈 노드 추가
            module_node = self.grid_tree.insert("", "end",
                                               text=module_text,
                                               values=[""] * len(columns),
                                               open=True,
                                               tags=(module_tag,))

            for part_name in sorted(modules_data[module_name].keys()):
                # 파트 레벨 통계 계산
                part_total = len(modules_data[module_name][part_name])
                part_diff = sum(1 for item in modules_data[module_name][part_name]
                              if modules_data[module_name][part_name][item]["has_difference"])

                # 파트 표시 - 차이가 없으면 초록색, 있으면 회색
                if part_diff == 0:
                    part_text = f"📂 {part_name} ({part_total})"
                    part_tag = "part_clean"
                else:
                    part_text = f"📂 {part_name} ({part_total}) Diff: {part_diff}"
                    part_tag = "part_diff"

                # 파트 노드 추가
                part_node = self.grid_tree.insert(module_node, "end",
                                                 text=part_text,
                                                 values=[""] * len(columns),
                                                 open=True,
                                                 tags=(part_tag,))

                for item_name in sorted(modules_data[module_name][part_name].keys()):
                    # 파라미터 노드 추가
                    item_data = modules_data[module_name][part_name][item_name]
                    values = item_data["values"]
                    has_difference = item_data["has_difference"]

                    # 태그 선택
                    tag = "parameter_different" if has_difference else "parameter_same"

                    self.grid_tree.insert(part_node, "end",
                                        text=item_name,
                                        values=values,
                                        tags=(tag,))

        # 통계 정보 업데이트
        total_params = sum(len(parts_data)
                          for module_data in modules_data.values()
                          for parts_data in module_data.values())

        if hasattr(self, 'grid_total_label'):
            self.grid_total_label.config(text=f"총 파라미터: {total_params}")
            self.grid_modules_label.config(text=f"모듈 수: {len(modules_data)}")

            total_parts = sum(len(parts) for parts in modules_data.values())
            self.grid_parts_label.config(text=f"파트 수: {total_parts}")

            # 차이점 개수도 표시
            if hasattr(self, 'grid_diff_label'):
                self.grid_diff_label.config(text=f"값이 다른 항목: {diff_count}")

    # ==================== Diff Only Tab Update Methods ====================

    def update_diff_only_view(self):
        """차이점만 보기 탭 업데이트

        manager.py:1169-1214에서 이관
        """
        if not hasattr(self, 'diff_only_tree') or self.diff_only_tree is None:
            return

        # 기존 데이터 삭제
        self._clear_treeview(self.diff_only_tree)

        diff_count = 0
        merged_df = getattr(self.manager, 'merged_df', None)
        file_names = getattr(self.manager, 'file_names', [])

        if merged_df is not None and not merged_df.empty:
            # 컬럼 업데이트
            columns = ["Module", "Part", "ItemName"] + file_names
            self.diff_only_tree["columns"] = columns

            for col in columns:
                self.diff_only_tree.heading(col, text=col)
                if col in ["Module", "Part", "ItemName"]:
                    self.diff_only_tree.column(col, width=120)
                else:
                    self.diff_only_tree.column(col, width=150)

            grouped = merged_df.groupby(["Module", "Part", "ItemName"])

            for (module, part, item_name), group in grouped:
                # 각 파일별 값 추출
                file_values = {}
                for model in file_names:
                    model_data = group[group["Model"] == model]
                    if not model_data.empty:
                        file_values[model] = str(model_data["ItemValue"].iloc[0])
                    else:
                        file_values[model] = "-"

                # 차이점이 있는지 확인
                unique_values = set(v for v in file_values.values() if v != "-")
                if len(unique_values) > 1:
                    # 차이점이 있는 항목만 추가
                    row_values = [module, part, item_name]
                    row_values.extend([file_values.get(model, "-") for model in file_names])

                    self.diff_only_tree.insert("", "end", values=row_values)
                    diff_count += 1

        # 차이점 카운트 업데이트
        if hasattr(self, 'diff_only_count_label'):
            self.diff_only_count_label.config(text=f"값이 다른 항목: {diff_count}개")

        self.logger.debug(f"Diff only view updated: {diff_count} differences found")

    # ==================== Helper Methods ====================

    def _clear_treeview(self, treeview):
        """Treeview의 모든 항목 제거

        manager.py:289-297에서 이관

        Args:
            treeview (ttk.Treeview): 제거할 Treeview 객체
        """
        if treeview is None:
            return

        for item in treeview.get_children():
            treeview.delete(item)

    # ==================== Filter Panel Methods ====================

    def _create_comparison_filter_panel(self, parent_frame):
        """전체 목록 탭 필터 패널 생성

        manager.py:1743-1766에서 이관
        """
        try:
            # 메인 필터 컨테이너 프레임
            self.comparison_main_filter_container = ttk.Frame(parent_frame)
            self.comparison_main_filter_container.pack(fill=tk.X, pady=(0, 5), padx=10)

            # 구분선 추가
            separator = ttk.Separator(self.comparison_main_filter_container, orient='horizontal')
            separator.pack(fill=tk.X, pady=(5, 8))

            # 고급 필터 패널 (처음에는 숨김)
            self.comparison_advanced_filter_frame = ttk.Frame(self.comparison_main_filter_container)

            # 고급 필터 내용 생성
            self._create_comparison_advanced_filters()

            self.logger.debug("Filter panel created - advanced filter hidden by default")

        except Exception as e:
            self.logger.error(f"Comparison filter panel error: {e}")
            import traceback
            traceback.print_exc()

    def _create_comparison_advanced_filters(self):
        """전체 목록 탭 고급 필터 생성

        manager.py:1768-1805에서 이관
        """
        try:
            # 구분선
            filter_separator = ttk.Separator(self.comparison_advanced_filter_frame, orient='horizontal')
            filter_separator.pack(fill=tk.X, pady=(5, 8))

            # 필터 행
            filters_row = ttk.Frame(self.comparison_advanced_filter_frame)
            filters_row.pack(fill=tk.X, pady=(0, 8))

            # Module Filter
            module_frame = ttk.Frame(filters_row)
            module_frame.pack(side=tk.LEFT, padx=(0, 20))

            ttk.Label(module_frame, text="Module:", font=('Segoe UI', 8)).pack(anchor='w')
            self.comparison_module_filter_var = tk.StringVar()
            self.comparison_module_filter_combo = ttk.Combobox(module_frame, textvariable=self.comparison_module_filter_var,
                                                      state="readonly", width=12, font=('Segoe UI', 8))
            self.comparison_module_filter_combo.pack()
            self.comparison_module_filter_combo.bind('<<ComboboxSelected>>', self._apply_comparison_filters)

            # Part Filter
            part_frame = ttk.Frame(filters_row)
            part_frame.pack(side=tk.LEFT, padx=(0, 20))

            ttk.Label(part_frame, text="Part:", font=('Segoe UI', 8)).pack(anchor='w')
            self.comparison_part_filter_var = tk.StringVar()
            self.comparison_part_filter_combo = ttk.Combobox(part_frame, textvariable=self.comparison_part_filter_var,
                                                    state="readonly", width=12, font=('Segoe UI', 8))
            self.comparison_part_filter_combo.pack()
            self.comparison_part_filter_combo.bind('<<ComboboxSelected>>', self._apply_comparison_filters)

        except Exception as e:
            self.logger.error(f"Comparison advanced filters error: {e}")

    def _toggle_comparison_advanced_filters(self):
        """전체 목록 탭 고급 필터 토글

        manager.py:1807-1831에서 이관
        """
        try:
            self.logger.debug(f"Toggle called - Current state: {self.comparison_advanced_filter_visible.get()}")

            if self.comparison_advanced_filter_visible.get():
                # 현재 보이는 상태 → 숨기기
                self.logger.debug("Hiding advanced filters")
                self.comparison_advanced_filter_frame.pack_forget()
                self.comparison_toggle_advanced_btn.config(text="▼ Filters")
                self.comparison_advanced_filter_visible.set(False)
            else:
                # 현재 숨겨진 상태 → 보이기
                self.logger.debug("Showing advanced filters")
                self.comparison_advanced_filter_frame.pack(fill=tk.X, pady=(0, 5))
                self.comparison_toggle_advanced_btn.config(text="▲ Filters")
                self.comparison_advanced_filter_visible.set(True)

            # UI 업데이트 강제 실행
            if hasattr(self, 'comparison_main_filter_container'):
                self.comparison_main_filter_container.update_idletasks()
            if hasattr(self, 'manager') and hasattr(self.manager, 'window'):
                self.manager.window.update_idletasks()

            self.logger.debug(f"Toggle complete - New state: {self.comparison_advanced_filter_visible.get()}")

        except Exception as e:
            self.logger.error(f"Toggle filters error: {e}")

    def _apply_comparison_filters(self, *args):
        """전체 목록 탭 필터 적용

        manager.py:1838-1845에서 이관
        """
        try:
            # 기존 검색 필터와 함께 Module, Part 필터 적용
            self.on_search_changed()

        except Exception as e:
            self.logger.error(f"Comparison filters apply error: {e}")

    def _reset_comparison_filters(self):
        """전체 목록 탭 모든 필터 초기화

        manager.py:1847-1864에서 이관
        """
        try:
            # 검색 초기화
            if hasattr(self, 'search_var'):
                self.search_var.set("")

            # 필터 초기화
            if hasattr(self, 'comparison_module_filter_var'):
                self.comparison_module_filter_var.set("All")
            if hasattr(self, 'comparison_part_filter_var'):
                self.comparison_part_filter_var.set("All")

            # 필터 적용
            self._apply_comparison_filters()

        except Exception as e:
            self.logger.error(f"Comparison filters reset error: {e}")

    def _update_comparison_filter_options(self):
        """전체 목록 탭 필터 옵션 업데이트

        manager.py:1866-1891에서 이관
        """
        try:
            merged_df = getattr(self.manager, 'merged_df', None)
            if merged_df is None:
                return

            # Module 옵션 업데이트
            if 'Module' in merged_df.columns:
                modules = sorted(merged_df['Module'].dropna().unique())
                module_values = ["All"] + list(modules)
                if hasattr(self, 'comparison_module_filter_combo'):
                    self.comparison_module_filter_combo['values'] = module_values
                    if not self.comparison_module_filter_var.get():
                        self.comparison_module_filter_var.set("All")

            # Part 옵션 업데이트
            if 'Part' in merged_df.columns:
                parts = sorted(merged_df['Part'].dropna().unique())
                part_values = ["All"] + list(parts)
                if hasattr(self, 'comparison_part_filter_combo'):
                    self.comparison_part_filter_combo['values'] = part_values
                    if not self.comparison_part_filter_var.get():
                        self.comparison_part_filter_var.set("All")

        except Exception as e:
            self.logger.error(f"Comparison filter options update error: {e}")

    # ==================== Search & Filter Methods ====================

    def on_search_changed(self, event=None):
        """검색어 변경 시 필터링

        manager.py:2469-2472에서 이관
        """
        search_text = self.search_var.get().lower().strip()
        self.update_comparison_view(search_filter=search_text)

    def clear_search(self):
        """검색 입력창 지우기

        manager.py:2474-2477에서 이관
        """
        self.search_var.set("")
        self.update_comparison_view(search_filter="")

    # ==================== Full List Update Methods ====================

    def update_comparison_view(self, search_filter=""):
        """비교 뷰 업데이트

        manager.py:2493-2502에서 이관
        """
        # 트리뷰 초기화
        saved_checkboxes = self._initialize_comparison_tree()

        # 데이터 처리
        diff_count, total_items, filtered_items = self._process_comparison_items(search_filter, saved_checkboxes)

        # 상태 업데이트
        self._update_comparison_status(diff_count, total_items, filtered_items, search_filter)

        # 필터 옵션 업데이트
        self._update_comparison_filter_options()

    def _initialize_comparison_tree(self):
        """비교 트리뷰 초기화 - 체크박스 상태 저장 및 반환

        manager.py:2504-2517에서 이관
        """
        if not hasattr(self, 'comparison_tree') or self.comparison_tree is None:
            return {}

        self._clear_treeview(self.comparison_tree)

        saved_checkboxes = self.item_checkboxes.copy()
        self.item_checkboxes.clear()

        maint_mode = getattr(self.manager, 'maint_mode', False)
        if maint_mode:
            self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
        else:
            self.comparison_tree.unbind("<ButtonRelease-1>")

        return saved_checkboxes

    def _process_comparison_items(self, search_filter, saved_checkboxes):
        """비교 항목 처리 및 트리에 삽입 - 통계 반환

        manager.py:2519-2601에서 이관
        """
        diff_count = 0
        total_items = 0
        filtered_items = 0

        merged_df = getattr(self.manager, 'merged_df', None)
        file_names = getattr(self.manager, 'file_names', [])
        maint_mode = getattr(self.manager, 'maint_mode', False)

        if merged_df is None:
            return diff_count, total_items, filtered_items

        # 파라미터별로 그룹화하여 비교
        grouped = merged_df.groupby(["Module", "Part", "ItemName"])

        for (module, part, item_name), group in grouped:
            total_items += 1

            # 검색 필터링 적용
            if search_filter and search_filter not in item_name.lower():
                continue

            # Module 필터링 적용
            if hasattr(self, 'comparison_module_filter_var'):
                module_filter = self.comparison_module_filter_var.get()
                if module_filter and module_filter != "All" and module != module_filter:
                    continue

            # Part 필터링 적용
            if hasattr(self, 'comparison_part_filter_var'):
                part_filter = self.comparison_part_filter_var.get()
                if part_filter and part_filter != "All" and part != part_filter:
                    continue

            filtered_items += 1

            values = []

            if maint_mode:
                checkbox_state = "☐"
                item_key = f"{module}_{part}_{item_name}"
                if item_key in saved_checkboxes and saved_checkboxes[item_key]:
                    checkbox_state = "☑"
                self.item_checkboxes[item_key] = (checkbox_state == "☑")
                values.append(checkbox_state)

            values.extend([module, part, item_name])

            # 각 파일별 값 추출 및 비교
            file_values = []
            for model in file_names:
                model_data = group[group["Model"] == model]
                if not model_data.empty:
                    value = model_data["ItemValue"].iloc[0]
                    file_values.append(str(value))
                else:
                    file_values.append("-")

            values.extend(file_values)

            # 차이점 검사 - 모든 값이 동일한지 확인
            unique_values = set(v for v in file_values if v != "-")
            has_difference = len(unique_values) > 1

            tags = []
            if has_difference:
                tags.append("different")
                diff_count += 1

            # Default DB에 존재하는지 확인
            is_existing = self._check_if_parameter_exists(module, part, item_name)
            if is_existing:
                tags.append("existing")

            self.comparison_tree.insert("", "end", values=values, tags=tuple(tags))

        # 스타일 설정
        self.comparison_tree.tag_configure("different", background="#FFECB3", foreground="#E65100")
        self.comparison_tree.tag_configure("existing", foreground="#1976D2")

        if maint_mode:
            self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)

        self.update_selected_count(None)

        return diff_count, total_items, filtered_items

    def _update_comparison_status(self, diff_count, total_items, filtered_items, search_filter):
        """비교 뷰 상태 레이블 업데이트

        manager.py:2603-2619에서 이관
        """
        maint_mode = getattr(self.manager, 'maint_mode', False)

        # 차이점 카운트 업데이트
        if not maint_mode and hasattr(self, 'diff_count_label'):
            self.diff_count_label.config(text=f"값이 다른 항목: {diff_count}개")

        # 검색 결과 표시 업데이트
        if hasattr(self, 'search_result_label'):
            if search_filter:
                self.search_result_label.config(text=f"검색 결과: {filtered_items}개 (전체: {total_items}개)")
            else:
                self.search_result_label.config(text="")

        # 필터 결과 표시 업데이트
        if hasattr(self, 'comparison_filter_result_label'):
            module_filter = getattr(self, 'comparison_module_filter_var', tk.StringVar()).get()
            part_filter = getattr(self, 'comparison_part_filter_var', tk.StringVar()).get()

            if (module_filter and module_filter != "All") or (part_filter and part_filter != "All"):
                self.comparison_filter_result_label.config(text=f"필터링됨: {filtered_items}개 (전체: {total_items}개)")
            else:
                self.comparison_filter_result_label.config(text="")

    def _check_if_parameter_exists(self, module, part, item_name):
        """Default DB에 파라미터 존재 여부 확인

        manager.py:2697-2710에서 이관
        """
        try:
            db_schema = getattr(self.manager, 'db_schema', None)
            if not db_schema:
                return False

            equipment_types = db_schema.get_equipment_types()
            for type_id, type_name, _ in equipment_types:
                if type_name.lower() == module.lower():
                    default_values = db_schema.get_default_values(type_id)
                    for _, param_name, _, _, _, _ in default_values:
                        # ItemName만으로 체크
                        if param_name == item_name:
                            return True
            return False
        except Exception as e:
            self.logger.error(f"DB ItemName 존재 여부 확인 중 오류: {e}")
            return False

    # ==================== Checkbox Methods ====================

    def toggle_checkbox(self, event):
        """체크박스 토글

        manager.py:2655-2678에서 이관
        """
        maint_mode = getattr(self.manager, 'maint_mode', False)
        if not maint_mode:
            return

        region = self.comparison_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.comparison_tree.identify_column(event.x)
        if column != "#1":
            return

        item = self.comparison_tree.identify_row(event.y)
        if not item:
            return

        values = self.comparison_tree.item(item, "values")
        if not values or len(values) < 4:
            return

        current_state = values[0]
        module, part, item_name = values[1], values[2], values[3]
        item_key = f"{module}_{part}_{item_name}"
        new_state = "☑" if current_state == "☐" else "☐"
        self.item_checkboxes[item_key] = (new_state == "☑")
        new_values = list(values)
        new_values[0] = new_state
        self.comparison_tree.item(item, values=new_values)
        self.update_checked_count()

    def toggle_select_all_checkboxes(self):
        """전체 선택 체크박스 토글

        manager.py:2479-2492에서 이관
        """
        maint_mode = getattr(self.manager, 'maint_mode', False)
        if not maint_mode:
            return

        check = self.select_all_var.get()
        for item in self.comparison_tree.get_children():
            values = list(self.comparison_tree.item(item, "values"))
            if len(values) > 0:
                values[0] = "☑" if check else "☐"
                self.comparison_tree.item(item, values=values)
                module, part, item_name = values[1], values[2], values[3]
                item_key = f"{module}_{part}_{item_name}"
                self.item_checkboxes[item_key] = check

        self.update_checked_count()

    def update_selected_count(self, event):
        """선택된 항목 카운트 업데이트

        manager.py:2680-2689에서 이관
        """
        maint_mode = getattr(self.manager, 'maint_mode', False)
        if not maint_mode:
            return

        if not hasattr(self, 'selected_count_label'):
            return

        checked_count = sum(1 for checked in self.item_checkboxes.values() if checked)
        if checked_count > 0:
            self.selected_count_label.config(text=f"체크된 항목: {checked_count}개")
        else:
            selected_items = self.comparison_tree.selection()
            count = len(selected_items)
            self.selected_count_label.config(text=f"선택된 항목: {count}개")

    def update_checked_count(self):
        """체크된 항목 카운트 업데이트

        manager.py:2691-2695에서 이관
        """
        maint_mode = getattr(self.manager, 'maint_mode', False)
        if not maint_mode:
            return

        if not hasattr(self, 'selected_count_label'):
            return

        checked_count = sum(1 for checked in self.item_checkboxes.values() if checked)
        self.selected_count_label.config(text=f"체크된 항목: {checked_count}개")

    # ==================== Default DB Methods ====================

    def add_to_default_db(self):
        """체크된 항목들을 Default DB로 전송 - 중복도 기반 통계 분석

        manager.py:2022-2232에서 이관

        복잡한 비즈니스 로직(통계 분석, DB 저장)은 manager에 위임하고,
        UI 구성만 담당합니다.
        """
        # 관리자 모드 확인
        maint_mode = getattr(self.manager, 'maint_mode', False)
        if not maint_mode:
            messagebox.showwarning("권한 없음", "Default DB 항목 추가는 관리자 모드에서만 가능합니다.")
            return

        # manager에 구현된 메서드 위임
        # manager.py의 add_to_default_db()가 모든 로직 처리:
        # - 선택된 항목 수집 (_collect_selected_comparison_items)
        # - 장비 유형 선택 다이얼로그
        # - 통계 분석 설정 다이얼로그
        # - 미리보기 및 중복 검사
        # - DB 저장 및 로깅
        # - UI 갱신
        if hasattr(self.manager, 'add_to_default_db'):
            self.manager.add_to_default_db()
        else:
            messagebox.showerror("오류", "add_to_default_db 메서드를 찾을 수 없습니다.")
            self.logger.error("manager.add_to_default_db method not found")

    # ==================== Context Menu ====================

    def create_comparison_context_menu(self):
        """비교 뷰 우클릭 메뉴 생성

        manager.py:2631-2635에서 이관
        """
        self.comparison_context_menu = tk.Menu(self.manager.window, tearoff=0)
        self.comparison_context_menu.add_command(
            label="선택한 항목을 Default DB에 추가",
            command=self.add_to_default_db
        )

        # 우클릭 이벤트 바인딩
        if self.comparison_tree:
            self.comparison_tree.bind("<Button-3>", self.show_comparison_context_menu)

        # 초기 상태 업데이트
        self.update_comparison_context_menu_state()

        self.logger.debug("Comparison context menu created")

    def show_comparison_context_menu(self, event):
        """비교 뷰 우클릭 메뉴 표시

        manager.py:2637-2645에서 이관

        Args:
            event: 마우스 이벤트
        """
        # 관리자 모드 확인
        maint_mode = getattr(self.manager, 'maint_mode', False)
        if not maint_mode:
            return

        # 선택된 항목 확인
        if not self.comparison_tree.selection():
            return

        # 메뉴 표시
        try:
            self.comparison_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.comparison_context_menu.grab_release()

    def update_comparison_context_menu_state(self):
        """비교 뷰 컨텍스트 메뉴 상태 업데이트

        manager.py:2647-2653에서 이관

        관리자 모드에 따라 메뉴 항목 활성화/비활성화
        """
        if not hasattr(self, 'comparison_context_menu'):
            return

        maint_mode = getattr(self.manager, 'maint_mode', False)
        state = "normal" if maint_mode else "disabled"

        try:
            self.comparison_context_menu.entryconfig(
                "선택한 항목을 Default DB에 추가",
                state=state
            )
        except Exception as e:
            self.logger.warning(f"컨텍스트 메뉴 상태 업데이트 중 오류: {e}")

    # ==================== Update Methods ====================

    def update_all_views(self):
        """
        모든 비교 뷰 업데이트

        데이터 변경 시 호출 (파일 로드, 필터 변경 등)
        """
        self.update_grid_view()
        self.update_diff_only_view()
        self.update_comparison_view()
        self.logger.debug("All comparison views updated")

    # ==================== Public Interface ====================

    def get_selected_items(self) -> List[str]:
        """
        선택된 항목 ID 목록 반환 (관리자 모드)

        Returns:
            List[str]: 선택된 Tree item ID 리스트
        """
        if self.comparison_tree:
            return self.comparison_tree.selection()
        return []

    def refresh(self):
        """탭 새로고침 (데이터 재로드)"""
        self.update_all_views()


# ==================== Migration Notes ====================
"""
마이그레이션 상태: ✅ Day 3-4 완료 (100% 진행) - manager.py 통합 대기

완료:
- ✅ 기본 클래스 구조 및 초기화 (Day 1)
- ✅ 3개 서브 탭 스켈레톤 생성 (Day 1)
- ✅ Grid View Tab 완전 구현 (Day 2) - ~250 lines
  - update_grid_view()
  - _configure_grid_view_tags()
  - _build_grid_hierarchy_data()
  - _populate_grid_tree()
  - _clear_treeview() (helper)
- ✅ Diff Only Tab 완전 구현 (Day 2) - ~90 lines
  - update_diff_only_view()
- ✅ Full List Tab 완전 구현 (Day 3-4) - ~470 lines
  - create_full_list_tab() - 전체 UI 구조 (검색, 필터, 트리뷰)
  - _create_comparison_filter_panel() - 필터 패널
  - _create_comparison_advanced_filters() - Module/Part 필터
  - _toggle_comparison_advanced_filters() - 필터 토글
  - _apply_comparison_filters() - 필터 적용
  - _reset_comparison_filters() - 필터 초기화
  - _update_comparison_filter_options() - 필터 옵션 업데이트
  - update_comparison_view() - 메인 업데이트
  - _initialize_comparison_tree() - 트리 초기화
  - _process_comparison_items() - 항목 처리 및 통계
  - _update_comparison_status() - 상태 라벨 업데이트
  - _check_if_parameter_exists() - 파라미터 존재 확인
  - toggle_checkbox() - 체크박스 토글
  - toggle_select_all_checkboxes() - 전체 선택
  - update_selected_count() - 선택 카운트 업데이트
  - update_checked_count() - 체크 카운트 업데이트
  - on_search_changed() - 검색 이벤트
  - clear_search() - 검색 초기화
- ✅ Default DB 메서드 (Day 4)
  - add_to_default_db() - manager에 위임
- ✅ Context 메뉴 (Day 4)
  - create_comparison_context_menu()
  - show_comparison_context_menu()
  - update_comparison_context_menu_state()

총 코드량: ~1,210 lines (목표 ~810 lines 초과 달성, 150%)
- Day 1: 200 lines (스켈레톤)
- Day 2: +380 lines (Grid View + Diff Only)
- Day 3-4: +470 lines (Full List Tab + Context Menu)
- Day 4: +160 lines (add_to_default_db + helper methods)

다음 단계 (Day 5):
1. manager.py에서 ComparisonTab 사용으로 전환
   - create_comparison_tabs() 메서드 수정
   - self.comparison_tab = ComparisonTab(self, self.comparison_notebook) 인스턴스 생성
   - 기존 비교 관련 메서드를 ComparisonTab으로 리다이렉트
2. 기존 코드 제거 또는 주석 처리
   - manager.py:1380-2680 (약 1300 lines) 제거 대상
3. 테스트 및 검증
   - 파일 비교 기능
   - 필터/검색 기능
   - Default DB 전송 기능
   - Context 메뉴 동작
4. 문서 업데이트
   - UI_MIGRATION_PLAN.md 업데이트
   - SESSION_SUMMARY 업데이트
   - 커밋 메시지 작성

설계 결정:
- add_to_default_db()는 manager.py에 위임:
  복잡한 통계 분석 로직(analyze_parameter_statistics, add_parameters_with_statistics)은
  비즈니스 로직이므로 manager에 남겨두고, UI는 단순히 호출만 수행
- Context 메뉴는 ComparisonTab에서 관리:
  UI 관련 요소이므로 ComparisonTab에서 직접 생성 및 관리
"""
