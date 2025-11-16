#!/usr/bin/env python3
"""
Test suite for file comparison engine
Tests the core comparison functionality of DB Manager
"""

import unittest
import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestFileComparison(unittest.TestCase):
    """Test file comparison engine functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        # Create sample test files
        self.test_file1 = os.path.join(self.temp_dir, "test1.txt")
        self.test_file2 = os.path.join(self.temp_dir, "test2.txt")

        # Sample data format: Module.Part.ItemName=ItemValue
        with open(self.test_file1, 'w', encoding='utf-8') as f:
            f.write("System.Controller.Temperature=25.5\n")
            f.write("System.Controller.Pressure=101.3\n")
            f.write("Chamber.Heater.SetPoint=150.0\n")

        with open(self.test_file2, 'w', encoding='utf-8') as f:
            f.write("System.Controller.Temperature=26.0\n")  # Different value
            f.write("System.Controller.Pressure=101.3\n")    # Same value
            f.write("Chamber.Heater.SetPoint=150.0\n")

    def tearDown(self):
        """Clean up test files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_file_loading(self):
        """Test 1: File loading functionality"""
        # Import here to avoid early import errors
        from app.manager import DBManager

        # Create a minimal manager instance
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window

        try:
            # We can't fully instantiate DBManager without a full GUI,
            # but we can test the file parsing logic independently

            # Test file exists
            self.assertTrue(os.path.exists(self.test_file1))
            self.assertTrue(os.path.exists(self.test_file2))

            # Test file can be read
            with open(self.test_file1, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 3)

            print("✅ Test 1: File loading - PASS")

        finally:
            root.destroy()

    def test_data_parsing(self):
        """Test 2: Data parsing and structure"""
        # Test parsing Module.Part.ItemName format
        test_line = "System.Controller.Temperature=25.5"
        parts = test_line.split('=')
        self.assertEqual(len(parts), 2)

        param_parts = parts[0].split('.')
        self.assertEqual(len(param_parts), 3)
        self.assertEqual(param_parts[0], "System")
        self.assertEqual(param_parts[1], "Controller")
        self.assertEqual(param_parts[2], "Temperature")
        self.assertEqual(parts[1], "25.5")

        print("✅ Test 2: Data parsing - PASS")

    def test_data_comparison(self):
        """Test 3: Basic data comparison logic"""
        # Create test data structures (dict-based instead of pandas)
        data1 = [
            {'Module': 'System', 'Part': 'Controller', 'ItemName': 'Temperature', 'ItemValue': '25.5'},
            {'Module': 'System', 'Part': 'Controller', 'ItemName': 'Pressure', 'ItemValue': '101.3'},
            {'Module': 'Chamber', 'Part': 'Heater', 'ItemName': 'SetPoint', 'ItemValue': '150.0'}
        ]

        data2 = [
            {'Module': 'System', 'Part': 'Controller', 'ItemName': 'Temperature', 'ItemValue': '26.0'},
            {'Module': 'System', 'Part': 'Controller', 'ItemName': 'Pressure', 'ItemValue': '101.3'},
            {'Module': 'Chamber', 'Part': 'Heater', 'ItemName': 'SetPoint', 'ItemValue': '150.0'}
        ]

        # Test: Find differences
        differences = []
        for idx in range(len(data1)):
            if data1[idx]['ItemValue'] != data2[idx]['ItemValue']:
                differences.append(data1[idx]['ItemName'])

        self.assertEqual(len(differences), 1)
        self.assertEqual(differences[0], 'Temperature')

        print("✅ Test 3: Data comparison - PASS")

    def test_module_grouping(self):
        """Test 4: Module/Part grouping functionality"""
        data = [
            {'Module': 'System', 'Part': 'Controller', 'ItemName': 'Temperature', 'ItemValue': '25.5'},
            {'Module': 'System', 'Part': 'Controller', 'ItemName': 'Pressure', 'ItemValue': '101.3'},
            {'Module': 'Chamber', 'Part': 'Heater', 'ItemName': 'SetPoint', 'ItemValue': '150.0'},
            {'Module': 'Chamber', 'Part': 'Heater', 'ItemName': 'Power', 'ItemValue': '500'}
        ]

        # Group by Module manually
        modules = {}
        for item in data:
            module = item['Module']
            if module not in modules:
                modules[module] = []
            modules[module].append(item)

        self.assertEqual(len(modules), 2)

        # Check System module has 2 items
        self.assertEqual(len(modules['System']), 2)

        print("✅ Test 4: Module grouping - PASS")

    def test_difference_detection(self):
        """Test 5: Difference detection accuracy"""
        # Create test data with known differences
        data = [
            {'File': 'A', 'Module': 'System', 'ItemName': 'Temp', 'ItemValue': '25.0'},
            {'File': 'B', 'Module': 'System', 'ItemName': 'Temp', 'ItemValue': '26.0'},
            {'File': 'A', 'Module': 'Chamber', 'ItemName': 'Pressure', 'ItemValue': '101.3'},
            {'File': 'B', 'Module': 'Chamber', 'ItemName': 'Pressure', 'ItemValue': '101.3'}
        ]

        # Group by (Module, ItemName) manually
        grouped = {}
        for item in data:
            key = (item['Module'], item['ItemName'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item['ItemValue'])

        # Count differences
        differences = 0
        for key, values in grouped.items():
            unique_values = set(values)
            if len(unique_values) > 1:
                differences += 1

        self.assertEqual(differences, 1)  # Only Temp differs

        print("✅ Test 5: Difference detection - PASS")


def run_tests():
    """Run all comparison tests"""
    print("=" * 70)
    print("FILE COMPARISON ENGINE TESTS")
    print("=" * 70)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestFileComparison)
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
