"""
파일 비교 서비스 인터페이스

파일 비교 엔진, 차이 분석, 통계 계산을 위한 추상 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd


@dataclass
class ComparisonResult:
    """파일 비교 결과"""
    common_parameters: List[str]
    different_parameters: List[str]
    missing_in_file1: List[str]
    missing_in_file2: List[str]
    differences: Dict[str, Dict[str, Any]]
    statistics: Dict[str, Any]
    execution_time: float


@dataclass
class DifferenceDetail:
    """차이점 상세 정보"""
    parameter: str
    file1_value: str
    file2_value: str
    difference: Optional[float]
    percentage: Optional[float]
    is_significant: bool


class IComparisonService(ABC):
    """파일 비교 서비스 인터페이스"""

    @abstractmethod
    def compare_files(self, file1_data: pd.DataFrame, file2_data: pd.DataFrame,
                     tolerance: float = 0.0) -> ComparisonResult:
        """두 파일 비교"""
        pass

    @abstractmethod
    def compare_multiple_files(self, files_data: List[pd.DataFrame]) -> Dict[str, Any]:
        """여러 파일 비교"""
        pass

    @abstractmethod
    def find_differences(self, file1_data: pd.DataFrame, file2_data: pd.DataFrame,
                        tolerance: float = 0.0) -> List[DifferenceDetail]:
        """차이점 찾기"""
        pass

    @abstractmethod
    def calculate_statistics(self, comparison_result: ComparisonResult) -> Dict[str, Any]:
        """비교 통계 계산"""
        pass

    @abstractmethod
    def format_comparison_result(self, comparison_result: ComparisonResult,
                                 format: str = "table") -> str:
        """비교 결과 포맷팅"""
        pass
