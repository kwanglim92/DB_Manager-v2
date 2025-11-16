"""
보고서 생성 서비스

HTML/Excel 보고서 생성, 템플릿 관리 기능을 제공합니다.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import os

from ..interfaces.report_service_interface import (
    IReportService, ReportTemplate, ReportData
)


class ReportService(IReportService):
    """보고서 생성 서비스 구현"""

    def __init__(self):
        """보고서 서비스 초기화"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.templates = {}
        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """기본 템플릿 초기화"""
        self.templates['qc_report'] = ReportTemplate(
            template_name='qc_report',
            template_type='html',
            sections=['summary', 'basic_qc', 'checklist', 'recommendations']
        )

        self.templates['comparison_report'] = ReportTemplate(
            template_name='comparison_report',
            template_type='html',
            sections=['summary', 'common_params', 'differences', 'statistics']
        )

    def generate_html_report(self, data: ReportData,
                            template: Optional[ReportTemplate] = None) -> str:
        """
        HTML 보고서 생성

        Args:
            data: 보고서 데이터
            template: 템플릿 (선택적)

        Returns:
            HTML 문자열
        """
        try:
            html = f"""
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{data.title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
                    h2 {{ color: #555; margin-top: 30px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #007bff; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    .summary {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; }}
                    .metadata {{ color: #666; font-size: 0.9em; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <h1>{data.title}</h1>
                <div class="metadata">
                    <p>생성 시각: {data.timestamp}</p>
            """

            # 메타데이터 추가
            for key, value in data.metadata.items():
                html += f"<p>{key}: {value}</p>"

            html += "</div>"

            # 요약 섹션
            if data.summary:
                html += '<div class="summary"><h2>요약</h2><ul>'
                for key, value in data.summary.items():
                    html += f"<li><strong>{key}:</strong> {value}</li>"
                html += "</ul></div>"

            # 상세 섹션
            if data.details:
                html += "<h2>상세 정보</h2>"
                for section_name, section_data in data.details.items():
                    html += f"<h3>{section_name}</h3>"

                    if isinstance(section_data, dict):
                        html += "<table><tr><th>항목</th><th>값</th></tr>"
                        for item_key, item_value in section_data.items():
                            html += f"<tr><td>{item_key}</td><td>{item_value}</td></tr>"
                        html += "</table>"
                    elif isinstance(section_data, list):
                        html += "<ul>"
                        for item in section_data:
                            html += f"<li>{item}</li>"
                        html += "</ul>"
                    else:
                        html += f"<p>{section_data}</p>"

            html += """
            </body>
            </html>
            """

            self.logger.info(f"HTML 보고서 생성 완료: {data.title}")
            return html

        except Exception as e:
            self.logger.error(f"HTML 보고서 생성 실패: {str(e)}")
            raise

    def generate_excel_report(self, data: ReportData, file_path: str) -> bool:
        """
        Excel 보고서 생성

        Args:
            data: 보고서 데이터
            file_path: 저장 경로

        Returns:
            생성 성공 여부
        """
        try:
            # pandas와 openpyxl을 사용한 Excel 생성
            import pandas as pd

            # 엑셀 작성기 생성
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 요약 시트
                if data.summary:
                    summary_df = pd.DataFrame([data.summary])
                    summary_df.to_excel(writer, sheet_name='요약', index=False)

                # 상세 시트
                if data.details:
                    for sheet_name, sheet_data in data.details.items():
                        if isinstance(sheet_data, dict):
                            df = pd.DataFrame([sheet_data])
                        elif isinstance(sheet_data, list):
                            df = pd.DataFrame(sheet_data)
                        else:
                            df = pd.DataFrame([{'data': sheet_data}])

                        # 시트 이름 길이 제한 (Excel 제한: 31자)
                        safe_sheet_name = sheet_name[:31]
                        df.to_excel(writer, sheet_name=safe_sheet_name, index=False)

            self.logger.info(f"Excel 보고서 생성 완료: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Excel 보고서 생성 실패: {str(e)}")
            return False

    def generate_pdf_report(self, data: ReportData, file_path: str) -> bool:
        """
        PDF 보고서 생성 (선택적)

        Args:
            data: 보고서 데이터
            file_path: 저장 경로

        Returns:
            생성 성공 여부
        """
        try:
            # HTML을 먼저 생성하고 PDF로 변환 (향후 구현)
            html_content = self.generate_html_report(data)

            # TODO: HTML → PDF 변환 (pdfkit, weasyprint 등 사용)
            self.logger.warning("PDF 생성은 현재 구현되지 않았습니다")
            return False

        except Exception as e:
            self.logger.error(f"PDF 보고서 생성 실패: {str(e)}")
            return False

    def save_report(self, report_content: str, file_path: str, format: str) -> bool:
        """
        보고서 저장

        Args:
            report_content: 보고서 내용
            file_path: 저장 경로
            format: 형식 ("html", "text")

        Returns:
            저장 성공 여부
        """
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 파일 저장
            encoding = 'utf-8' if format in ['html', 'text'] else 'utf-8'
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(report_content)

            self.logger.info(f"보고서 저장 완료: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"보고서 저장 실패: {str(e)}")
            return False

    def get_report_template(self, template_name: str) -> Optional[ReportTemplate]:
        """
        보고서 템플릿 조회

        Args:
            template_name: 템플릿 이름

        Returns:
            템플릿 또는 None
        """
        return self.templates.get(template_name)

    def create_qc_report(self, qc_result: Dict[str, Any]) -> ReportData:
        """
        QC 검수 보고서 데이터 생성

        Args:
            qc_result: QC 검수 결과

        Returns:
            보고서 데이터
        """
        summary = {
            '전체 파라미터': qc_result.get('total_parameters', 0),
            '통과': qc_result.get('passed_count', 0),
            '실패': qc_result.get('failed_count', 0),
            '경고': qc_result.get('warning_count', 0),
            '통과율': f"{qc_result.get('pass_rate', 0):.1f}%"
        }

        details = {
            '기본 QC 검사': qc_result.get('basic_qc', {}),
            'Check list 검증': qc_result.get('checklist', {}),
            '권장사항': qc_result.get('recommendations', [])
        }

        metadata = {
            '장비 유형': qc_result.get('equipment_type', 'N/A'),
            '검수자': qc_result.get('inspector', 'N/A')
        }

        return ReportData(
            title='QC 검수 보고서',
            summary=summary,
            details=details,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )

    def create_comparison_report(self, comparison_result: Dict[str, Any]) -> ReportData:
        """
        파일 비교 보고서 데이터 생성

        Args:
            comparison_result: 파일 비교 결과

        Returns:
            보고서 데이터
        """
        summary = {
            '공통 파라미터': len(comparison_result.get('common_parameters', [])),
            '차이점': len(comparison_result.get('different_parameters', [])),
            '일치율': f"{comparison_result.get('match_rate', 0):.1f}%"
        }

        details = {
            '공통 파라미터': comparison_result.get('common_parameters', []),
            '차이점': comparison_result.get('differences', {}),
            '통계': comparison_result.get('statistics', {})
        }

        metadata = {
            '파일1': comparison_result.get('file1_name', 'N/A'),
            '파일2': comparison_result.get('file2_name', 'N/A')
        }

        return ReportData(
            title='파일 비교 보고서',
            summary=summary,
            details=details,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )
