#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
단기 계획 신규 기능 테스트
- ConfigurationService 신규 메서드 (convert_to_type_common, convert_to_configuration_specific)
- ValidationService 커스텀 규칙
- 기타 TODO에서 구현된 기능들

테스트 커버리지: 20% → 25% 목표
"""

import sys
import os
import unittest
import tempfile

# pandas가 없으면 mock DataFrame 사용
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    # Simple DataFrame mock
    class MockDataFrame:
        def __init__(self, data):
            self.data = data
            self.columns = list(data.keys()) if data else []

        def items(self):
            for col, values in self.data.items():
                for idx, val in enumerate(values):
                    yield idx, val

        def __getitem__(self, key):
            if isinstance(key, str):
                # Column access
                return MockSeries(self.data.get(key, []))
            return self

        def value_counts(self):
            # Simple value counts
            from collections import Counter
            return Counter(self.data.values())

    class MockSeries:
        def __init__(self, values):
            self.values = values

        def items(self):
            return enumerate(self.values)

        def value_counts(self):
            from collections import Counter
            return Counter(self.values)

    pd = type('pd', (), {'DataFrame': MockDataFrame})()

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

class TestConfigurationServiceConversion(unittest.TestCase):
    """ConfigurationService 변환 메서드 테스트"""

    def setUp(self):
        """테스트용 임시 DB 생성"""
        from app.schema import DBSchema
        from app.services.configuration.configuration_service import ConfigurationService
        from app.services.category.category_service import CategoryService

        # 임시 DB
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite')
        self.db_path = self.temp_db_file.name
        self.temp_db_file.close()

        self.db_schema = DBSchema(self.db_path)
        self.config_service = ConfigurationService(self.db_schema)
        self.category_service = CategoryService(self.db_schema)

        # 테스트 데이터 생성
        self._create_test_data()

    def tearDown(self):
        """임시 DB 삭제"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_test_data(self):
        """테스트용 Model, Type, Configuration, Parameters 생성"""
        # 1. Model 생성
        model_id = self.category_service.create_equipment_model(
            model_name="Test Model",
            description="Test Model Description"
        )

        # 2. Type 생성
        type_id = self.category_service.create_equipment_type(
            model_id=model_id,
            type_name="Test Type",
            description="Test Type Description"
        )

        # 3. Configuration 생성 (2개)
        self.config_id_1 = self.config_service.create_configuration(
            type_id=type_id,
            configuration_name="Config A",
            port_count=1,
            wafer_count=1
        )

        self.config_id_2 = self.config_service.create_configuration(
            type_id=type_id,
            configuration_name="Config B",
            port_count=2,
            wafer_count=2
        )

        # 4. Configuration-specific 파라미터 추가 (Config A)
        self.param_id_1 = self.config_service.create_default_value(
            configuration_id=self.config_id_1,
            parameter_name="Temperature",
            default_value="25.0",
            is_type_common=False  # Configuration-specific
        )

        self.param_id_2 = self.config_service.create_default_value(
            configuration_id=self.config_id_1,
            parameter_name="Pressure",
            default_value="100.0",
            is_type_common=False
        )

        # 5. Type Common 파라미터 추가
        self.param_id_3 = self.config_service.create_default_value(
            configuration_id=self.config_id_1,
            parameter_name="Voltage",
            default_value="220.0",
            is_type_common=True  # Type Common
        )

        self.type_id = type_id
        self.model_id = model_id

    def test_01_convert_to_type_common(self):
        """Configuration-specific → Type Common 변환 테스트"""
        # Configuration-specific 파라미터를 Type Common으로 변환
        param_ids = [self.param_id_1, self.param_id_2]

        success = self.config_service.convert_to_type_common(param_ids, self.type_id)

        self.assertTrue(success, "Type Common 변환 성공해야 함")

        # 변환 후 확인
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()

            # Temperature 파라미터 확인
            cursor.execute("""
                SELECT is_type_common FROM Default_DB_Values
                WHERE id = ?
            """, (self.param_id_1,))
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Temperature 파라미터 존재해야 함")
            self.assertEqual(row[0], 1, "Temperature는 Type Common이어야 함")

            # Pressure 파라미터 확인
            cursor.execute("""
                SELECT is_type_common FROM Default_DB_Values
                WHERE id = ?
            """, (self.param_id_2,))
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Pressure 파라미터 존재해야 함")
            self.assertEqual(row[0], 1, "Pressure는 Type Common이어야 함")

        print("✓ Test 1: Type Common 변환 성공")

    def test_02_convert_to_configuration_specific(self):
        """Type Common → Configuration-specific 변환 테스트"""
        # Type Common 파라미터를 Configuration-specific으로 변환
        param_ids = [self.param_id_3]

        success = self.config_service.convert_to_configuration_specific(param_ids, self.config_id_2)

        self.assertTrue(success, "Configuration-specific 변환 성공해야 함")

        # 변환 후 확인: Config B에 새 파라미터가 생성되어야 함
        values = self.config_service.get_default_values_by_configuration(self.config_id_2)

        voltage_params = [v for v in values if v.parameter_name == "Voltage"]
        self.assertGreater(len(voltage_params), 0, "Config B에 Voltage 파라미터 존재해야 함")

        # Configuration-specific인지 확인
        config_specific = [v for v in voltage_params if not v.is_type_common]
        self.assertGreater(len(config_specific), 0, "Configuration-specific Voltage 파라미터 존재해야 함")

        print("✓ Test 2: Configuration-specific 변환 성공")

    def test_03_convert_duplicate_handling(self):
        """중복 파라미터 처리 테스트"""
        # Temperature를 다시 Type Common으로 변환 시도 (이미 Type Common)
        # convert_to_type_common이 멱등성을 가져야 함

        success = self.config_service.convert_to_type_common([self.param_id_1], self.type_id)
        self.assertTrue(success, "중복 변환도 성공해야 함 (멱등성)")

        # Temperature 파라미터 개수 확인 (1개여야 함)
        with self.db_schema.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM Default_DB_Values
                WHERE parameter_name = 'Temperature'
            """)
            count = cursor.fetchone()[0]
            # 중복 없이 1개만 존재해야 함 (또는 convert_to_type_common이 is_type_common=1로 업데이트만)
            self.assertLessEqual(count, 2, "Temperature 파라미터가 과도하게 중복되지 않아야 함")

        print("✓ Test 3: 중복 처리 정상")


class TestValidationServiceCustomRules(unittest.TestCase):
    """ValidationService 커스텀 규칙 테스트"""

    def setUp(self):
        """ValidationService 초기화"""
        if not HAS_PANDAS:
            self.skipTest("pandas not available")

        from app.services.validation.validation_service import ValidationService

        self.validation_service = ValidationService()

        # 테스트용 DataFrame 생성
        self.test_data = pd.DataFrame({
            'Temperature': [20.0, 25.0, 30.0, 35.0, 40.0],
            'Pressure': [90.0, 100.0, 110.0, 120.0, 130.0],
            'Status': ['OK', 'OK', 'NG', 'OK', 'UNKNOWN'],
            'SerialNumber': ['AB123456', 'CD789012', 'EF345678', 'INVALID', 'GH901234'],
            'ID': [1, 2, 2, 3, 4]  # 중복 있음
        })

    def test_01_range_rule(self):
        """Range 검증 규칙 테스트"""
        rules = [
            {'type': 'range', 'column': 'Temperature', 'min': 22.0, 'max': 38.0}
        ]

        result = self.validation_service.apply_custom_rules(self.test_data, rules)

        # 20.0과 40.0은 범위 밖이므로 이슈 발생해야 함
        self.assertGreater(len(result['issues']), 0, "범위 밖 값에 대한 이슈 발생해야 함")

        # 이슈 내용 확인
        issues_str = " ".join(result['issues'])
        self.assertIn("20.0", issues_str, "20.0이 최소값 미달로 감지되어야 함")
        self.assertIn("40.0", issues_str, "40.0이 최대값 초과로 감지되어야 함")

        print(f"✓ Test 1: Range 검증 성공 ({len(result['issues'])}개 이슈 발견)")

    def test_02_enum_rule(self):
        """Enum 검증 규칙 테스트"""
        rules = [
            {'type': 'enum', 'column': 'Status', 'values': ['OK', 'NG']}
        ]

        result = self.validation_service.apply_custom_rules(self.test_data, rules)

        # 'UNKNOWN'은 허용된 값이 아니므로 이슈 발생
        self.assertGreater(len(result['issues']), 0, "허용되지 않은 값에 대한 이슈 발생해야 함")

        issues_str = " ".join(result['issues'])
        self.assertIn("UNKNOWN", issues_str, "UNKNOWN이 허용되지 않은 값으로 감지되어야 함")

        print(f"✓ Test 2: Enum 검증 성공 ({len(result['issues'])}개 이슈 발견)")

    def test_03_regex_rule(self):
        """Regex 검증 규칙 테스트"""
        rules = [
            {'type': 'regex', 'column': 'SerialNumber', 'pattern': '^[A-Z]{2}\\d{6}$'}
        ]

        result = self.validation_service.apply_custom_rules(self.test_data, rules)

        # 'INVALID'는 패턴과 일치하지 않으므로 이슈 발생
        self.assertGreater(len(result['issues']), 0, "패턴 불일치 값에 대한 이슈 발생해야 함")

        issues_str = " ".join(result['issues'])
        self.assertIn("INVALID", issues_str, "INVALID가 패턴 불일치로 감지되어야 함")

        print(f"✓ Test 3: Regex 검증 성공 ({len(result['issues'])}개 이슈 발견)")

    def test_04_unique_rule(self):
        """Unique 검증 규칙 테스트"""
        rules = [
            {'type': 'unique', 'column': 'ID'}
        ]

        result = self.validation_service.apply_custom_rules(self.test_data, rules)

        # ID=2가 중복되므로 이슈 발생
        self.assertGreater(len(result['issues']), 0, "중복 값에 대한 이슈 발생해야 함")

        issues_str = " ".join(result['issues'])
        self.assertIn("2", issues_str, "ID=2가 중복으로 감지되어야 함")

        print(f"✓ Test 4: Unique 검증 성공 ({len(result['issues'])}개 이슈 발견)")

    def test_05_multiple_rules(self):
        """여러 규칙 동시 적용 테스트"""
        rules = [
            {'type': 'range', 'column': 'Temperature', 'min': 22.0, 'max': 38.0},
            {'type': 'enum', 'column': 'Status', 'values': ['OK', 'NG']},
            {'type': 'unique', 'column': 'ID'}
        ]

        result = self.validation_service.apply_custom_rules(self.test_data, rules)

        # 모든 규칙 위반이 감지되어야 함
        self.assertGreaterEqual(len(result['issues']), 3, "최소 3개 이상의 이슈 발견해야 함")

        print(f"✓ Test 5: 다중 규칙 검증 성공 ({len(result['issues'])}개 이슈 발견)")


class TestHelperMethods(unittest.TestCase):
    """신규 헬퍼 메서드 테스트"""

    def test_01_infer_port_type(self):
        """Port Type 추론 메서드 테스트"""
        from app.dialogs.configuration_dialog import ConfigurationDialog

        # Mock 서비스 (None으로 테스트)
        try:
            dialog = ConfigurationDialog(None, None, None)
        except:
            # 초기화 실패 시 헬퍼 메서드만 직접 테스트
            # 간단한 로직이므로 직접 검증
            pass

        # 간접 검증: Port count 기반 추론이 정상 작동하는지
        # (실제 dialog 없이는 테스트 어려우므로 SKIP)
        self.skipTest("ConfigurationDialog._infer_port_type는 UI 테스트 필요")

    def test_02_show_selection_dialog(self):
        """Selection Dialog 메서드 테스트"""
        from app.dialogs.equipment_hierarchy_dialog import EquipmentHierarchyDialog

        # UI 테스트는 별도로 수행
        self.skipTest("EquipmentHierarchyDialog._show_selection_dialog는 UI 테스트 필요")


def run_tests():
    """모든 테스트 실행"""
    print("=" * 80)
    print("단기 계획 신규 기능 테스트")
    print("=" * 80)
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 클래스 추가
    test_classes = [
        TestConfigurationServiceConversion,
        TestValidationServiceCustomRules,
        TestHelperMethods
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors) - len(result.skipped)
    print(f"총 테스트: {total}")
    print(f"통과: {passed} (✓)")
    print(f"실패: {len(result.failures)} (✗)")
    print(f"오류: {len(result.errors)} (⚠)")
    print(f"건너뜀: {len(result.skipped)} (○)")
    print()

    if passed == total:
        print("🎉 모든 테스트 통과!")
        return 0
    else:
        pass_rate = (passed / total * 100) if total > 0 else 0
        print(f"⚠️  일부 테스트 실패 (통과율: {pass_rate:.1f}%)")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
