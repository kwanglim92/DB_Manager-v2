# UI/로직 분리 마이그레이션 계획

**작성일**: 2025-11-16
**Phase**: 중기 계획 Week 1-2 (UI 컴포넌트 추출)
**상태**: 🚧 진행중 - Day 1 완료

---

## 목표

manager.py (5,593 lines)를 UI/비즈니스 로직으로 분리하여 유지보수성 향상

**목표 구조**:
```
src/app/
├── ui/                    # UI 계층 (NEW)
│   ├── tabs/              # 탭별 UI
│   │   ├── comparison_tab.py      ✅ 스켈레톤 완료
│   │   ├── default_db_tab.py      ⏳ 예정
│   │   └── qc_tab.py              ⏳ 예정
│   └── widgets/           # 재사용 위젯 (향후)
│
├── business/              # 비즈니스 로직 (Week 3-4)
│   ├── comparison_logic.py
│   ├── default_db_logic.py
│   └── qc_logic.py
│
├── events/                # 이벤트 시스템 (Week 5-6)
│   ├── event_bus.py
│   └── handlers/
│
└── manager.py             # 메인 컨트롤러 (간소화)
```

---

## Day 1 진행 상황 (2025-11-16 오전)

### ✅ 완료된 작업

1. **디렉토리 구조 생성**
   - `src/app/ui/` 디렉토리
   - `src/app/ui/tabs/` 디렉토리
   - `__init__.py` 파일들

2. **ComparisonTab 스켈레톤 구현** (~200 lines)
   - 기본 클래스 구조
   - 3개 서브 탭 생성 메서드:
     - Grid View Tab (메인 비교)
     - Full List Tab (전체 목록)
     - Diff Only Tab (차이점 분석)
   - 검색/필터 메서드 스켈레톤
   - 상세한 TODO 주석 및 마이그레이션 노트

3. **코드 분석 완료**
   - manager.py에서 비교 관련 메서드 21개 식별
   - 예상 코드량: ~810 lines
   - 마이그레이션 우선순위 결정

---

## Day 2 진행 상황 (2025-11-16 오후)

### ✅ 완료된 작업

1. **Grid View Tab 완전 구현** (~250 lines)
   - `update_grid_view()` - 메인 업데이트 로직
   - `_configure_grid_view_tags()` - 계층별 스타일 설정
   - `_build_grid_hierarchy_data()` - 데이터 구조화 (Module → Part → ItemName)
   - `_populate_grid_tree()` - 트리뷰 렌더링 및 통계 업데이트
   - `_clear_treeview()` - 헬퍼 메서드

2. **Diff Only Tab 완전 구현** (~90 lines)
   - `update_diff_only_view()` - 차이점 필터링 및 표시

3. **update_all_views() 통합**
   - Grid View, Diff Only 자동 업데이트
   - Full List Tab 연동 준비 (Day 3-4)

**총 코드 추가**: ~380 lines (Day 2)
**누적 코드**: ~580 lines (Day 1: 200 + Day 2: 380)

---

## ComparisonTab 마이그레이션 상세

### 현재 상태: 70% 완료 (580/810 lines)

#### ✅ 완료 (70%)
- Day 1: 기본 구조 및 초기화 (200 lines)
- Day 2: Grid View Tab 완전 구현 (250 lines)
- Day 2: Diff Only Tab 완전 구현 (90 lines)
- Helper 메서드 (_clear_treeview)
- update_all_views() 통합

#### ⏳ 진행 예정 (30%)

**Full List Tab 완전 구현** (~230 lines, 30%)
```python
# manager.py 이관 대상:
- 트리뷰 완전 구성 (line 1714-1741)
- _create_comparison_filter_panel() (line 1743)
- _create_comparison_advanced_filters() (line 1768)
- _toggle_comparison_advanced_filters() (line 1807)
- _apply_comparison_filters() (line 1838)
- _reset_comparison_filters() (line 1847)
- _update_comparison_filter_options() (line 1866)
- _collect_selected_comparison_items() (line 1894)
- update_comparison_view() (line 2493)
- _initialize_comparison_tree() (line 2504)
- _process_comparison_items() (line 2519)
- _update_comparison_status() (line 2603)
- create_comparison_context_menu() (line 2631)
- show_comparison_context_menu() (line 2637)
- update_comparison_context_menu_state() (line 2647)
- add_to_default_db() (line 2022)
- on_search_changed() (line 2469)
- clear_search() (line 2474)
- toggle_select_all_checkboxes() (line 2479)
- update_selected_count() (line 2680)
```

**3. Diff Only Tab 완전 구현** (~90 lines, 11%)
```python
# manager.py 이관 대상:
- update_diff_only_view() (line 1169)
```

---

## 마이그레이션 전략

### 점진적 마이그레이션 (Incremental Migration)

**Phase 1: 스켈레톤 생성** ✅ 완료
- 새 클래스 구조 생성
- 기본 UI 위젯 초기화
- 인터페이스 정의

**Phase 2: 메서드 이관** ⏳ 다음 단계
- manager.py에서 메서드 복사
- ComparisonTab으로 이동
- `self.manager` 참조를 통한 데이터 접근

**Phase 3: 통합 및 테스트** ⏳ 예정
- manager.py에서 ComparisonTab 사용
- 기존 코드 제거
- 기능 검증

**Phase 4: 리팩토링** ⏳ 예정
- UI/비즈니스 로직 완전 분리
- 이벤트 기반 통신
- 단위 테스트 추가

---

## 다음 단계 (Day 2)

### 우선순위 1: Grid View Tab 완전 구현
1. `update_grid_view()` 메서드 이관
2. `_configure_grid_view_tags()` 이관
3. `_build_grid_hierarchy_data()` 이관
4. `_populate_grid_tree()` 이관
5. 데이터 접근 방식 정리 (`self.manager.merged_df`)

### 우선순위 2: Diff Only Tab 완전 구현
1. `update_diff_only_view()` 이관 (상대적으로 간단)
2. 테스트

### 우선순위 3: Full List Tab 필터 시스템
1. 필터 패널 완전 구현
2. 검색 로직 구현
3. 트리뷰 업데이트 로직

---

## 통합 계획

### manager.py 변경사항
```python
# 기존 (manager.py:109):
self.create_comparison_tabs()

# 변경 후:
from app.ui.tabs import ComparisonTab
self.comparison_tab = ComparisonTab(self, self.comparison_notebook)
```

### 호환성 유지
- 기존 `self.comparison_tree`, `self.grid_tree` 등의 속성 유지
- manager.py의 다른 메서드에서 접근 가능하도록 프록시 설정
- 점진적 전환으로 리스크 최소화

---

## 예상 일정

| Day | 작업 | 예상 코드량 | 상태 |
|-----|------|-------------|------|
| **Day 1** | ComparisonTab 스켈레톤 | 200 lines | ✅ 완료 (2025-11-16 오전) |
| **Day 2** | Grid View + Diff Only Tab | 380 lines | ✅ 완료 (2025-11-16 오후) |
| **Day 3-4** | Full List Tab 완전 구현 | 230 lines | ⏳ 예정 |
| **Day 5** | manager.py 통합 및 테스트 | - | ⏳ 예정 |

**총 예상 소요**: 5일 (Week 1)
**현재 진행**: Day 2 완료 (40% → 70%)

---

## 리스크 관리

### 식별된 리스크

| 리스크 | 영향 | 확률 | 완화 전략 |
|--------|------|------|-----------|
| 데이터 접근 방식 변경 | 높음 | 중 | `self.manager` 프록시 사용, 점진적 전환 |
| 기존 기능 손상 | 높음 | 중 | 메서드별 테스트, 회귀 테스트 |
| 복잡한 상태 관리 | 중 | 높음 | 명확한 인터페이스 정의, 문서화 |

### 롤백 계획
- Git 커밋: 메서드 단위로 커밋
- 테스트 실패 시 즉시 롤백
- manager.py 원본 유지 (주석 처리)

---

## 테스트 계획

### 수동 테스트 (각 단계마다)
1. **Grid View Tab**
   - 파일 로드 후 계층 구조 표시 확인
   - Module/Part/ItemName 계층 확인
   - 차이점 하이라이트 확인
   - 통계 정보 정확성 확인

2. **Full List Tab**
   - 검색 기능 동작 확인
   - 필터 적용 확인 (Module, Part)
   - Context 메뉴 확인
   - Default DB 전송 확인 (관리자 모드)

3. **Diff Only Tab**
   - 차이점만 표시되는지 확인
   - 개수 정확성 확인

### 자동 테스트 (향후)
- pytest-qt를 사용한 UI 테스트
- 통합 테스트 추가

---

## 성공 기준

### Week 1-2 목표
- ✅ ComparisonTab 스켈레톤 생성 (Day 1)
- ✅ Grid View Tab 완전 구현 (Day 2)
- ✅ Diff Only Tab 완전 구현 (Day 2)
- ⏳ Full List Tab 완전 구현 (Day 3-4, 30% 남음)
- ⏳ manager.py 통합 및 기존 코드 제거 (Day 5)
- ⏳ 모든 기능 정상 작동 (회귀 없음) (Day 5)

### 품질 지표
- 코드 라인 수: manager.py 5,593 → ~4,800 lines (-14%) 목표
- **ComparisonTab 완성도: 70%** (580/810 lines) ✅ **Day 2 완료**
- 테스트 통과율: 100% (예정, Day 5)
- 수동 테스트: 모든 시나리오 통과 (예정, Day 5)

---

## 참조 문서
- FUTURE_ROADMAP.md - 중기 계획 전체 개요
- manager.py - 원본 코드 (line 965-2680)
- CLAUDE.md - 프로젝트 전체 가이드

---

**최종 업데이트**: 2025-11-16 Day 2 완료 (70% 진행)
**다음 리뷰**: 2025-11-17 (Day 3-4 Full List Tab 구현)
**담당자**: Claude Code

---

## Day 2 완료 요약

**완료 항목**:
- ✅ Grid View Tab 완전 구현 (5개 메서드, ~250 lines)
- ✅ Diff Only Tab 완전 구현 (1개 메서드, ~90 lines)
- ✅ Helper 메서드 (_clear_treeview)
- ✅ update_all_views() 통합
- ✅ 문서 업데이트 (UI_MIGRATION_PLAN.md)

**코드 통계**:
- Day 1: 200 lines (스켈레톤)
- Day 2: +380 lines (Grid View + Diff Only)
- **총**: 580 lines (목표 810 lines의 70%)

**다음 단계**:
- Day 3-4: Full List Tab 구현 (~230 lines, 30% 남음)
- Day 5: manager.py 통합 및 테스트
