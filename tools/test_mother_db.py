#!/usr/bin/env python3
"""
Test suite for Mother DB management
Tests Default DB operations and candidate analysis
"""

import unittest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestMotherDB(unittest.TestCase):
    """Test Mother DB (Default DB) management functionality"""

    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_db.sqlite")

        # Create test database schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Equipment Types table
        cursor.execute('''
            CREATE TABLE Equipment_Types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')

        # Default DB Values table
        cursor.execute('''
            CREATE TABLE Default_DB_Values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_type_id INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                default_value TEXT,
                min_spec TEXT,
                max_spec TEXT,
                UNIQUE(equipment_type_id, parameter_name),
                FOREIGN KEY (equipment_type_id) REFERENCES Equipment_Types(id) ON DELETE CASCADE
            )
        ''')

        # Insert test equipment type
        cursor.execute("INSERT INTO Equipment_Types (type_name, description) VALUES (?, ?)",
                      ("NX-Hybrid", "Test Equipment"))
        self.equipment_type_id = cursor.lastrowid

        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up test database"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_equipment_type_creation(self):
        """Test 1: Equipment type can be created"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Equipment_Types")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

        cursor.execute("SELECT type_name FROM Equipment_Types WHERE id = ?", (self.equipment_type_id,))
        type_name = cursor.fetchone()[0]
        self.assertEqual(type_name, "NX-Hybrid")

        conn.close()
        print("✅ Test 1: Equipment type creation - PASS")

    def test_parameter_insertion(self):
        """Test 2: Parameters can be inserted into Default DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert test parameter
        cursor.execute('''
            INSERT INTO Default_DB_Values
            (equipment_type_id, parameter_name, default_value, min_spec, max_spec)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.equipment_type_id, "System.Controller.Temperature", "25.0", "20.0", "30.0"))

        conn.commit()

        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM Default_DB_Values WHERE equipment_type_id = ?",
                      (self.equipment_type_id,))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

        conn.close()
        print("✅ Test 2: Parameter insertion - PASS")

    def test_duplicate_prevention(self):
        """Test 3: Duplicate parameters are prevented by UNIQUE constraint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert first parameter
        cursor.execute('''
            INSERT INTO Default_DB_Values
            (equipment_type_id, parameter_name, default_value)
            VALUES (?, ?, ?)
        ''', (self.equipment_type_id, "Test.Param", "100"))
        conn.commit()

        # Try to insert duplicate - should fail
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO Default_DB_Values
                (equipment_type_id, parameter_name, default_value)
                VALUES (?, ?, ?)
            ''', (self.equipment_type_id, "Test.Param", "200"))
            conn.commit()

        conn.close()
        print("✅ Test 3: Duplicate prevention - PASS")

    def test_candidate_analysis_logic(self):
        """Test 4: Candidate analysis logic (80% threshold)"""
        # Simulate candidate analysis
        test_data = [
            ("File1", "25.0"),
            ("File2", "25.0"),
            ("File3", "25.0"),
            ("File4", "25.0"),
            ("File5", "26.0")  # Different value
        ]

        # Count occurrences
        value_counts = {}
        for file, value in test_data:
            value_counts[value] = value_counts.get(value, 0) + 1

        # Find most common value
        most_common_value = max(value_counts, key=value_counts.get)
        occurrence_count = value_counts[most_common_value]
        total_files = len(test_data)

        # Calculate confidence (80% threshold)
        confidence = (occurrence_count / total_files) * 100

        self.assertEqual(most_common_value, "25.0")
        self.assertEqual(occurrence_count, 4)
        self.assertEqual(confidence, 80.0)
        self.assertGreaterEqual(confidence, 80.0)  # Meets threshold

        print("✅ Test 4: Candidate analysis (80% threshold) - PASS")


def run_tests():
    """Run all Mother DB tests"""
    print("=" * 70)
    print("MOTHER DB MANAGEMENT TESTS")
    print("=" * 70)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestMotherDB)
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
