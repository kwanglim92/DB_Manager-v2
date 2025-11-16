"""
Mother DB 서비스 인터페이스

Mother DB 관리, 후보 분석, 자동 업데이트를 위한 추상 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd


@dataclass
class CandidateParameter:
    """후보 파라미터"""
    parameter_name: str
    candidate_value: str
    occurrence_count: int
    occurrence_percentage: float
    confidence: float
    is_recommended: bool


@dataclass
class MotherDBAnalysis:
    """Mother DB 분석 결과"""
    equipment_type_id: int
    total_parameters: int
    recommended_candidates: List[CandidateParameter]
    threshold: float
    analysis_time: float


class IMotherDBService(ABC):
    """Mother DB 관리 서비스 인터페이스"""

    @abstractmethod
    def analyze_candidates(self, files_data: List[pd.DataFrame],
                          threshold: float = 0.8) -> MotherDBAnalysis:
        """파라미터 후보 분석 (80% 이상 일치)"""
        pass

    @abstractmethod
    def update_mother_db(self, equipment_type_id: int,
                        candidates: List[CandidateParameter]) -> int:
        """Mother DB 업데이트"""
        pass

    @abstractmethod
    def get_mother_db_parameters(self, equipment_type_id: int) -> List[Dict[str, Any]]:
        """Mother DB 파라미터 조회"""
        pass

    @abstractmethod
    def validate_mother_db(self, equipment_type_id: int,
                          test_data: pd.DataFrame) -> Dict[str, Any]:
        """Mother DB 유효성 검증"""
        pass

    @abstractmethod
    def quick_setup_mother_db(self, equipment_type_id: int,
                             files_data: List[pd.DataFrame],
                             threshold: float = 0.8) -> int:
        """Mother DB 빠른 설정 (분석 + 업데이트)"""
        pass
