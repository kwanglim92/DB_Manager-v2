"""
탭 UI 컴포넌트

이 패키지는 메인 애플리케이션의 각 탭을 별도 클래스로 분리합니다.

Phase: 중기 계획 Week 1-2 (UI/로직 분리)
"""

from .comparison_tab import ComparisonTab

__all__ = ['ComparisonTab']

# 향후 추가될 탭들:
# from .default_db_tab import DefaultDBTab
# from .qc_tab import QCTab
