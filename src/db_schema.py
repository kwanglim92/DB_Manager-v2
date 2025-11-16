"""
⚠️ DEPRECATED - 이 파일은 더 이상 사용되지 않습니다 ⚠️

Phase 1.5부터 모든 스키마 정의는 app/schema.py로 이동되었습니다.
이 파일은 역호환성을 위해서만 유지됩니다.

사용법:
  - 기존: from db_schema import DBSchema
  - 권장: from app.schema import DBSchema

Phase 1.5/2 테이블 (Equipment_Models, Equipment_Configurations, Shipped_Equipment)은
src/app/schema.py에만 정의되어 있습니다.

이 파일은 향후 버전에서 삭제될 예정입니다.
마지막 업데이트: 2025-11-16
"""

# 역호환성을 위한 re-export
from app.schema import DBSchema

__all__ = ['DBSchema']
