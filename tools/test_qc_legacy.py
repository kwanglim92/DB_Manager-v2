#!/usr/bin/env python3
"""
Test suite for QC inspection (legacy)
Tests QC validation and checklist functionality
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestQCInspection(unittest.TestCase):
    """Test QC inspection functionality"""

    def setUp(self):
        """Set up test data"""
        # Sample equipment data (list of dicts instead of pandas)
        self.test_data = [
            {'Module': 'System', 'Part': 'Controller', 'ItemName': 'Temperature', 'ItemValue': '25.5'},
            {'Module': 'System', 'Part': 'Controller', 'ItemName': 'Pressure', 'ItemValue': '101.3'},
            {'Module': 'Chamber', 'Part': 'Heater', 'ItemName': 'SetPoint', 'ItemValue': '150.0'},
            {'Module': 'Chamber', 'Part': 'Heater', 'ItemName': 'Power', 'ItemValue': '500'},
            {'Module': 'Safety', 'Part': 'Interlock', 'ItemName': 'EmergencyStop', 'ItemValue': 'Enabled'}
        ]

        # Default DB values for comparison
        self.default_values = {
            'System.Controller.Temperature': {'default': '25.0', 'min': '20.0', 'max': '30.0'},
            'System.Controller.Pressure': {'default': '101.3', 'min': '90.0', 'max': '110.0'},
            'Chamber.Heater.SetPoint': {'default': '150.0', 'min': '100.0', 'max': '200.0'},
            'Safety.Interlock.EmergencyStop': {'default': 'Enabled', 'expected': 'Enabled'}
        }

    def test_data_structure(self):
        """Test 1: QC data structure validation"""
        # Verify test data has required keys
        required_keys = ['Module', 'Part', 'ItemName', 'ItemValue']
        for item in self.test_data:
            for key in required_keys:
                self.assertIn(key, item)

        # Verify data count
        self.assertEqual(len(self.test_data), 5)

        print("✅ Test 1: Data structure validation - PASS")

    def test_spec_validation(self):
        """Test 2: Spec range validation"""
        # Test temperature is within spec
        temp_item = [item for item in self.test_data if item['ItemName'] == 'Temperature'][0]
        temp_value = float(temp_item['ItemValue'])
        temp_spec = self.default_values['System.Controller.Temperature']

        self.assertGreaterEqual(temp_value, float(temp_spec['min']))
        self.assertLessEqual(temp_value, float(temp_spec['max']))

        print("✅ Test 2: Spec range validation - PASS")

    def test_critical_parameter_check(self):
        """Test 3: Critical parameter validation (Safety)"""
        # Safety parameters must match exactly
        emergency_item = [item for item in self.test_data if item['ItemName'] == 'EmergencyStop'][0]
        emergency_stop = emergency_item['ItemValue']
        expected = self.default_values['Safety.Interlock.EmergencyStop']['expected']

        self.assertEqual(emergency_stop, expected)

        print("✅ Test 3: Critical parameter check - PASS")

    def test_value_comparison(self):
        """Test 4: Default value comparison"""
        issues = []

        # Check each parameter
        for item in self.test_data:
            param_name = f"{item['Module']}.{item['Part']}.{item['ItemName']}"

            if param_name in self.default_values:
                spec = self.default_values[param_name]
                value = item['ItemValue']

                # Check if value matches default
                if value != spec['default']:
                    issues.append({
                        'parameter': param_name,
                        'current': value,
                        'expected': spec['default']
                    })

        # Temperature is 25.5 vs default 25.0, so we should have 1 issue
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['parameter'], 'System.Controller.Temperature')

        print("✅ Test 4: Value comparison - PASS")

    def test_missing_parameter_detection(self):
        """Test 5: Missing critical parameter detection"""
        # Check if all required parameters are present
        required_params = [
            'System.Controller.Temperature',
            'System.Controller.Pressure',
            'Safety.Interlock.EmergencyStop'
        ]

        present_params = set()
        for item in self.test_data:
            param_name = f"{item['Module']}.{item['Part']}.{item['ItemName']}"
            present_params.add(param_name)

        missing = []
        for required in required_params:
            if required not in present_params:
                missing.append(required)

        self.assertEqual(len(missing), 0)  # All required params present

        print("✅ Test 5: Missing parameter detection - PASS")

    def test_qc_pass_fail_logic(self):
        """Test 6: QC pass/fail determination"""
        # Simulate QC check
        critical_failures = 0
        warnings = 0

        for item in self.test_data:
            param_name = f"{item['Module']}.{item['Part']}.{item['ItemName']}"

            if param_name in self.default_values:
                spec = self.default_values[param_name]
                value = item['ItemValue']

                # Critical: Safety parameters
                if item['Module'] == 'Safety':
                    if 'expected' in spec and value != spec['expected']:
                        critical_failures += 1

                # Warning: Values outside spec
                elif 'min' in spec and 'max' in spec:
                    try:
                        val_float = float(value)
                        if val_float < float(spec['min']) or val_float > float(spec['max']):
                            critical_failures += 1
                    except ValueError:
                        pass

                # Info: Value differs from default
                if value != spec['default']:
                    warnings += 1

        # Determine QC result
        qc_pass = critical_failures == 0

        self.assertTrue(qc_pass)  # Should pass (no critical failures)
        self.assertEqual(critical_failures, 0)
        self.assertEqual(warnings, 1)  # Temperature differs from default

        print("✅ Test 6: QC pass/fail logic - PASS")


def run_tests():
    """Run all QC inspection tests"""
    print("=" * 70)
    print("QC INSPECTION TESTS (LEGACY)")
    print("=" * 70)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestQCInspection)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
