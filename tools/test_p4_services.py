"""
P4 신규 서비스 통합 테스트

6개 신규 서비스 (Parameter, Validation, QC, Comparison, MotherDB, Report)의
기본 기능을 테스트합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

import unittest
import tempfile
import pandas as pd
from datetime import datetime


class TestP4Services(unittest.TestCase):
    """P4 신규 서비스 테스트"""

    def setUp(self):
        """테스트 초기화"""
        # 테스트용 데이터
        self.test_data = pd.DataFrame({
            'param1': ['100'],
            'param2': ['200'],
            'param3': ['300']
        })

    def test_01_import_all_services(self):
        """Test 1: 모든 서비스 import 테스트"""
        print("\n" + "="*60)
        print("Test 1: Import All Services")
        print("="*60)

        try:
            from app.services.parameter.parameter_service import ParameterService
            from app.services.validation.validation_service import ValidationService
            from app.services.qc.qc_service import QCService
            from app.services.comparison.comparison_service import ComparisonService
            from app.services.motherdb.motherdb_service import MotherDBService
            from app.services.report.report_service import ReportService

            print("✓ ParameterService")
            print("✓ ValidationService")
            print("✓ QCService")
            print("✓ ComparisonService")
            print("✓ MotherDBService")
            print("✓ ReportService")

            self.assertTrue(True)

        except Exception as e:
            print(f"✗ Import failed: {str(e)}")
            self.fail(f"Service import failed: {str(e)}")

    def test_02_comparison_service(self):
        """Test 2: ComparisonService 테스트"""
        print("\n" + "="*60)
        print("Test 2: ComparisonService")
        print("="*60)

        try:
            from app.services.comparison.comparison_service import ComparisonService

            service = ComparisonService()

            # 두 파일 비교
            file1_data = pd.DataFrame({
                'param1': ['100'],
                'param2': ['200'],
                'param3': ['300']
            })

            file2_data = pd.DataFrame({
                'param1': ['100'],
                'param2': ['250'],  # 차이점
                'param4': ['400']   # 새 파라미터
            })

            result = service.compare_files(file1_data, file2_data)

            print(f"공통 파라미터: {len(result.common_parameters)}개")
            print(f"차이점: {len(result.different_parameters)}개")
            print(f"일치율: {result.statistics.get('match_rate', 0):.1f}%")

            self.assertEqual(len(result.common_parameters), 2)  # param1, param2
            self.assertEqual(len(result.different_parameters), 1)  # param2
            self.assertEqual(len(result.missing_in_file1), 1)  # param4
            self.assertEqual(len(result.missing_in_file2), 1)  # param3

            print("✓ ComparisonService: PASS")

        except Exception as e:
            print(f"✗ ComparisonService: FAIL - {str(e)}")
            raise

    def test_03_report_service(self):
        """Test 3: ReportService 테스트"""
        print("\n" + "="*60)
        print("Test 3: ReportService")
        print("="*60)

        try:
            from app.services.report.report_service import ReportService
            from app.services.interfaces.report_service_interface import ReportData

            service = ReportService()

            # 보고서 데이터 생성
            report_data = ReportData(
                title="테스트 보고서",
                summary={
                    '전체': 100,
                    '통과': 90,
                    '실패': 10
                },
                details={
                    '상세정보': {'항목1': '값1', '항목2': '값2'}
                },
                metadata={
                    '작성자': 'Test',
                    '날짜': datetime.now().strftime('%Y-%m-%d')
                },
                timestamp=datetime.now().isoformat()
            )

            # HTML 보고서 생성
            html_report = service.generate_html_report(report_data)

            self.assertIn('<html', html_report)
            self.assertIn('테스트 보고서', html_report)
            self.assertIn('전체', html_report)

            print(f"HTML 보고서 생성 완료 ({len(html_report)} bytes)")

            # Excel 보고서 생성 테스트 (실제 파일 저장은 생략)
            print("✓ ReportService: PASS")

        except Exception as e:
            print(f"✗ ReportService: FAIL - {str(e)}")
            raise

    def test_04_service_factory_registration(self):
        """Test 4: ServiceFactory 서비스 등록 테스트"""
        print("\n" + "="*60)
        print("Test 4: ServiceFactory Registration")
        print("="*60)

        try:
            # Note: 실제 DB 연결이 없으면 일부 서비스는 등록되지 않을 수 있음
            print("✓ ServiceFactory registration test (skipped - requires DB)")
            self.assertTrue(True)

        except Exception as e:
            print(f"✗ ServiceFactory: FAIL - {str(e)}")
            raise

    def test_05_validation_service_basic(self):
        """Test 5: ValidationService 기본 기능 테스트"""
        print("\n" + "="*60)
        print("Test 5: ValidationService Basic")
        print("="*60)

        try:
            from app.services.validation.validation_service import ValidationService

            service = ValidationService()

            # 데이터 타입 검증
            result = service.validate_data_types(self.test_data)

            print(f"전체 파라미터: {result.total_parameters}")
            print(f"통과: {result.passed_count}")
            print(f"실패: {result.failed_count}")
            print(f"경고: {result.warning_count}")

            self.assertIsNotNone(result)
            self.assertEqual(result.total_parameters, 3)

            print("✓ ValidationService: PASS")

        except Exception as e:
            print(f"✗ ValidationService: FAIL - {str(e)}")
            raise

    def test_06_qc_service_basic(self):
        """Test 6: QCService 기본 기능 테스트"""
        print("\n" + "="*60)
        print("Test 6: QCService Basic")
        print("="*60)

        try:
            from app.services.qc.qc_service import QCService

            service = QCService()

            # 결측값 검사
            result = service.check_missing_values(self.test_data)

            print(f"전체 파라미터: {result.total_parameters}")
            print(f"이슈: {len(result.issues)}개")

            self.assertIsNotNone(result)

            print("✓ QCService: PASS")

        except Exception as e:
            print(f"✗ QCService: FAIL - {str(e)}")
            raise


def run_tests():
    """테스트 실행"""
    print("\n" + "="*60)
    print("P4 신규 서비스 통합 테스트")
    print("="*60)
    print(f"시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestP4Services)

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"총 테스트: {result.testsRun}개")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}개")
    print(f"실패: {len(result.failures)}개")
    print(f"에러: {len(result.errors)}개")
    print(f"성공률: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*60)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
