"""
Mother DB 관리 서비스

Mother DB 관리, 후보 분석, 자동 업데이트 기능을 제공합니다.
"""

from typing import List, Dict, Any, Optional
import logging
import pandas as pd
from datetime import datetime
from collections import Counter

from ..interfaces.motherdb_service_interface import (
    IMotherDBService, CandidateParameter, MotherDBAnalysis
)


class MotherDBService(IMotherDBService):
    """Mother DB 관리 서비스 구현"""

    def __init__(self, db_schema):
        """
        Mother DB 서비스 초기화

        Args:
            db_schema: 데이터베이스 스키마 인스턴스
        """
        self.db_schema = db_schema
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze_candidates(self, files_data: List[pd.DataFrame],
                          threshold: float = 0.8) -> MotherDBAnalysis:
        """
        파라미터 후보 분석 (80% 이상 일치)

        Args:
            files_data: 파일 데이터 리스트
            threshold: 일치 임계값 (기본: 0.8 = 80%)

        Returns:
            Mother DB 분석 결과
        """
        start_time = datetime.now()

        try:
            total_files = len(files_data)
            if total_files == 0:
                self.logger.warning("분석할 파일이 없습니다")
                return self._create_empty_analysis(0, threshold, start_time)

            # 모든 파라미터 수집
            all_params = set()
            for df in files_data:
                all_params.update(df.columns)

            # 각 파라미터의 값 빈도 계산
            candidates = []

            for param in all_params:
                values = []
                for df in files_data:
                    if param in df.columns:
                        value = str(df[param].iloc[0]) if len(df) > 0 else ""
                        if value:  # 빈 값 제외
                            values.append(value)

                if not values:
                    continue

                # 가장 많이 나타나는 값 찾기
                value_counts = Counter(values)
                most_common_value, occurrence_count = value_counts.most_common(1)[0]

                occurrence_percentage = occurrence_count / total_files
                confidence = occurrence_percentage

                # 임계값 이상인 경우 추천
                is_recommended = occurrence_percentage >= threshold

                candidates.append(CandidateParameter(
                    parameter_name=param,
                    candidate_value=most_common_value,
                    occurrence_count=occurrence_count,
                    occurrence_percentage=occurrence_percentage,
                    confidence=confidence,
                    is_recommended=is_recommended
                ))

            # 추천 후보만 필터링
            recommended = [c for c in candidates if c.is_recommended]

            execution_time = (datetime.now() - start_time).total_seconds()

            analysis = MotherDBAnalysis(
                equipment_type_id=0,  # 나중에 설정
                total_parameters=len(all_params),
                recommended_candidates=recommended,
                threshold=threshold,
                analysis_time=execution_time
            )

            self.logger.info(
                f"후보 분석 완료: {len(all_params)}개 파라미터 중 {len(recommended)}개 추천 "
                f"(임계값: {threshold*100:.0f}%)"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"후보 분석 실패: {str(e)}")
            raise

    def update_mother_db(self, equipment_type_id: int,
                        candidates: List[CandidateParameter]) -> int:
        """
        Mother DB 업데이트

        Args:
            equipment_type_id: 장비 유형 ID
            candidates: 후보 파라미터 리스트

        Returns:
            업데이트된 파라미터 개수
        """
        count = 0
        timestamp = datetime.now().isoformat()

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                for candidate in candidates:
                    try:
                        # 기존 파라미터 확인
                        cursor.execute("""
                            SELECT id FROM Default_DB_Values
                            WHERE equipment_type_id = ? AND parameter_name = ?
                        """, (equipment_type_id, candidate.parameter_name))

                        existing = cursor.fetchone()

                        if existing:
                            # 업데이트
                            cursor.execute("""
                                UPDATE Default_DB_Values
                                SET default_value = ?, updated_at = ?
                                WHERE id = ?
                            """, (candidate.candidate_value, timestamp, existing[0]))
                        else:
                            # 삽입
                            cursor.execute("""
                                INSERT INTO Default_DB_Values
                                (equipment_type_id, parameter_name, default_value, created_at)
                                VALUES (?, ?, ?, ?)
                            """, (
                                equipment_type_id,
                                candidate.parameter_name,
                                candidate.candidate_value,
                                timestamp
                            ))

                        count += 1

                    except Exception as e:
                        self.logger.warning(
                            f"파라미터 {candidate.parameter_name} 업데이트 실패: {str(e)}"
                        )

                conn.commit()

            self.logger.info(f"Mother DB 업데이트 완료: {count}개 파라미터")
            return count

        except Exception as e:
            self.logger.error(f"Mother DB 업데이트 실패: {str(e)}")
            raise

    def get_mother_db_parameters(self, equipment_type_id: int) -> List[Dict[str, Any]]:
        """
        Mother DB 파라미터 조회

        Args:
            equipment_type_id: 장비 유형 ID

        Returns:
            파라미터 리스트
        """
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT parameter_name, default_value, min_spec, max_spec
                    FROM Default_DB_Values
                    WHERE equipment_type_id = ?
                    ORDER BY parameter_name
                """, (equipment_type_id,))

                rows = cursor.fetchall()
                parameters = [
                    {
                        'parameter_name': row[0],
                        'default_value': row[1],
                        'min_spec': row[2],
                        'max_spec': row[3]
                    }
                    for row in rows
                ]

                self.logger.info(f"Mother DB 파라미터 {len(parameters)}개 조회")
                return parameters

        except Exception as e:
            self.logger.error(f"Mother DB 파라미터 조회 실패: {str(e)}")
            raise

    def validate_mother_db(self, equipment_type_id: int,
                          test_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Mother DB 유효성 검증

        Args:
            equipment_type_id: 장비 유형 ID
            test_data: 테스트 데이터

        Returns:
            검증 결과 딕셔너리
        """
        try:
            mother_db_params = self.get_mother_db_parameters(equipment_type_id)
            mother_db_dict = {p['parameter_name']: p['default_value'] for p in mother_db_params}

            matched = 0
            mismatched = 0
            missing = 0

            for param_name, expected_value in mother_db_dict.items():
                if param_name in test_data.columns:
                    actual_value = str(test_data[param_name].iloc[0]) if len(test_data) > 0 else ""
                    if actual_value == expected_value:
                        matched += 1
                    else:
                        mismatched += 1
                else:
                    missing += 1

            total = len(mother_db_dict)
            match_rate = (matched / total * 100) if total > 0 else 0

            result = {
                'total_parameters': total,
                'matched': matched,
                'mismatched': mismatched,
                'missing': missing,
                'match_rate': match_rate,
                'is_valid': match_rate >= 80.0  # 80% 이상 일치하면 유효
            }

            self.logger.info(
                f"Mother DB 검증 완료: {matched}/{total} 일치 ({match_rate:.1f}%)"
            )

            return result

        except Exception as e:
            self.logger.error(f"Mother DB 검증 실패: {str(e)}")
            raise

    def quick_setup_mother_db(self, equipment_type_id: int,
                             files_data: List[pd.DataFrame],
                             threshold: float = 0.8) -> int:
        """
        Mother DB 빠른 설정 (분석 + 업데이트)

        Args:
            equipment_type_id: 장비 유형 ID
            files_data: 파일 데이터 리스트
            threshold: 일치 임계값

        Returns:
            설정된 파라미터 개수
        """
        try:
            self.logger.info(f"Mother DB 빠른 설정 시작 (장비: {equipment_type_id})")

            # 1. 후보 분석
            analysis = self.analyze_candidates(files_data, threshold)
            analysis.equipment_type_id = equipment_type_id

            # 2. Mother DB 업데이트
            count = self.update_mother_db(equipment_type_id, analysis.recommended_candidates)

            self.logger.info(
                f"Mother DB 빠른 설정 완료: {count}개 파라미터 "
                f"(분석 시간: {analysis.analysis_time:.2f}초)"
            )

            return count

        except Exception as e:
            self.logger.error(f"Mother DB 빠른 설정 실패: {str(e)}")
            raise

    def _create_empty_analysis(self, equipment_type_id: int, threshold: float,
                              start_time: datetime) -> MotherDBAnalysis:
        """빈 분석 결과 생성"""
        execution_time = (datetime.now() - start_time).total_seconds()
        return MotherDBAnalysis(
            equipment_type_id=equipment_type_id,
            total_parameters=0,
            recommended_candidates=[],
            threshold=threshold,
            analysis_time=execution_time
        )
