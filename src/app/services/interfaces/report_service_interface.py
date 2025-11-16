"""
보고서 서비스 인터페이스

HTML/Excel 보고서 생성, 템플릿 관리를 위한 추상 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ReportTemplate:
    """보고서 템플릿"""
    template_name: str
    template_type: str  # "html", "excel", "pdf"
    sections: List[str]
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class ReportData:
    """보고서 데이터"""
    title: str
    summary: Dict[str, Any]
    details: Dict[str, Any]
    metadata: Dict[str, str]
    timestamp: str


class IReportService(ABC):
    """보고서 생성 서비스 인터페이스"""

    @abstractmethod
    def generate_html_report(self, data: ReportData,
                            template: Optional[ReportTemplate] = None) -> str:
        """HTML 보고서 생성"""
        pass

    @abstractmethod
    def generate_excel_report(self, data: ReportData, file_path: str) -> bool:
        """Excel 보고서 생성"""
        pass

    @abstractmethod
    def generate_pdf_report(self, data: ReportData, file_path: str) -> bool:
        """PDF 보고서 생성 (선택적)"""
        pass

    @abstractmethod
    def save_report(self, report_content: str, file_path: str, format: str) -> bool:
        """보고서 저장"""
        pass

    @abstractmethod
    def get_report_template(self, template_name: str) -> Optional[ReportTemplate]:
        """보고서 템플릿 조회"""
        pass

    @abstractmethod
    def create_qc_report(self, qc_result: Dict[str, Any]) -> ReportData:
        """QC 검수 보고서 데이터 생성"""
        pass

    @abstractmethod
    def create_comparison_report(self, comparison_result: Dict[str, Any]) -> ReportData:
        """파일 비교 보고서 데이터 생성"""
        pass
