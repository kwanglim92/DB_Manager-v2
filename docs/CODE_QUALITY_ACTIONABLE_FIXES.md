# 코드 품질 개선 - 실행 가능한 수정 사항

## 빠른 참고 (Quick Reference)

### 🔴 P0 - 긴급 수정 (1-2일)

```
1. Bare except 절 제거 (20+ 곳)
2. print() → logging 변경 (15+ 곳)
3. db_schema.py / schema.py 동기화
4. 전역 변수 → Singleton 패턴
5. 파일 인코딩 명시
```

---

## 1. Bare Except 절 수정

### 발견된 모든 위치

```
manager.py:      2547, 2557, 3236, 4697, 4699, 4706, 4713, 4727, 4740, 4742 (10곳)
enhanced_qc.py:  104, 143 (2곳)
file_service.py: 156 (1곳)
comparison_filters.py: 175, 306 (2곳)
checklist_manager_dialog.py: 280 (1곳)
shipped_equipment_service.py: 594 (1곳)
services/__init__.py: 87, 95, 104 (3곳)
```

### 수정 패턴

**Before:**
```python
try:
    result = some_operation()
except:
    pass  # ❌ 위험!
```

**After:**
```python
try:
    result = some_operation()
except Exception as e:
    logger.error(f"작업 실패: {e}", exc_info=True)
    return None  # 또는 적절한 에러 처리
```

### 우선순위별 수정 순서

1. **manager.py** (영향도 최고)
   ```python
   # manager.py:2547 - enable_maint_features
   try:
       self.enable_maint_features()
   except:
       pass
   # ↓ 변경
   try:
       self.enable_maint_features()
   except Exception as e:
       self.update_log(f"관리자 기능 활성화 실패: {e}")
       logger.error(f"enable_maint_features error: {e}", exc_info=True)
   ```

2. **file_service.py** (데이터 손실 위험)
   ```python
   # file_service.py:156
   except:
       return None
   # ↓ 변경
   except Exception as e:
       logger.error(f"파일 처리 오류: {e}", exc_info=True)
       return None
   ```

3. **services/** (서비스 레이어)
   ```python
   # services/__init__.py:87
   except:
       pass
   # ↓ 변경
   except ImportError as e:
       logger.warning(f"서비스 import 실패: {e}")
       pass
   ```

---

## 2. print() → Logging 변경

### 통합 해결책

**Step 1:** 모든 파일에서 logging import 추가
```python
import logging
logger = logging.getLogger(__name__)

# 또는 서비스 로깅 사용
from app.services.common.logging_service import LoggingService
_logger = LoggingService().get_logger(__name__)
```

**Step 2:** print() 변경
```python
# ❌ Before
print(f"Check list 로드 실패: {e}")

# ✅ After
logger.error(f"Check list 로드 실패: {e}", exc_info=True)
```

### 파일별 수정 사항

#### A. checklist_validator.py (3곳)

```python
# Line 31
# ❌ print(f"Check list 로드 실패: {e}")
# ✅
self.logger.error(f"Check list 로드 실패: {e}", exc_info=True)

# Line 58
# ❌ print("경고: ItemName 컬럼이 없습니다.")
# ✅
self.logger.warning("경고: ItemName 컬럼이 없습니다.")

# Line 270
# ❌ print(f"Check list 검증 통합 중 오류: {e}")
# ✅
self.logger.error(f"Check list 검증 통합 중 오류: {e}", exc_info=True)
```

#### B. manager.py (10+ 곳 DEBUG 로그)

```python
# Line 842
# ❌ print(f"DEBUG - enable_maint_features error: {e}")
# ✅
self.logger.debug(f"enable_maint_features error: {e}")
# 또는
self.update_log(f"관리자 기능 활성화 실패: {str(e)}")

# Line 2573
# ❌ print(f"DEBUG - disable_maint_features error: {e}")
# ✅
self.logger.debug(f"disable_maint_features error: {e}")

# Lines 4282-4333 (export_to_text_file)
# 여러 DEBUG print 로그들
# ✅ 모두 logger.debug()로 변경
```

#### C. services/__init__.py (1곳)

```python
# Line 41
# ❌ print(f"서비스 import 실패: {e}")
# ✅
logger.warning(f"서비스 import 실패: {e}")
```

---

## 3. 이중 DBSchema 파일 해결

### 현재 상황

```
src/db_schema.py          src/app/schema.py
─────────────────        ──────────────────
729 lines                 (간단한 버전)
✓ Equipment_Models        ✗ Equipment_Models 없음
✓ Equipment_Types         ✓ Equipment_Types
✓ Equipment_Configurations ✗ Equipment_Configurations 없음
✓ 9개 테이블              ✓ 6개 테이블 (Phase 0 기본)
```

### 해결 방안

**Option 1: db_schema.py 사용 (권장)**
```python
# manager.py:7
# ❌ from app.schema import DBSchema
# ✅
from db_schema import DBSchema  # src 디렉토리에서
```

**Option 2: schema.py 업데이트**
```python
# src/app/schema.py에 Phase 1.5 테이블 추가
# Equipment_Models, Equipment_Types (model_id FK), Equipment_Configurations

# db_schema.py의 create_tables() 메서드 복사
# 그 후 app/schema.py 사용 유지
```

### 실행 단계

1. **두 파일 내용 비교**
   ```bash
   diff src/db_schema.py src/app/schema.py
   ```

2. **누락된 부분 확인**
   - Equipment_Models 테이블
   - Equipment_Configurations 테이블
   - 기타 Phase 1.5 테이블들

3. **src/app/schema.py 업데이트**
   ```python
   # src/app/schema.py에 add
   
   # Phase 1.5: Equipment_Models
   cursor.execute('''
   CREATE TABLE IF NOT EXISTS Equipment_Models (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       model_name TEXT NOT NULL UNIQUE,
       description TEXT,
       display_order INTEGER DEFAULT 999,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   ''')
   ```

4. **테스트**
   ```python
   # db_schema.py 삭제 후 app/schema.py로만 작동 확인
   python src/main.py
   ```

---

## 4. 전역 변수 → Singleton 패턴

### 문제 코드 (services/__init__.py:113)

```python
# ❌ Before: 전역 변수
global _legacy_adapter

_legacy_adapter = None

def get_legacy_adapter():
    global _legacy_adapter
    if _legacy_adapter is None:
        _legacy_adapter = LegacyAdapter(...)
    return _legacy_adapter
```

### 해결책

**Option 1: Singleton 클래스**
```python
# ✅ services/legacy_adapter_singleton.py (새 파일)

class LegacyAdapterSingleton:
    _instance: Optional['LegacyAdapter'] = None
    
    def __new__(cls) -> 'LegacyAdapter':
        if cls._instance is None:
            from .service_factory import ServiceFactory
            # ServiceFactory 얻기
            cls._instance = LegacyAdapter(service_factory)
        return cls._instance
    
    @classmethod
    def reset(cls):
        """테스트용 리셋"""
        cls._instance = None
```

**Option 2: ServiceRegistry 활용 (현재 패턴)**
```python
# ✅ 기존 ServiceRegistry 활용
from .common.service_registry import ServiceRegistry

class LegacyAdapterService:
    def __init__(self, service_factory):
        self._factory = service_factory
    
    # ... 구현

# services/__init__.py
def setup_legacy_adapter(service_factory):
    adapter = LegacyAdapterService(service_factory)
    # ServiceRegistry에 등록
    return adapter
```

---

## 5. 파일 인코딩 명시

### 발견된 위치

```python
# manager.py:174
with open(config_path, 'r') as f:  # ❌ UTF-8 명시 필요
```

### 수정

```python
# ✅ 모든 파일 작업
with open(config_path, 'r', encoding='utf-8') as f:
    settings = json.load(f)

# 쓰기도 마찬가지
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 프로젝트 전체 검색 및 수정

```bash
# 모든 open() 호출 확인
grep -rn "open(" src/app --include="*.py" | grep -v "encoding="

# 수정 템플릿
# ❌ open(file, 'r')
# ✅ open(file, 'r', encoding='utf-8')
```

---

## 6. 로깅 일관성

### 필수: LoggingService 통합

**모든 서비스 클래스:**
```python
from .common.logging_service import LoggingService

class MyService:
    def __init__(self):
        self._logger = LoggingService().get_logger(__name__)
    
    def do_something(self):
        try:
            # 작업
            self._logger.info("작업 완료")
        except Exception as e:
            self._logger.error(f"오류: {e}", exc_info=True)
```

**manager.py (UI 클래스):**
```python
class DBManager:
    def __init__(self):
        # 기존: update_log() 메서드 사용
        # 추가: logger도 함께 사용
        self.logger = LoggingService().get_logger('DBManager')
    
    def some_operation(self):
        try:
            # 작업
            self.update_log("UI에서 표시할 메시지")
            self.logger.info("로그에도 기록")
        except Exception as e:
            self.update_log(f"오류: {e}")
            self.logger.error(f"상세 오류 정보: {e}", exc_info=True)
```

---

## 7. 상수 정의 완성

### 현재 constants.py 확장

**추가할 상수:**
```python
# constants.py

# Window 설정
WINDOW_TITLE = "DB Manager"
WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 800
ICON_PATH = "resources/icons/db_compare.ico"

# 상태 메시지
STATUS_READY = "Ready"
STATUS_LOADING = "Loading..."
STATUS_ERROR = "Error"

# 신뢰도 임계값
DEFAULT_CONFIDENCE_THRESHOLD = 0.5

# Check list 심각도
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"
SEVERITY_LEVELS = (SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW)

# 캐시 설정
CACHE_MAX_SIZE = 1000
CACHE_DEFAULT_TTL = 300  # 5분

# 데이터베이스
DB_PATH = "data/local_db.sqlite"
```

**manager.py에서 사용:**
```python
# ❌ Before
self.window.title("DB Manager")
self.window.geometry("1300x800")

# ✅ After
from app.constants import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, STATUS_READY
)

self.window.title(WINDOW_TITLE)
self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
self.status_bar.config(text=STATUS_READY)
```

---

## 8. 메서드 분할 (Refactoring)

### manager.py 주요 분할 대상

**Problem:** create_comparison_tabs() - 300+ lines

**Solution:**
```python
# ❌ Before (300+ lines 한 메서드)
def create_comparison_tabs(self):
    # ... 300+ lines

# ✅ After (분할)
def create_comparison_tabs(self):
    self._create_file_selection_tab()
    self._create_comparison_options_tab()
    self._create_results_tab()
    self._create_statistics_tab()

def _create_file_selection_tab(self):
    # 50 lines
    pass

def _create_comparison_options_tab(self):
    # 50 lines
    pass

def _create_results_tab(self):
    # 100 lines
    pass

def _create_statistics_tab(self):
    # 50 lines
    pass
```

### 우선순위 (영향도 큰 것부터)

1. create_comparison_tabs() - 300+ lines
2. load_folder() - 150+ lines
3. add_default_value_dialog() - 200+ lines
4. perform_qc_check() - 100+ lines

---

## 9. 테스트 추가

### Phase 1.5 테이블 테스트

```python
# tools/test_phase1_5_tables.py (새 파일)

import unittest
from app.schema import DBSchema

class TestPhase15Tables(unittest.TestCase):
    def setUp(self):
        self.db = DBSchema(":memory:")
    
    def test_equipment_models_table_exists(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(Equipment_Models)")
            columns = cursor.fetchall()
            self.assertGreater(len(columns), 0)
    
    def test_equipment_configurations_table_exists(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(Equipment_Configurations)")
            columns = cursor.fetchall()
            self.assertGreater(len(columns), 0)
    
    # ... 추가 테스트
```

---

## 10. 실행 체크리스트

### Week 1 - 긴급 수정

- [ ] Bare except 절 → Exception으로 변경 (모든 20+ 곳)
- [ ] print() → logging 변경 (모든 15+ 곳)
- [ ] 파일 인코딩 명시 (모든 open() 호출)
- [ ] db_schema.py와 schema.py 동기화 완료
- [ ] 테스트 실행: `python src/main.py` 정상 종료 확인

### Week 2 - 구조 개선

- [ ] 전역 변수 → Singleton 패턴 변경
- [ ] 상수 정의 완성
- [ ] LoggingService 일관되게 사용
- [ ] Phase 1.5 테이블 테스트 추가

### Week 3 - 리팩토링

- [ ] manager.py 주요 메서드 분할
- [ ] 중복 코드 추출 (validation, UI patterns)
- [ ] 서비스 레이어 활용 확대

---

## 부록: 자동 검증 스크립트

```python
# tools/code_quality_check.py (새 파일)

import re
import os

def check_bare_except():
    """Bare except 절 찾기"""
    issues = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    for i, line in enumerate(f, 1):
                        if re.match(r'^\s*except\s*:\s*$', line):
                            issues.append((path, i, line.strip()))
    return issues

def check_print_statements():
    """print() 문 찾기 (테스트 제외)"""
    issues = []
    for root, dirs, files in os.walk("src/app"):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    for i, line in enumerate(f, 1):
                        if re.search(r'print\s*\(', line) and 'test_' not in path:
                            issues.append((path, i, line.strip()))
    return issues

if __name__ == "__main__":
    print("=== Bare Except Clauses ===")
    for path, line, code in check_bare_except():
        print(f"{path}:{line} -> {code}")
    
    print("\n=== Print Statements ===")
    for path, line, code in check_print_statements():
        print(f"{path}:{line} -> {code}")
```

실행:
```bash
python tools/code_quality_check.py
```

