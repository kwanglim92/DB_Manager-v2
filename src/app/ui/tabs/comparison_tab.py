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

    # ==================== Search & Filter Methods ====================

    def on_search_changed(self, event=None):
        """
        검색어 변경 시 호출

        TODO: manager.py:2469 코드 이관
        """
        search_text = self.search_var.get()
        # TODO: Implement search logic
        self.logger.debug(f"Search changed: {search_text}")

    def clear_search(self):
        """
        검색 초기화

        TODO: manager.py:2474 코드 이관
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
        # TODO: Call individual update methods
        self.logger.debug("Updating all comparison views")

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
마이그레이션 상태: 🚧 진행중

완료:
- ✅ 기본 클래스 구조 및 초기화
- ✅ 3개 서브 탭 스켈레톤 생성

진행 예정 (manager.py에서 이관):
- ⏳ Grid View Tab 완전 구현 (~250 lines)
  - update_grid_view()
  - _configure_grid_view_tags()
  - _build_grid_hierarchy_data()
  - _populate_grid_tree()

- ⏳ Full List Tab 완전 구현 (~470 lines)
  - 전체 트리뷰 구성
  - 필터 패널 완전 구현
  - Context 메뉴
  - 검색 로직
  - add_to_default_db() 통합

- ⏳ Diff Only Tab 완전 구현 (~90 lines)
  - update_diff_only_view()

총 예상 코드량: ~810 lines (현재 ~200 lines, 75% 남음)

다음 단계:
1. Grid View Tab 업데이트 로직 이관
2. Full List Tab 필터/검색 완전 구현
3. Context 메뉴 통합
4. manager.py에서 비교 관련 코드 제거 및 ComparisonTab 호출로 대체
5. 테스트 및 검증
"""
