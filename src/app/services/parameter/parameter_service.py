"""
파라미터 관리 서비스

Default DB 값 CRUD, 검색, 통계 분석, import/export 기능을 제공합니다.
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..interfaces.equipment_service_interface import IParameterService, Parameter
from ..common.cache_service import CacheService


class ParameterService(IParameterService):
    """파라미터 관리 서비스 구현"""

    def __init__(self, db_schema, cache_service: Optional[CacheService] = None):
        """
        파라미터 서비스 초기화

        Args:
            db_schema: 데이터베이스 스키마 인스턴스
            cache_service: 캐시 서비스 (선택적)
        """
        self.db_schema = db_schema
        self.cache = cache_service
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_parameters_by_equipment_type(self, equipment_type_id: int) -> List[Parameter]:
        """
        특정 장비 유형의 파라미터 조회

        Args:
            equipment_type_id: 장비 유형 ID

        Returns:
            파라미터 리스트
        """
        cache_key = f"params_equipment_{equipment_type_id}"

        # 캐시 확인
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                self.logger.debug(f"캐시에서 파라미터 조회: {equipment_type_id}")
                return cached

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, equipment_type_id, parameter_name, default_value,
                           min_spec, max_spec, created_at, updated_at
                    FROM Default_DB_Values
                    WHERE equipment_type_id = ?
                    ORDER BY parameter_name
                """, (equipment_type_id,))

                rows = cursor.fetchall()
                parameters = [
                    Parameter(
                        id=row[0],
                        equipment_type_id=row[1],
                        name=row[2],
                        default_value=row[3],
                        min_spec=row[4],
                        max_spec=row[5],
                        created_at=row[6],
                        updated_at=row[7]
                    ) for row in rows
                ]

                # 캐시 저장
                if self.cache:
                    self.cache.set(cache_key, parameters)

                self.logger.info(f"장비 유형 {equipment_type_id}의 파라미터 {len(parameters)}개 조회")
                return parameters

        except Exception as e:
            self.logger.error(f"파라미터 조회 실패: {str(e)}")
            raise

    def get_parameter(self, parameter_id: int) -> Optional[Parameter]:
        """
        특정 파라미터 조회

        Args:
            parameter_id: 파라미터 ID

        Returns:
            파라미터 객체 또는 None
        """
        cache_key = f"param_{parameter_id}"

        # 캐시 확인
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, equipment_type_id, parameter_name, default_value,
                           min_spec, max_spec, created_at, updated_at
                    FROM Default_DB_Values
                    WHERE id = ?
                """, (parameter_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                parameter = Parameter(
                    id=row[0],
                    equipment_type_id=row[1],
                    name=row[2],
                    default_value=row[3],
                    min_spec=row[4],
                    max_spec=row[5],
                    created_at=row[6],
                    updated_at=row[7]
                )

                # 캐시 저장
                if self.cache:
                    self.cache.set(cache_key, parameter)

                return parameter

        except Exception as e:
            self.logger.error(f"파라미터 {parameter_id} 조회 실패: {str(e)}")
            raise

    def create_parameter(self, parameter: Parameter) -> int:
        """
        새 파라미터 생성

        Args:
            parameter: 파라미터 객체

        Returns:
            생성된 파라미터 ID
        """
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Default_DB_Values
                    (equipment_type_id, parameter_name, default_value, min_spec, max_spec, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    parameter.equipment_type_id,
                    parameter.name,
                    parameter.default_value,
                    parameter.min_spec,
                    parameter.max_spec,
                    datetime.now().isoformat()
                ))
                conn.commit()

                param_id = cursor.lastrowid

                # 캐시 무효화
                if self.cache:
                    self.cache.invalidate(f"params_equipment_{parameter.equipment_type_id}")

                self.logger.info(f"파라미터 생성 완료: {parameter.name} (ID: {param_id})")
                return param_id

        except Exception as e:
            self.logger.error(f"파라미터 생성 실패: {str(e)}")
            raise

    def update_parameter(self, parameter_id: int, parameter: Parameter) -> bool:
        """
        파라미터 정보 수정

        Args:
            parameter_id: 파라미터 ID
            parameter: 수정할 파라미터 객체

        Returns:
            수정 성공 여부
        """
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Default_DB_Values
                    SET parameter_name = ?, default_value = ?,
                        min_spec = ?, max_spec = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    parameter.name,
                    parameter.default_value,
                    parameter.min_spec,
                    parameter.max_spec,
                    datetime.now().isoformat(),
                    parameter_id
                ))
                conn.commit()

                # 캐시 무효화
                if self.cache:
                    self.cache.invalidate(f"param_{parameter_id}")
                    self.cache.invalidate(f"params_equipment_{parameter.equipment_type_id}")

                self.logger.info(f"파라미터 {parameter_id} 수정 완료")
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"파라미터 {parameter_id} 수정 실패: {str(e)}")
            raise

    def delete_parameter(self, parameter_id: int) -> bool:
        """
        파라미터 삭제

        Args:
            parameter_id: 파라미터 ID

        Returns:
            삭제 성공 여부
        """
        try:
            # 먼저 파라미터 정보를 조회 (캐시 무효화용)
            param = self.get_parameter(parameter_id)
            if not param:
                return False

            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Default_DB_Values WHERE id = ?", (parameter_id,))
                conn.commit()

                # 캐시 무효화
                if self.cache:
                    self.cache.invalidate(f"param_{parameter_id}")
                    self.cache.invalidate(f"params_equipment_{param.equipment_type_id}")

                self.logger.info(f"파라미터 {parameter_id} 삭제 완료")
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"파라미터 {parameter_id} 삭제 실패: {str(e)}")
            raise

    def search_parameters(self, query: str, equipment_type_id: Optional[int] = None) -> List[Parameter]:
        """
        파라미터 검색

        Args:
            query: 검색어
            equipment_type_id: 장비 유형 ID (선택적)

        Returns:
            검색된 파라미터 리스트
        """
        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT id, equipment_type_id, parameter_name, default_value,
                           min_spec, max_spec, created_at, updated_at
                    FROM Default_DB_Values
                    WHERE parameter_name LIKE ?
                """
                params = [f"%{query}%"]

                if equipment_type_id:
                    sql += " AND equipment_type_id = ?"
                    params.append(equipment_type_id)

                sql += " ORDER BY parameter_name"

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                parameters = [
                    Parameter(
                        id=row[0],
                        equipment_type_id=row[1],
                        name=row[2],
                        default_value=row[3],
                        min_spec=row[4],
                        max_spec=row[5],
                        created_at=row[6],
                        updated_at=row[7]
                    ) for row in rows
                ]

                self.logger.info(f"파라미터 검색 결과: {len(parameters)}개 (쿼리: {query})")
                return parameters

        except Exception as e:
            self.logger.error(f"파라미터 검색 실패: {str(e)}")
            raise

    def validate_parameter_value(self, parameter_id: int, value: str) -> bool:
        """
        파라미터 값 유효성 검사

        Args:
            parameter_id: 파라미터 ID
            value: 검증할 값

        Returns:
            유효성 검사 통과 여부
        """
        parameter = self.get_parameter(parameter_id)
        if not parameter:
            return False

        # min_spec, max_spec이 있으면 범위 검사
        if parameter.min_spec or parameter.max_spec:
            try:
                val = float(value)

                if parameter.min_spec:
                    min_val = float(parameter.min_spec)
                    if val < min_val:
                        self.logger.warning(f"값 {val}이 최소값 {min_val}보다 작음")
                        return False

                if parameter.max_spec:
                    max_val = float(parameter.max_spec)
                    if val > max_val:
                        self.logger.warning(f"값 {val}이 최대값 {max_val}보다 큼")
                        return False

            except ValueError:
                self.logger.warning(f"숫자 변환 실패: {value}")
                return False

        return True

    def get_parameter_statistics(self, equipment_type_id: int) -> Dict[str, Any]:
        """
        파라미터 통계 조회

        Args:
            equipment_type_id: 장비 유형 ID

        Returns:
            통계 정보 딕셔너리
        """
        parameters = self.get_parameters_by_equipment_type(equipment_type_id)

        stats = {
            'total_count': len(parameters),
            'with_min_spec': sum(1 for p in parameters if p.min_spec),
            'with_max_spec': sum(1 for p in parameters if p.max_spec),
            'with_both_specs': sum(1 for p in parameters if p.min_spec and p.max_spec),
            'parameters': [p.name for p in parameters]
        }

        return stats

    def bulk_import_parameters(self, equipment_type_id: int, parameters: List[Dict[str, str]]) -> int:
        """
        파라미터 일괄 임포트

        Args:
            equipment_type_id: 장비 유형 ID
            parameters: 파라미터 딕셔너리 리스트 [{name, default_value, min_spec, max_spec}, ...]

        Returns:
            임포트된 파라미터 개수
        """
        count = 0
        timestamp = datetime.now().isoformat()

        try:
            with self.db_schema.get_connection() as conn:
                cursor = conn.cursor()

                for param_data in parameters:
                    try:
                        cursor.execute("""
                            INSERT INTO Default_DB_Values
                            (equipment_type_id, parameter_name, default_value, min_spec, max_spec, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            equipment_type_id,
                            param_data.get('name', ''),
                            param_data.get('default_value', ''),
                            param_data.get('min_spec'),
                            param_data.get('max_spec'),
                            timestamp
                        ))
                        count += 1
                    except Exception as e:
                        self.logger.warning(f"파라미터 {param_data.get('name')} 임포트 실패: {str(e)}")

                conn.commit()

                # 캐시 무효화
                if self.cache:
                    self.cache.invalidate(f"params_equipment_{equipment_type_id}")

                self.logger.info(f"{count}개 파라미터 일괄 임포트 완료")
                return count

        except Exception as e:
            self.logger.error(f"일괄 임포트 실패: {str(e)}")
            raise

    def export_parameters(self, equipment_type_id: int) -> List[Dict[str, str]]:
        """
        파라미터 내보내기

        Args:
            equipment_type_id: 장비 유형 ID

        Returns:
            파라미터 딕셔너리 리스트
        """
        parameters = self.get_parameters_by_equipment_type(equipment_type_id)

        return [
            {
                'name': p.name,
                'default_value': p.default_value,
                'min_spec': p.min_spec or '',
                'max_spec': p.max_spec or ''
            }
            for p in parameters
        ]
