#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 통합 테스트 - 코드 품질 개선 프로젝트 검증
P0-P4 모든 개선 사항이 함께 작동하는지 검증

테스트 범위:
1. 서비스 레이어 통합 (9개 서비스)
2. Phase 1.5/2 DB 스키마 호환성
3. 로깅 표준화 검증
4. 예외 처리 개선 검증
5. 헬퍼 메서드 재사용성
6. 전체 시스템 안정성
"""

import sys
import os
import unittest
import logging
from io import StringIO
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

# 테스트 결과 통계
class TestStats:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.skipped = 0
        self.start_time = None
        self.end_time = None

    def duration(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

stats = TestStats()


class Test1_ServiceLayerIntegration(unittest.TestCase):
    """서비스 레이어 통합 테스트"""

    def test_01_service_factory_initialization(self):
        """ServiceFactory 초기화 및 9개 서비스 등록 확인"""
        try:
            from app.services.service_factory import ServiceFactory

            factory = ServiceFactory()

            # 9개 서비스 모두 등록되었는지 확인
            services = [
                'equipment_service',
                'checklist_service',
                'cache_service',
                'logging_service',
                'parameter_service',
                'validation_service',
                'qc_service',
                'comparison_service',
                'motherdb_service'
            ]

            for service_name in services:
                getter = f'get_{service_name}'
                self.assertTrue(
                    hasattr(factory, getter),
                    f"ServiceFactory should have {getter} method"
                )

            print("✓ ServiceFactory: 9개 서비스 모두 등록됨")

        except ImportError as e:
            self.skipTest(f"서비스 레이어 모듈 미설치: {e}")

    def test_02_service_dependencies(self):
        """서비스 간 의존성 주입 확인"""
        try:
            from app.services.service_factory import ServiceFactory

            factory = ServiceFactory()

            # QCService는 ValidationService와 ChecklistService에 의존
            qc_service = factory.get_qc_service()

            # 서비스가 정상적으로 생성되었는지 확인
            self.assertIsNotNone(qc_service, "QCService should be created")

            print("✓ 서비스 의존성: 정상 주입 확인")

        except ImportError as e:
            self.skipTest(f"서비스 레이어 모듈 미설치: {e}")

    def test_03_singleton_pattern(self):
        """Singleton 패턴 적용 확인 (중복 인스턴스 방지)"""
        try:
            from app.services.service_factory import ServiceFactory

            factory1 = ServiceFactory()
            factory2 = ServiceFactory()

            # 같은 인스턴스를 반환하는지 확인
            cache1 = factory1.get_cache_service()
            cache2 = factory2.get_cache_service()

            self.assertIs(cache1, cache2, "CacheService should be singleton")

            print("✓ Singleton 패턴: 중복 인스턴스 방지 확인")

        except ImportError as e:
            self.skipTest(f"서비스 레이어 모듈 미설치: {e}")


class Test2_DatabaseSchemaCompatibility(unittest.TestCase):
    """Phase 1.5/2 DB 스키마 호환성 테스트"""

    def test_01_schema_deprecation(self):
        """db_schema.py 폐기 및 app.schema.py 사용 확인"""
        try:
            # db_schema.py는 이제 래퍼여야 함
            import db_schema
            from app import schema

            # 같은 클래스를 참조하는지 확인
            self.assertIs(
                db_schema.DBSchema,
                schema.DBSchema,
                "db_schema.DBSchema should re-export app.schema.DBSchema"
            )

            print("✓ DB 스키마: db_schema.py → app.schema.py 마이그레이션 확인")

        except ImportError as e:
            self.fail(f"DB 스키마 import 실패: {e}")

    def test_02_phase15_tables(self):
        """Phase 1.5 테이블 존재 확인"""
        try:
            from app.schema import DBSchema
            import tempfile
            import os

            # 임시 DB 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
                temp_db = f.name

            try:
                db = DBSchema(temp_db)

                with db.get_connection() as conn:
                    cursor = conn.cursor()

                    # Phase 1.5 테이블 확인
                    tables = [
                        'Equipment_Models',
                        'Equipment_Configurations'
                    ]

                    for table in tables:
                        cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                            (table,)
                        )
                        result = cursor.fetchone()
                        self.assertIsNotNone(
                            result,
                            f"Phase 1.5 table '{table}' should exist"
                        )

                print("✓ Phase 1.5: Equipment_Models, Equipment_Configurations 테이블 확인")

            finally:
                if os.path.exists(temp_db):
                    os.remove(temp_db)

        except ImportError as e:
            self.skipTest(f"DB 스키마 모듈 미설치: {e}")

    def test_03_phase2_tables(self):
        """Phase 2 테이블 존재 확인"""
        try:
            from app.schema import DBSchema
            import tempfile
            import os

            # 임시 DB 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
                temp_db = f.name

            try:
                db = DBSchema(temp_db)

                with db.get_connection() as conn:
                    cursor = conn.cursor()

                    # Phase 2 테이블 확인
                    tables = [
                        'Shipped_Equipment',
                        'Shipped_Equipment_Parameters'
                    ]

                    for table in tables:
                        cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                            (table,)
                        )
                        result = cursor.fetchone()
                        self.assertIsNotNone(
                            result,
                            f"Phase 2 table '{table}' should exist"
                        )

                print("✓ Phase 2: Shipped_Equipment 테이블 확인")

            finally:
                if os.path.exists(temp_db):
                    os.remove(temp_db)

        except ImportError as e:
            self.skipTest(f"DB 스키마 모듈 미설치: {e}")


class Test3_LoggingStandardization(unittest.TestCase):
    """로깅 표준화 검증"""

    def test_01_no_print_in_manager(self):
        """manager.py에 print() 문이 없는지 확인"""
        manager_path = os.path.join(project_root, 'src', 'app', 'manager.py')

        if not os.path.exists(manager_path):
            self.skipTest(f"manager.py not found: {manager_path}")

        with open(manager_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # print( 패턴 찾기 (주석 제외)
        lines = content.split('\n')
        print_lines = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 주석이 아니고 print( 가 있으면
            if not stripped.startswith('#') and 'print(' in line:
                # 단, logging.debug(f"print(...)")  같은 경우는 제외
                if 'logging' not in line and '"print(' not in line and "'print(" not in line:
                    print_lines.append((i, line))

        # 허용된 print 문 (최대 3개)
        self.assertLessEqual(
            len(print_lines),
            3,
            f"manager.py should have <= 3 print statements, found {len(print_lines)}: {print_lines[:5]}"
        )

        print(f"✓ 로깅 표준화: print() 사용 최소화 ({len(print_lines)}/3)")

    def test_02_logging_import(self):
        """manager.py가 logging 모듈을 import하는지 확인"""
        manager_path = os.path.join(project_root, 'src', 'app', 'manager.py')

        if not os.path.exists(manager_path):
            self.skipTest(f"manager.py not found: {manager_path}")

        with open(manager_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('import logging', content, "manager.py should import logging")

        # logging.error, logging.warning, logging.info 사용 확인
        self.assertIn('logging.error', content, "manager.py should use logging.error")

        print("✓ 로깅 표준화: logging 모듈 사용 확인")


class Test4_ExceptionHandling(unittest.TestCase):
    """예외 처리 개선 검증"""

    def test_01_no_bare_except_in_manager(self):
        """manager.py에 bare except가 없는지 확인"""
        manager_path = os.path.join(project_root, 'src', 'app', 'manager.py')

        if not os.path.exists(manager_path):
            self.skipTest(f"manager.py not found: {manager_path}")

        with open(manager_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        bare_except_lines = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # "except:" 패턴 찾기 (except Exception은 OK)
            if stripped.startswith('except:'):
                bare_except_lines.append((i, line))

        self.assertEqual(
            len(bare_except_lines),
            0,
            f"manager.py should have no bare except clauses, found {len(bare_except_lines)}: {bare_except_lines}"
        )

        print("✓ 예외 처리: bare except 0개 (100% 제거)")

    def test_02_specific_exceptions(self):
        """manager.py가 구체적인 예외 타입을 사용하는지 확인"""
        manager_path = os.path.join(project_root, 'src', 'app', 'manager.py')

        if not os.path.exists(manager_path):
            self.skipTest(f"manager.py not found: {manager_path}")

        with open(manager_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 구체적인 예외 타입 사용 확인
        exceptions = ['ValueError', 'TypeError', 'KeyError', 'FileNotFoundError', 'IOError']

        found_count = 0
        for exc in exceptions:
            if f'except {exc}' in content or f'except ({exc}' in content:
                found_count += 1

        self.assertGreater(
            found_count,
            0,
            "manager.py should use specific exception types"
        )

        print(f"✓ 예외 처리: 구체적 예외 타입 사용 ({found_count}종)")


class Test5_HelperMethodReusability(unittest.TestCase):
    """헬퍼 메서드 재사용성 테스트"""

    def test_01_helper_methods_exist(self):
        """manager.py에 헬퍼 메서드가 추가되었는지 확인"""
        manager_path = os.path.join(project_root, 'src', 'app', 'manager.py')

        if not os.path.exists(manager_path):
            self.skipTest(f"manager.py not found: {manager_path}")

        with open(manager_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # P1에서 추가된 헬퍼 메서드들
        helper_methods = [
            '_show_error',
            '_show_warning',
            '_show_info',
            '_require_maintenance_mode',
            '_require_equipment_selection',
            '_confirm_action',
            '_load_and_parse_comparison_files',
            '_analyze_parameter_statistics'
        ]

        found_methods = []
        for method in helper_methods:
            if f'def {method}(' in content:
                found_methods.append(method)

        self.assertGreater(
            len(found_methods),
            10,
            f"manager.py should have >= 10 helper methods, found {len(found_methods)}"
        )

        print(f"✓ 헬퍼 메서드: {len(found_methods)}개 추가됨")

    def test_02_method_size_reduction(self):
        """주요 메서드 크기가 줄어들었는지 확인"""
        manager_path = os.path.join(project_root, 'src', 'app', 'manager.py')

        if not os.path.exists(manager_path):
            self.skipTest(f"manager.py not found: {manager_path}")

        with open(manager_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 메서드별 라인 수 계산
        method_sizes = {}
        current_method = None
        current_size = 0
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # 메서드 시작
            if stripped.startswith('def ') and '(' in stripped:
                if current_method:
                    method_sizes[current_method] = current_size

                current_method = stripped.split('(')[0].replace('def ', '')
                current_size = 1
                indent_level = len(line) - len(line.lstrip())

            # 메서드 내부
            elif current_method and stripped:
                current_line_indent = len(line) - len(line.lstrip())
                # 같은 레벨이거나 더 깊은 들여쓰기면 메서드 내부
                if current_line_indent > indent_level:
                    current_size += 1
                # 들여쓰기가 같거나 작으면 메서드 종료
                elif current_line_indent <= indent_level and stripped.startswith('def '):
                    method_sizes[current_method] = current_size
                    current_method = stripped.split('(')[0].replace('def ', '')
                    current_size = 1
                    indent_level = current_line_indent

        if current_method:
            method_sizes[current_method] = current_size

        # 가장 큰 메서드 찾기
        if method_sizes:
            max_size = max(method_sizes.values())
            avg_size = sum(method_sizes.values()) / len(method_sizes)

            # 최대 메서드 크기가 200줄 이하인지 확인 (원래 278줄)
            self.assertLess(
                max_size,
                200,
                f"Largest method should be < 200 lines (was 278), found {max_size}"
            )

            print(f"✓ 메서드 크기: 최대 {max_size}줄, 평균 {avg_size:.1f}줄")


class Test6_SystemStability(unittest.TestCase):
    """전체 시스템 안정성 테스트"""

    def test_01_main_import(self):
        """main.py가 정상적으로 import되는지 확인"""
        try:
            # main.py import 시도
            sys.path.insert(0, os.path.join(project_root, 'src'))

            # DBManager 클래스만 import (GUI 실행 X)
            from app.manager import DBManager

            self.assertTrue(True, "main.py imports successfully")
            print("✓ 시스템 안정성: main.py import 성공")

        except Exception as e:
            self.fail(f"main.py import failed: {e}")

    def test_02_schema_creation(self):
        """DB 스키마가 정상적으로 생성되는지 확인"""
        try:
            from app.schema import DBSchema
            import tempfile
            import os

            # 임시 DB 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite') as f:
                temp_db = f.name

            try:
                db = DBSchema(temp_db)

                with db.get_connection() as conn:
                    cursor = conn.cursor()

                    # 테이블 개수 확인 (Phase 0 + Phase 1 + Phase 1.5 + Phase 2)
                    cursor.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                    )
                    table_count = cursor.fetchone()[0]

                    # 최소 10개 이상의 테이블이 있어야 함
                    self.assertGreater(
                        table_count,
                        10,
                        f"Database should have > 10 tables, found {table_count}"
                    )

                print(f"✓ 시스템 안정성: DB 스키마 생성 성공 ({table_count}개 테이블)")

            finally:
                if os.path.exists(temp_db):
                    os.remove(temp_db)

        except ImportError as e:
            self.skipTest(f"DB 스키마 모듈 미설치: {e}")

    def test_03_all_imports(self):
        """주요 모듈들이 모두 import되는지 확인"""
        try:
            # 핵심 모듈 import
            from app.schema import DBSchema
            from app.manager import DBManager
            from app.services.service_factory import ServiceFactory

            # QC 시스템
            from app.qc import ChecklistValidator

            # 서비스들
            from app.services.equipment.equipment_service import EquipmentService
            from app.services.checklist.checklist_service import ChecklistService

            print("✓ 시스템 안정성: 모든 핵심 모듈 import 성공")

        except ImportError as e:
            self.fail(f"Module import failed: {e}")


def run_tests():
    """모든 테스트 실행"""
    global stats

    print("=" * 80)
    print("최종 통합 테스트 - 코드 품질 개선 프로젝트 검증")
    print("=" * 80)
    print()

    stats.start_time = datetime.now()

    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 모든 테스트 클래스 추가
    test_classes = [
        Test1_ServiceLayerIntegration,
        Test2_DatabaseSchemaCompatibility,
        Test3_LoggingStandardization,
        Test4_ExceptionHandling,
        Test5_HelperMethodReusability,
        Test6_SystemStability
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    stats.end_time = datetime.now()
    stats.total = result.testsRun
    stats.passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    stats.failed = len(result.failures)
    stats.errors = len(result.errors)
    stats.skipped = len(result.skipped)

    # 결과 요약
    print()
    print("=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    print(f"총 테스트: {stats.total}")
    print(f"통과: {stats.passed} (✓)")
    print(f"실패: {stats.failed} (✗)")
    print(f"오류: {stats.errors} (⚠)")
    print(f"건너뜀: {stats.skipped} (○)")
    print(f"실행 시간: {stats.duration():.2f}초")
    print()

    if stats.passed == stats.total:
        print("🎉 모든 테스트 통과!")
        return 0
    else:
        pass_rate = (stats.passed / stats.total * 100) if stats.total > 0 else 0
        print(f"⚠️  일부 테스트 실패 (통과율: {pass_rate:.1f}%)")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
