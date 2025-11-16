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

        Features:
        - 검색 기능 (ItemName 기반)
        - 고급 필터 (Module, Part)
        - Context 메뉴 (Default DB 전송, 복사 등)
        - 선택 기능 (관리자 모드)

        TODO: manager.py:1632-2100 코드 이관 필요 (약 470 lines)
        - _create_comparison_filter_panel()
        - _create_comparison_advanced_filters()
        - _toggle_comparison_advanced_filters()
        - _apply_comparison_filters()
        - _reset_comparison_filters()
        - _update_comparison_filter_options()
        - create_comparison_context_menu()
        - show_comparison_context_menu()
        - update_comparison_context_menu_state()
        """
        comparison_frame = ttk.Frame(self.notebook)
        self.notebook.add(comparison_frame, text="📋 전체 목록")

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

        # TODO: 필터 컨트롤 추가
        # TODO: 트리뷰 추가
        # TODO: Context 메뉴 추가

        self.logger.info("Full List Tab created (skeleton)")

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

    # ==================== Search & Filter Methods ====================

    def on_search_changed(self, event=None):
        """
        검색어 변경 시 호출

        TODO: manager.py:2469 코드 이관 (Full List Tab에서 구현 예정)
        """
        search_text = self.search_var.get()
        # TODO: Implement search logic
        self.logger.debug(f"Search changed: {search_text}")

    def clear_search(self):
        """
        검색 초기화

        TODO: manager.py:2474 코드 이관 (Full List Tab에서 구현 예정)
        """
        self.search_var.set("")
        # TODO: Reset search filter
        self.logger.debug("Search cleared")

    # ==================== Update Methods ====================

    def update_all_views(self):
        """
        모든 비교 뷰 업데이트

        데이터 변경 시 호출 (파일 로드, 필터 변경 등)
        """
        self.update_grid_view()
        self.update_diff_only_view()
        # TODO: update_comparison_view() (Full List Tab, Day 3-4 구현 예정)
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
마이그레이션 상태: 🚧 진행중 - Day 2 완료 (70% 진행)

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

진행 예정 (manager.py에서 이관):
- ⏳ Full List Tab 완전 구현 (Day 3-4) - ~470 lines
  - 전체 트리뷰 구성
  - 필터 패널 완전 구현
  - Context 메뉴
  - 검색 로직
  - add_to_default_db() 통합
  - update_comparison_view()

총 코드량: ~580 lines (목표 ~810 lines의 70%)
- Day 1: 200 lines (스켈레톤)
- Day 2: +380 lines (Grid View + Diff Only)

다음 단계 (Day 3-4):
1. Full List Tab 트리뷰 완전 구성
2. 필터 패널 및 검색 로직 구현
3. Context 메뉴 통합
4. add_to_default_db() 통합
5. update_comparison_view() 구현

다음 단계 (Day 5):
1. manager.py에서 ComparisonTab 사용으로 전환
2. 기존 코드 제거
3. 테스트 및 검증
"""
