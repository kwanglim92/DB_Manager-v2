# DB Manager v2 사용자 가이드 업데이트

**최종 업데이트**: 2025-11-16
**버전**: v2.1 (Code Quality Improvement + 단기 계획 완료)

---

## 주요 신규 기능

### 1. Configuration Management (Phase 1.5)

#### 1.1 Type Common ↔ Configuration-specific 변환

**위치**: Default DB 관리 탭 → Parameter 우클릭 메뉴

**기능**:
- **Convert to Type Common**: Configuration-specific 파라미터를 Type 공통으로 변환
  - 선택한 Configuration의 파라미터가 모든 Configuration에서 사용 가능해짐
  - 중복 파라미터 자동 병합

- **Convert to Configuration-specific**: Type Common 파라미터를 특정 Configuration 전용으로 변환
  - 선택한 Configuration에만 적용되는 파라미터로 변경
  - 다른 Configuration에는 영향 없음 (기존 Type Common 유지)

**사용 방법**:
1. Default DB 관리 탭에서 Configuration 선택
2. 파라미터 선택 (다중 선택 가능)
3. 우클릭 → "Convert to Type Common" 또는 "Convert to Configuration-specific"
4. 확인 다이얼로그에서 "Yes" 클릭

**권한**: 관리자 모드 필요

**예시**:
```
시나리오 1: Configuration A의 "Temperature" 파라미터를 Type Common으로 변환
  → 모든 Configuration (A, B, C)에서 "Temperature" 파라미터 사용 가능

시나리오 2: Type Common "Voltage" 파라미터를 Configuration B 전용으로 변환
  → Configuration B에만 "Voltage" 파라미터 적용 (A, C는 기존 Type Common 사용)
```

#### 1.2 Equipment Hierarchy Tree View

**위치**: 관리자 모드 → 🏗️ Equipment Hierarchy 관리

**기능**:
- 3단계 계층 구조 시각화: Model → Type → Configuration
- Combobox 기반 Model 선택 (UX 개선)
- Configuration 추가/수정/삭제
- 계층별 아이콘 표시 (📁 Model, 🔧 Type, ⚙️ Configuration)

**사용 방법**:
1. 관리자 모드 진입
2. "🏗️ Equipment Hierarchy 관리" 버튼 클릭
3. Tree View에서 항목 선택
4. 우클릭 → Add/Edit/Delete

### 2. 커스텀 검증 규칙 (Phase P4)

#### 2.1 ValidationService Custom Rules

**지원 규칙**:
1. **Range**: 숫자 범위 검증
   ```json
   {"type": "range", "column": "Temperature", "min": 20, "max": 80}
   ```

2. **Regex**: 정규식 패턴 검증
   ```json
   {"type": "regex", "column": "SerialNumber", "pattern": "^[A-Z]{2}\\d{6}$"}
   ```

3. **Enum**: 허용된 값 목록 검증
   ```json
   {"type": "enum", "column": "Status", "values": ["OK", "NG"]}
   ```

4. **Required**: 필수 값 검증 (NULL/빈 값 불허)
   ```json
   {"type": "required", "column": "PartNumber"}
   ```

5. **Unique**: 유니크 값 검증 (중복 불허)
   ```json
   {"type": "unique", "column": "ID"}
   ```

**사용 방법**:
- QC 검수 시 자동 적용
- Check list 항목에 validation_rule JSON으로 정의

### 3. PDF 보고서 생성 (향후 지원)

**현재 상태**: HTML 보고서 생성 지원

**PDF 변환 옵션** (외부 라이브러리 필요):
1. **weasyprint** (권장, 순수 Python)
   ```bash
   pip install weasyprint
   ```

2. **pdfkit** (wkhtmltopdf 필요)
   ```bash
   pip install pdfkit
   ```

3. **xhtml2pdf** (간단)
   ```bash
   pip install xhtml2pdf
   ```

**향후 업데이트**: Phase 2 완료 후 PDF 자동 변환 지원 예정

---

## 개선된 UI/UX

### 1. Combobox Selection Dialog

**변경 전**: simpledialog (텍스트 입력)
**변경 후**: Combobox 다이얼로그 (드롭다운 선택)

**장점**:
- 오타 방지
- 사용 가능한 옵션 명확히 표시
- 마우스 클릭만으로 선택 가능

**적용 위치**:
- Equipment Type 추가 시 Model 선택
- Configuration 추가 시 Port/Wafer Type 선택

### 2. Port/Wafer Type 자동 추론

**기능**: Configuration 수정 시 Port/Wafer Type 자동 추론

**추론 로직**:
1. custom_options JSON에서 port_type 정보 확인
2. 없으면 port_count 기반 추론:
   - port_count = 1 → "Single Port"
   - port_count = 2 → "Double Port"
   - port_count >= 3 → "Multi Port"

**장점**: 데이터 일관성 유지, 휴먼 에러 방지

---

## 코드 품질 개선 (v2.1)

### 전체 품질 점수: 6.0/10 → 8.0/10 (+33%)

**주요 개선 사항**:
- ✅ Bare except 100% 제거 (18개 → 0개)
- ✅ print() 100% 제거 (69개 → 0개)
- ✅ 헬퍼 메서드 66개 추가
- ✅ 평균 메서드 크기 76% 감소 (120 lines → 29 lines)
- ✅ 서비스 레이어 200% 확장 (3개 → 9개)
- ✅ 테스트 커버리지 20%+ 달성 (42개 테스트)

**사용자 영향**:
- 더 빠른 응답 속도
- 더 명확한 에러 메시지
- 더 안정적인 동작
- 더 나은 로깅 (문제 추적 용이)

---

## 알려진 제한사항

### 1. PDF 변환
- **현재**: HTML 보고서만 지원
- **해결**: 외부 라이브러리 설치 필요 (weasyprint/pdfkit/xhtml2pdf)

### 2. Edit Dialog
- **현재**: Model/Type 수정 시 simpledialog 사용
- **향후**: 상세 Edit Dialog (description, display_order 편집 가능)

### 3. 환경 의존성
- **pandas**: 데이터 처리 필수
- **tkinter**: GUI 필수
- **Python 3.7+**: 최소 요구사항

---

## FAQ

### Q1: Configuration-specific 파라미터와 Type Common 파라미터의 차이는?
**A**:
- **Configuration-specific**: 특정 Configuration에만 적용 (예: Config A의 특수 온도)
- **Type Common**: 모든 Configuration에 공통 적용 (예: 모든 장비의 전압)

### Q2: Convert 기능이 비활성화되어 있어요
**A**: 관리자 모드에서만 사용 가능합니다. "도움말 → 🔐 Maintenance" (비밀번호: 1234)

### Q3: PDF 보고서가 생성되지 않아요
**A**: 외부 라이브러리 설치 필요합니다. `pip install weasyprint` 실행 후 재시도하세요.

### Q4: 커스텀 검증 규칙은 어디서 설정하나요?
**A**: QC Checklist 관리에서 각 항목의 validation_rule을 JSON으로 설정합니다.

---

## 다음 업데이트 예정

### Phase 1.5 완료 (2-3주 내)
- Equipment Hierarchy 완전 통합
- QC Check list ItemName 자동 매칭
- Configuration Exception 관리

### Phase 2 (1-2개월 내)
- Shipped Equipment Raw Data 관리
- 통계 분석 및 시각화
- Default DB 자동 업데이트

### Phase 3 (3-6개월 내)
- 모듈 기반 동적 DB 생성
- 구성 템플릿 관리
- 호환성 자동 검증

---

**문의**: 문제가 발생하면 GitHub Issues에 보고해주세요
**문서**: CLAUDE.md 참조
**버전 히스토리**: docs/FINAL_QUALITY_ASSESSMENT.md 참조
