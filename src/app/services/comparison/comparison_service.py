"""
파일 비교 서비스

파일 비교 엔진, 차이 분석, 통계 계산 기능을 제공합니다.
"""

from typing import List, Dict, Any, Optional
import logging
import pandas as pd
import numpy as np
from datetime import datetime

from ..interfaces.comparison_service_interface import (
    IComparisonService, ComparisonResult, DifferenceDetail
)


class ComparisonService(IComparisonService):
    """파일 비교 서비스 구현"""

    def __init__(self):
        """비교 서비스 초기화"""
        self.logger = logging.getLogger(self.__class__.__name__)

    def compare_files(self, file1_data: pd.DataFrame, file2_data: pd.DataFrame,
                     tolerance: float = 0.0) -> ComparisonResult:
        """
        두 파일 비교

        Args:
            file1_data: 첫 번째 파일 데이터
            file2_data: 두 번째 파일 데이터
            tolerance: 허용 오차 (기본: 0.0)

        Returns:
            비교 결과
        """
        start_time = datetime.now()

        try:
            # 공통 파라미터 찾기
            params1 = set(file1_data.columns)
            params2 = set(file2_data.columns)

            common = list(params1 & params2)
            missing_in_file1 = list(params2 - params1)
            missing_in_file2 = list(params1 - params2)

            # 차이점 분석
            differences = {}
            different_params = []

            for param in common:
                val1 = str(file1_data[param].iloc[0]) if len(file1_data) > 0 else ""
                val2 = str(file2_data[param].iloc[0]) if len(file2_data) > 0 else ""

                if val1 != val2:
                    # 숫자형 비교 (tolerance 적용)
                    try:
                        num1 = float(val1)
                        num2 = float(val2)
                        diff = abs(num1 - num2)

                        if diff > tolerance:
                            different_params.append(param)
                            differences[param] = {
                                'file1_value': val1,
                                'file2_value': val2,
                                'difference': diff,
                                'percentage': (diff / num1 * 100) if num1 != 0 else 0
                            }
                    except (ValueError, TypeError):
                        # 문자열 비교
                        if val1 != val2:
                            different_params.append(param)
                            differences[param] = {
                                'file1_value': val1,
                                'file2_value': val2,
                                'difference': None,
                                'percentage': None
                            }

            # 통계 계산
            total_params = len(params1 | params2)
            match_rate = (len(common) - len(different_params)) / len(common) * 100 if common else 0

            statistics = {
                'total_parameters': total_params,
                'common_parameters': len(common),
                'different_parameters': len(different_params),
                'missing_in_file1': len(missing_in_file1),
                'missing_in_file2': len(missing_in_file2),
                'match_rate': match_rate
            }

            execution_time = (datetime.now() - start_time).total_seconds()

            result = ComparisonResult(
                common_parameters=common,
                different_parameters=different_params,
                missing_in_file1=missing_in_file1,
                missing_in_file2=missing_in_file2,
                differences=differences,
                statistics=statistics,
                execution_time=execution_time
            )

            self.logger.info(f"파일 비교 완료: {len(common)}개 공통, {len(different_params)}개 차이")
            return result

        except Exception as e:
            self.logger.error(f"파일 비교 실패: {str(e)}")
            raise

    def compare_multiple_files(self, files_data: List[pd.DataFrame]) -> Dict[str, Any]:
        """
        여러 파일 비교

        Args:
            files_data: 파일 데이터 리스트

        Returns:
            비교 결과 딕셔너리
        """
        try:
            if len(files_data) < 2:
                self.logger.warning("비교할 파일이 2개 미만입니다")
                return {}

            # 모든 파라미터 수집
            all_params = set()
            for df in files_data:
                all_params.update(df.columns)

            # 각 파라미터의 값 빈도 계산
            param_values = {param: {} for param in all_params}

            for df in files_data:
                for param in all_params:
                    if param in df.columns:
                        value = str(df[param].iloc[0]) if len(df) > 0 else ""
                        param_values[param][value] = param_values[param].get(value, 0) + 1

            # 통계 계산
            result = {
                'total_files': len(files_data),
                'total_parameters': len(all_params),
                'parameter_values': param_values,
                'common_parameters': [
                    param for param in all_params
                    if all(param in df.columns for df in files_data)
                ],
                'statistics': {
                    'common_count': sum(
                        1 for param in all_params
                        if all(param in df.columns for df in files_data)
                    )
                }
            }

            self.logger.info(f"{len(files_data)}개 파일 비교 완료")
            return result

        except Exception as e:
            self.logger.error(f"다중 파일 비교 실패: {str(e)}")
            raise

    def find_differences(self, file1_data: pd.DataFrame, file2_data: pd.DataFrame,
                        tolerance: float = 0.0) -> List[DifferenceDetail]:
        """
        차이점 찾기

        Args:
            file1_data: 첫 번째 파일 데이터
            file2_data: 두 번째 파일 데이터
            tolerance: 허용 오차

        Returns:
            차이점 상세 리스트
        """
        differences = []

        try:
            common_params = set(file1_data.columns) & set(file2_data.columns)

            for param in common_params:
                val1 = str(file1_data[param].iloc[0]) if len(file1_data) > 0 else ""
                val2 = str(file2_data[param].iloc[0]) if len(file2_data) > 0 else ""

                if val1 != val2:
                    try:
                        num1 = float(val1)
                        num2 = float(val2)
                        diff = abs(num1 - num2)
                        percentage = (diff / num1 * 100) if num1 != 0 else 0

                        differences.append(DifferenceDetail(
                            parameter=param,
                            file1_value=val1,
                            file2_value=val2,
                            difference=diff,
                            percentage=percentage,
                            is_significant=(diff > tolerance)
                        ))
                    except (ValueError, TypeError):
                        differences.append(DifferenceDetail(
                            parameter=param,
                            file1_value=val1,
                            file2_value=val2,
                            difference=None,
                            percentage=None,
                            is_significant=True
                        ))

            self.logger.info(f"차이점 {len(differences)}개 발견")
            return differences

        except Exception as e:
            self.logger.error(f"차이점 찾기 실패: {str(e)}")
            raise

    def calculate_statistics(self, comparison_result: ComparisonResult) -> Dict[str, Any]:
        """
        비교 통계 계산

        Args:
            comparison_result: 비교 결과

        Returns:
            통계 딕셔너리
        """
        stats = {
            'total_compared': len(comparison_result.common_parameters),
            'matched': len(comparison_result.common_parameters) - len(comparison_result.different_parameters),
            'different': len(comparison_result.different_parameters),
            'match_rate': comparison_result.statistics.get('match_rate', 0),
            'missing_count': (
                len(comparison_result.missing_in_file1) +
                len(comparison_result.missing_in_file2)
            ),
            'execution_time': comparison_result.execution_time
        }

        return stats

    def format_comparison_result(self, comparison_result: ComparisonResult,
                                 format: str = "table") -> str:
        """
        비교 결과 포맷팅

        Args:
            comparison_result: 비교 결과
            format: 형식 ("table", "text", "csv")

        Returns:
            포맷팅된 결과 문자열
        """
        if format == "table":
            return self._format_as_table(comparison_result)
        elif format == "text":
            return self._format_as_text(comparison_result)
        elif format == "csv":
            return self._format_as_csv(comparison_result)
        else:
            self.logger.warning(f"지원하지 않는 형식: {format}")
            return self._format_as_text(comparison_result)

    def _format_as_table(self, result: ComparisonResult) -> str:
        """테이블 형식으로 포맷팅"""
        lines = []
        lines.append("=" * 80)
        lines.append("파일 비교 결과")
        lines.append("=" * 80)
        lines.append(f"공통 파라미터: {len(result.common_parameters)}개")
        lines.append(f"차이점: {len(result.different_parameters)}개")
        lines.append(f"일치율: {result.statistics.get('match_rate', 0):.1f}%")
        lines.append("")

        if result.different_parameters:
            lines.append("차이점 상세:")
            lines.append("-" * 80)
            lines.append(f"{'파라미터':<30} {'파일1':<20} {'파일2':<20}")
            lines.append("-" * 80)

            for param in result.different_parameters:
                if param in result.differences:
                    diff = result.differences[param]
                    val1 = diff['file1_value'][:18] if len(diff['file1_value']) > 18 else diff['file1_value']
                    val2 = diff['file2_value'][:18] if len(diff['file2_value']) > 18 else diff['file2_value']
                    lines.append(f"{param:<30} {val1:<20} {val2:<20}")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_as_text(self, result: ComparisonResult) -> str:
        """텍스트 형식으로 포맷팅"""
        lines = [
            "파일 비교 결과",
            f"공통: {len(result.common_parameters)}, 차이: {len(result.different_parameters)}",
            f"일치율: {result.statistics.get('match_rate', 0):.1f}%"
        ]

        if result.different_parameters:
            lines.append("\n차이점:")
            for param in result.different_parameters:
                if param in result.differences:
                    diff = result.differences[param]
                    lines.append(f"  {param}: {diff['file1_value']} → {diff['file2_value']}")

        return "\n".join(lines)

    def _format_as_csv(self, result: ComparisonResult) -> str:
        """CSV 형식으로 포맷팅"""
        lines = ["Parameter,File1,File2,Difference"]

        for param in result.different_parameters:
            if param in result.differences:
                diff = result.differences[param]
                lines.append(
                    f"{param},{diff['file1_value']},{diff['file2_value']},"
                    f"{diff.get('difference', '')}"
                )

        return "\n".join(lines)
