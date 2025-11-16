"""
검증 서비스

데이터 유효성 검증, Spec 범위 체크, 타입 검증, 비즈니스 규칙 검증을 제공합니다.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import logging
import pandas as pd
import numpy as np
from datetime import datetime

from ..interfaces.validation_service_interface import (
    IValidationService, ValidationResult, ValidationIssue,
    ValidationSeverity, ValidationStatus
)


class ValidationService(IValidationService):
    """데이터 검증 서비스 구현"""

    def __init__(self, db_schema=None):
        """
        검증 서비스 초기화

        Args:
            db_schema: 데이터베이스 스키마 인스턴스 (선택적)
        """
        self.db_schema = db_schema
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_against_defaults(self, data: pd.DataFrame, equipment_type_id: int) -> ValidationResult:
        """
        Default DB 기준으로 데이터 검증

        Args:
            data: 검증할 데이터프레임
            equipment_type_id: 장비 유형 ID

        Returns:
            검증 결과
        """
        start_time = datetime.now()
        issues = []

        try:
            # Default DB 값 조회
            defaults = self._get_default_values(equipment_type_id)
            if not defaults:
                self.logger.warning(f"장비 유형 {equipment_type_id}의 Default DB 값이 없습니다")
                return self._create_empty_result(start_time)

            # 각 파라미터 검증
            for param_name, default_info in defaults.items():
                if param_name not in data.columns:
                    issues.append(ValidationIssue(
                        parameter=param_name,
                        issue_type="missing_parameter",
                        description="Default DB에는 있으나 데이터에 없음",
                        severity=ValidationSeverity.MEDIUM,
                        status=ValidationStatus.WARNING,
                        expected=default_info['default_value']
                    ))
                    continue

                # 값 검증
                value = str(data[param_name].iloc[0]) if len(data) > 0 else None
                if value:
                    # 범위 검증
                    if default_info.get('min_spec') or default_info.get('max_spec'):
                        issue = self._validate_range(
                            param_name, value,
                            default_info.get('min_spec'),
                            default_info.get('max_spec')
                        )
                        if issue:
                            issues.append(issue)

            # 결과 생성
            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(issues, len(data.columns), execution_time)

        except Exception as e:
            self.logger.error(f"Default DB 검증 실패: {str(e)}")
            raise

    def validate_data_types(self, data: pd.DataFrame) -> ValidationResult:
        """
        데이터 타입 검증

        Args:
            data: 검증할 데이터프레임

        Returns:
            검증 결과
        """
        start_time = datetime.now()
        issues = []

        try:
            for column in data.columns:
                col_data = data[column]

                # 빈 값 체크
                if col_data.isnull().any():
                    null_count = col_data.isnull().sum()
                    issues.append(ValidationIssue(
                        parameter=column,
                        issue_type="null_values",
                        description=f"{null_count}개의 빈 값 발견",
                        severity=ValidationSeverity.LOW,
                        status=ValidationStatus.WARNING
                    ))

                # 데이터 타입 일관성 체크
                if not col_data.isnull().all():
                    non_null = col_data.dropna()
                    # 숫자형으로 변환 가능한지 체크
                    try:
                        pd.to_numeric(non_null)
                    except (ValueError, TypeError):
                        # 문자열 타입
                        pass

            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(issues, len(data.columns), execution_time)

        except Exception as e:
            self.logger.error(f"데이터 타입 검증 실패: {str(e)}")
            raise

    def validate_ranges(self, data: pd.DataFrame, range_specs: Dict[str, tuple]) -> ValidationResult:
        """
        데이터 범위 검증

        Args:
            data: 검증할 데이터프레임
            range_specs: 범위 스펙 딕셔너리 {param_name: (min, max), ...}

        Returns:
            검증 결과
        """
        start_time = datetime.now()
        issues = []

        try:
            for param_name, (min_val, max_val) in range_specs.items():
                if param_name not in data.columns:
                    continue

                value = str(data[param_name].iloc[0]) if len(data) > 0 else None
                if value:
                    issue = self._validate_range(param_name, value, min_val, max_val)
                    if issue:
                        issues.append(issue)

            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(issues, len(data.columns), execution_time)

        except Exception as e:
            self.logger.error(f"범위 검증 실패: {str(e)}")
            raise

    def validate_required_fields(self, data: pd.DataFrame, required_fields: List[str]) -> ValidationResult:
        """
        필수 필드 검증

        Args:
            data: 검증할 데이터프레임
            required_fields: 필수 필드 리스트

        Returns:
            검증 결과
        """
        start_time = datetime.now()
        issues = []

        try:
            for field in required_fields:
                if field not in data.columns:
                    issues.append(ValidationIssue(
                        parameter=field,
                        issue_type="missing_required_field",
                        description="필수 필드가 누락됨",
                        severity=ValidationSeverity.CRITICAL,
                        status=ValidationStatus.FAILED
                    ))
                elif data[field].isnull().all():
                    issues.append(ValidationIssue(
                        parameter=field,
                        issue_type="empty_required_field",
                        description="필수 필드가 비어있음",
                        severity=ValidationSeverity.CRITICAL,
                        status=ValidationStatus.FAILED
                    ))

            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(issues, len(data.columns), execution_time)

        except Exception as e:
            self.logger.error(f"필수 필드 검증 실패: {str(e)}")
            raise

    def validate_custom_rules(self, data: pd.DataFrame, rules: List[str]) -> ValidationResult:
        """
        커스텀 검증 규칙 적용

        Args:
            data: 검증할 데이터프레임
            rules: 검증 규칙 리스트

        Returns:
            검증 결과
        """
        start_time = datetime.now()
        issues = []

        try:
            # TODO: 커스텀 규칙 파싱 및 적용 로직 구현
            # 현재는 기본 구현만 제공
            self.logger.info(f"커스텀 규칙 {len(rules)}개 적용")

            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(issues, len(data.columns), execution_time)

        except Exception as e:
            self.logger.error(f"커스텀 규칙 검증 실패: {str(e)}")
            raise

    # Helper methods

    def _get_default_values(self, equipment_type_id: int) -> Dict[str, Dict[str, Any]]:
        """Default DB 값 조회"""
        if not self.db_schema:
            return {}

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT parameter_name, default_value, min_spec, max_spec
                    FROM Default_DB_Values
                    WHERE equipment_type_id = ?
                """, (equipment_type_id,))

                rows = cursor.fetchall()
                return {
                    row[0]: {
                        'default_value': row[1],
                        'min_spec': row[2],
                        'max_spec': row[3]
                    }
                    for row in rows
                }

        except Exception as e:
            self.logger.error(f"Default DB 값 조회 실패: {str(e)}")
            return {}

    def _validate_range(self, param_name: str, value: str,
                       min_spec: Optional[str], max_spec: Optional[str]) -> Optional[ValidationIssue]:
        """범위 검증"""
        try:
            val = float(value)

            if min_spec and val < float(min_spec):
                return ValidationIssue(
                    parameter=param_name,
                    issue_type="below_min",
                    description=f"값이 최소값({min_spec})보다 작음",
                    severity=ValidationSeverity.HIGH,
                    status=ValidationStatus.FAILED,
                    value=value,
                    expected=f">= {min_spec}"
                )

            if max_spec and val > float(max_spec):
                return ValidationIssue(
                    parameter=param_name,
                    issue_type="above_max",
                    description=f"값이 최대값({max_spec})보다 큼",
                    severity=ValidationSeverity.HIGH,
                    status=ValidationStatus.FAILED,
                    value=value,
                    expected=f"<= {max_spec}"
                )

            return None

        except (ValueError, TypeError):
            return ValidationIssue(
                parameter=param_name,
                issue_type="invalid_number",
                description="숫자 형식이 아님",
                severity=ValidationSeverity.MEDIUM,
                status=ValidationStatus.WARNING,
                value=value
            )

    def _create_result(self, issues: List[ValidationIssue], total_params: int, execution_time: float) -> ValidationResult:
        """검증 결과 생성"""
        failed = sum(1 for i in issues if i.status == ValidationStatus.FAILED)
        warning = sum(1 for i in issues if i.status == ValidationStatus.WARNING)
        passed = total_params - len(issues)

        summary = {
            'critical_count': sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL),
            'high_count': sum(1 for i in issues if i.severity == ValidationSeverity.HIGH),
            'medium_count': sum(1 for i in issues if i.severity == ValidationSeverity.MEDIUM),
            'low_count': sum(1 for i in issues if i.severity == ValidationSeverity.LOW),
        }

        return ValidationResult(
            total_parameters=total_params,
            passed_count=passed,
            failed_count=failed,
            warning_count=warning,
            issues=issues,
            summary=summary,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

    def _create_empty_result(self, start_time: datetime) -> ValidationResult:
        """빈 검증 결과 생성"""
        execution_time = (datetime.now() - start_time).total_seconds()
        return ValidationResult(
            total_parameters=0,
            passed_count=0,
            failed_count=0,
            warning_count=0,
            issues=[],
            summary={},
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )
