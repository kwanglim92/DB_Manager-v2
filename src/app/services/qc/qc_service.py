"""
QC 검증 서비스

이상치 탐지, 데이터 일관성 검사, 결측값 검사, 중복 항목 검사, QC 리포트 생성을 제공합니다.
"""

from typing import List, Dict, Any, Optional
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats

from ..interfaces.validation_service_interface import (
    IQCService, ValidationResult, ValidationIssue, OutlierResult,
    ValidationSeverity, ValidationStatus, QCCheckConfig
)


class QCService(IQCService):
    """QC 검증 서비스 구현"""

    def __init__(self, db_schema=None):
        """
        QC 서비스 초기화

        Args:
            db_schema: 데이터베이스 스키마 인스턴스 (선택적)
        """
        self.db_schema = db_schema
        self.logger = logging.getLogger(self.__class__.__name__)

    def detect_outliers(self, data: pd.DataFrame, method: str = "zscore", threshold: float = 3.0) -> List[OutlierResult]:
        """
        이상치 탐지

        Args:
            data: 검증할 데이터프레임
            method: 탐지 방법 ("zscore", "iqr", "isolation_forest")
            threshold: 임계값

        Returns:
            이상치 결과 리스트
        """
        outliers = []

        try:
            for column in data.columns:
                col_data = data[column]

                # 숫자형 컬럼만 처리
                try:
                    numeric_data = pd.to_numeric(col_data, errors='coerce').dropna()
                    if len(numeric_data) < 2:
                        continue

                    if method == "zscore":
                        outliers.extend(self._detect_outliers_zscore(column, numeric_data, threshold))
                    elif method == "iqr":
                        outliers.extend(self._detect_outliers_iqr(column, numeric_data))
                    else:
                        self.logger.warning(f"지원하지 않는 이상치 탐지 방법: {method}")

                except (ValueError, TypeError):
                    continue

            self.logger.info(f"이상치 {len(outliers)}개 탐지 (방법: {method}, 임계값: {threshold})")
            return outliers

        except Exception as e:
            self.logger.error(f"이상치 탐지 실패: {str(e)}")
            raise

    def check_data_consistency(self, data: pd.DataFrame) -> ValidationResult:
        """
        데이터 일관성 검사

        Args:
            data: 검증할 데이터프레임

        Returns:
            검증 결과
        """
        start_time = datetime.now()
        issues = []

        try:
            # 각 컬럼의 일관성 체크
            for column in data.columns:
                col_data = data[column]

                # 데이터 타입 일관성
                if len(col_data) > 0:
                    types = col_data.apply(lambda x: type(x).__name__).unique()
                    if len(types) > 2:  # None 타입 포함해서 2개까지는 허용
                        issues.append(ValidationIssue(
                            parameter=column,
                            issue_type="inconsistent_types",
                            description=f"여러 데이터 타입 발견: {', '.join(types)}",
                            severity=ValidationSeverity.MEDIUM,
                            status=ValidationStatus.WARNING
                        ))

            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(issues, len(data.columns), execution_time)

        except Exception as e:
            self.logger.error(f"데이터 일관성 검사 실패: {str(e)}")
            raise

    def check_missing_values(self, data: pd.DataFrame) -> ValidationResult:
        """
        결측값 검사

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
                null_count = col_data.isnull().sum()

                if null_count > 0:
                    null_percentage = (null_count / len(col_data)) * 100

                    severity = ValidationSeverity.LOW
                    if null_percentage > 50:
                        severity = ValidationSeverity.CRITICAL
                    elif null_percentage > 20:
                        severity = ValidationSeverity.HIGH
                    elif null_percentage > 10:
                        severity = ValidationSeverity.MEDIUM

                    issues.append(ValidationIssue(
                        parameter=column,
                        issue_type="missing_values",
                        description=f"{null_count}개 ({null_percentage:.1f}%) 결측값 발견",
                        severity=severity,
                        status=ValidationStatus.WARNING if null_percentage < 50 else ValidationStatus.FAILED
                    ))

            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(issues, len(data.columns), execution_time)

        except Exception as e:
            self.logger.error(f"결측값 검사 실패: {str(e)}")
            raise

    def check_duplicate_entries(self, data: pd.DataFrame) -> ValidationResult:
        """
        중복 항목 검사

        Args:
            data: 검증할 데이터프레임

        Returns:
            검증 결과
        """
        start_time = datetime.now()
        issues = []

        try:
            # 전체 행 중복 체크
            duplicate_rows = data.duplicated().sum()
            if duplicate_rows > 0:
                issues.append(ValidationIssue(
                    parameter="전체 행",
                    issue_type="duplicate_rows",
                    description=f"{duplicate_rows}개의 중복 행 발견",
                    severity=ValidationSeverity.MEDIUM,
                    status=ValidationStatus.WARNING
                ))

            # 각 컬럼 중복 체크
            for column in data.columns:
                duplicates = data[column].duplicated().sum()
                if duplicates > 0:
                    dup_percentage = (duplicates / len(data)) * 100
                    if dup_percentage > 50:  # 50% 이상 중복은 정상일 수 있음
                        continue

                    issues.append(ValidationIssue(
                        parameter=column,
                        issue_type="duplicate_values",
                        description=f"{duplicates}개 ({dup_percentage:.1f}%) 중복값 발견",
                        severity=ValidationSeverity.LOW,
                        status=ValidationStatus.WARNING
                    ))

            execution_time = (datetime.now() - start_time).total_seconds()
            return self._create_result(issues, len(data.columns), execution_time)

        except Exception as e:
            self.logger.error(f"중복 항목 검사 실패: {str(e)}")
            raise

    def run_full_qc_check(self, data: pd.DataFrame, equipment_type_id: int, config: QCCheckConfig) -> ValidationResult:
        """
        전체 QC 검사 수행

        Args:
            data: 검증할 데이터프레임
            equipment_type_id: 장비 유형 ID
            config: QC 검사 설정

        Returns:
            종합 검증 결과
        """
        start_time = datetime.now()
        all_issues = []

        try:
            self.logger.info(f"전체 QC 검사 시작 (장비 유형: {equipment_type_id})")

            # 1. 이상치 검사
            if config.check_outliers:
                outliers = self.detect_outliers(data, config.outlier_method, config.outlier_threshold)
                for outlier in outliers:
                    all_issues.append(ValidationIssue(
                        parameter=outlier.parameter,
                        issue_type="outlier",
                        description=f"이상치 감지: {outlier.value} (편차: {outlier.deviation:.2f})",
                        severity=ValidationSeverity.MEDIUM,
                        status=ValidationStatus.WARNING,
                        value=str(outlier.value),
                        expected=f"{outlier.expected_range[0]} ~ {outlier.expected_range[1]}"
                    ))

            # 2. 결측값 검사
            if config.check_missing_values:
                result = self.check_missing_values(data)
                all_issues.extend(result.issues)

            # 3. 중복 항목 검사
            if config.check_duplicates:
                result = self.check_duplicate_entries(data)
                all_issues.extend(result.issues)

            # 4. 데이터 타입 검사
            if config.check_data_types:
                result = self.check_data_consistency(data)
                all_issues.extend(result.issues)

            execution_time = (datetime.now() - start_time).total_seconds()
            final_result = self._create_result(all_issues, len(data.columns), execution_time)

            self.logger.info(f"전체 QC 검사 완료: {final_result.passed_count} 통과, "
                           f"{final_result.failed_count} 실패, {final_result.warning_count} 경고")

            return final_result

        except Exception as e:
            self.logger.error(f"전체 QC 검사 실패: {str(e)}")
            raise

    def generate_qc_report(self, validation_result: ValidationResult, format: str = "html") -> str:
        """
        QC 리포트 생성

        Args:
            validation_result: 검증 결과
            format: 리포트 형식 ("html", "text")

        Returns:
            리포트 문자열
        """
        try:
            if format == "html":
                return self._generate_html_report(validation_result)
            elif format == "text":
                return self._generate_text_report(validation_result)
            else:
                self.logger.warning(f"지원하지 않는 리포트 형식: {format}")
                return self._generate_text_report(validation_result)

        except Exception as e:
            self.logger.error(f"QC 리포트 생성 실패: {str(e)}")
            raise

    def get_qc_statistics(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """
        QC 통계 정보 조회

        Args:
            validation_result: 검증 결과

        Returns:
            통계 정보 딕셔너리
        """
        stats = {
            'total_parameters': validation_result.total_parameters,
            'passed_count': validation_result.passed_count,
            'failed_count': validation_result.failed_count,
            'warning_count': validation_result.warning_count,
            'pass_rate': (validation_result.passed_count / validation_result.total_parameters * 100)
                        if validation_result.total_parameters > 0 else 0,
            'execution_time': validation_result.execution_time,
            'timestamp': validation_result.timestamp,
            'severity_breakdown': validation_result.summary
        }

        return stats

    # Helper methods

    def _detect_outliers_zscore(self, column: str, data: pd.Series, threshold: float) -> List[OutlierResult]:
        """Z-score 방법으로 이상치 탐지"""
        outliers = []

        try:
            mean = data.mean()
            std = data.std()

            if std == 0:  # 표준편차가 0이면 모든 값이 동일
                return outliers

            z_scores = np.abs((data - mean) / std)

            for idx, z_score in z_scores.items():
                if z_score > threshold:
                    outliers.append(OutlierResult(
                        parameter=column,
                        value=float(data[idx]),
                        expected_range=(mean - threshold * std, mean + threshold * std),
                        deviation=float(z_score),
                        method="zscore",
                        confidence=min(z_score / threshold, 1.0),
                        is_outlier=True
                    ))

        except Exception as e:
            self.logger.warning(f"Z-score 이상치 탐지 실패 ({column}): {str(e)}")

        return outliers

    def _detect_outliers_iqr(self, column: str, data: pd.Series) -> List[OutlierResult]:
        """IQR 방법으로 이상치 탐지"""
        outliers = []

        try:
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            for idx, value in data.items():
                if value < lower_bound or value > upper_bound:
                    deviation = min(abs(value - lower_bound), abs(value - upper_bound)) / IQR
                    outliers.append(OutlierResult(
                        parameter=column,
                        value=float(value),
                        expected_range=(lower_bound, upper_bound),
                        deviation=float(deviation),
                        method="iqr",
                        confidence=min(deviation, 1.0),
                        is_outlier=True
                    ))

        except Exception as e:
            self.logger.warning(f"IQR 이상치 탐지 실패 ({column}): {str(e)}")

        return outliers

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

    def _generate_html_report(self, result: ValidationResult) -> str:
        """HTML 리포트 생성"""
        html = f"""
        <html>
        <head><title>QC 검증 리포트</title></head>
        <body>
            <h1>QC 검증 리포트</h1>
            <p>생성 시각: {result.timestamp}</p>
            <h2>요약</h2>
            <ul>
                <li>전체 파라미터: {result.total_parameters}</li>
                <li>통과: {result.passed_count}</li>
                <li>실패: {result.failed_count}</li>
                <li>경고: {result.warning_count}</li>
                <li>실행 시간: {result.execution_time:.2f}초</li>
            </ul>
            <h2>이슈 목록</h2>
            <table border="1">
                <tr><th>파라미터</th><th>타입</th><th>설명</th><th>심각도</th></tr>
        """

        for issue in result.issues:
            html += f"""
                <tr>
                    <td>{issue.parameter}</td>
                    <td>{issue.issue_type}</td>
                    <td>{issue.description}</td>
                    <td>{issue.severity.value}</td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        return html

    def _generate_text_report(self, result: ValidationResult) -> str:
        """텍스트 리포트 생성"""
        lines = [
            "=" * 60,
            "QC 검증 리포트",
            "=" * 60,
            f"생성 시각: {result.timestamp}",
            f"실행 시간: {result.execution_time:.2f}초",
            "",
            "요약:",
            f"  전체 파라미터: {result.total_parameters}",
            f"  통과: {result.passed_count}",
            f"  실패: {result.failed_count}",
            f"  경고: {result.warning_count}",
            "",
            "이슈 목록:",
        ]

        for i, issue in enumerate(result.issues, 1):
            lines.append(f"{i}. [{issue.severity.value}] {issue.parameter}: {issue.description}")

        lines.append("=" * 60)

        return "\n".join(lines)
