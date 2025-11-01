#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 기능 테스트 스크립트

Phase 1에서 구현한 기능들을 테스트합니다:
1. Phase 1 데이터베이스 테이블 생성
2. 3단계 권한 시스템
3. Check list 관리 서비스
"""

import sys
import os

# 현재 파일의 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_database_schema():
    """Phase 1 데이터베이스 스키마 테스트"""
    print("\n[1] 데이터베이스 스키마 테스트")
    print("=" * 60)

    try:
        from app.schema import DBSchema
        db_schema = DBSchema()

        # 테이블 생성 확인
        import sqlite3
        conn = sqlite3.connect(db_schema.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]

        print(f"[통계] 총 {len(tables)}개 테이블:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count}개 레코드")

        # Phase 1 테이블 확인
        phase1_tables = [
            'QC_Checklist_Items',
            'Equipment_Checklist_Mapping',
            'Equipment_Checklist_Exceptions',
            'Checklist_Audit_Log'
        ]

        missing_tables = [t for t in phase1_tables if t not in tables]
        if missing_tables:
            print(f"[FAIL] 누락된 Phase 1 테이블: {missing_tables}")
            conn.close()
            return False
        else:
            print("[OK] Phase 1 테이블 모두 생성됨")

        conn.close()
        return True

    except Exception as e:
        print(f"[FAIL] 데이터베이스 스키마 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_access_control():
    """3단계 권한 시스템 테스트"""
    print("\n[검색] 2. 3단계 권한 시스템 테스트")
    print("=" * 60)

    try:
        # app.core의 __init__.py를 거치지 않고 직접 임포트
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "access_control",
            os.path.join(project_root, "src", "app", "core", "utils", "access_control.py")
        )
        access_control = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(access_control)
        AccessControl = access_control.AccessControl
        AccessLevel = access_control.AccessLevel

        # AccessControl 인스턴스 생성
        ac = AccessControl()

        # 초기 상태 (생산 엔지니어)
        print(f"[INFO] 초기 권한: {ac.get_current_level_name()}")
        assert ac.get_current_level() == AccessLevel.PRODUCTION
        assert not ac.can_access_qc()
        assert not ac.can_access_default_db()
        print("[OK] 생산 엔지니어 모드 정상")

        # QC 엔지니어 인증 (비밀번호: 1234)
        if ac.authenticate_qc("1234"):
            print(f"[INFO] QC 인증 성공: {ac.get_current_level_name()}")
            assert ac.can_access_qc()
            assert ac.can_propose_checklist()
            assert not ac.can_access_default_db()
            print("[OK] QC 엔지니어 모드 정상")
        else:
            print("[WARN] QC 인증 실패 (설정 확인 필요)")

        # 로그아웃
        ac.logout()
        print(f"[INFO] 로그아웃 후: {ac.get_current_level_name()}")
        assert ac.get_current_level() == AccessLevel.PRODUCTION
        print("[OK] 로그아웃 정상")

        # 관리자 인증 (비밀번호: 1)
        if ac.authenticate_admin("1"):
            print(f"[INFO] 관리자 인증 성공: {ac.get_current_level_name()}")
            assert ac.can_access_qc()
            assert ac.can_access_default_db()
            assert ac.can_manage_checklist()
            print("[OK] 관리자 모드 정상")
        else:
            print("[WARN] 관리자 인증 실패 (설정 확인 필요)")

        return True

    except Exception as e:
        print(f"[FAIL] 권한 시스템 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_checklist_service():
    """Check list 관리 서비스 테스트"""
    print("\n[검색] 3. Check list 관리 서비스 테스트")
    print("=" * 60)

    try:
        from app.schema import DBSchema
        from app.services import ServiceFactory

        db_schema = DBSchema()
        service_factory = ServiceFactory(db_schema)

        # Check list 서비스 조회
        checklist_service = service_factory.get_checklist_service()
        if not checklist_service:
            print("[FAIL] Check list 서비스를 찾을 수 없습니다")
            return False

        print("[OK] Check list 서비스 초기화 성공")

        # 테스트용 공통 Check list 항목 추가
        print("\n[추가] 공통 Check list 항목 추가 테스트...")
        item_id = checklist_service.add_checklist_item(
            item_name="안전 온도 제한",
            parameter_pattern=".*temperature.*limit.*",
            is_common=True,
            severity_level='CRITICAL',
            validation_rule='{"type": "range", "min": 0, "max": 100}',
            description="안전을 위한 온도 제한 파라미터"
        )

        if item_id:
            print(f"[OK] Check list 항목 추가 성공 (ID: {item_id})")
        else:
            print("[WARN] Check list 항목 추가 실패 (이미 존재할 수 있음)")

        # 공통 Check list 항목 조회
        print("\n[항목] 공통 Check list 항목 조회...")
        common_items = checklist_service.get_common_checklist_items()
        print(f"[OK] 공통 Check list 항목: {len(common_items)}개")

        for item in common_items[:3]:  # 처음 3개만 출력
            print(f"  - {item[1]} ({item[4]})")

        # 장비 유형 생성 (테스트용)
        print("\n[장비] 테스트 장비 유형 생성...")
        equipment_id = db_schema.add_equipment_type("테스트장비_Phase1", "Phase 1 테스트용 장비")
        if equipment_id:
            print(f"[OK] 테스트 장비 생성 성공 (ID: {equipment_id})")

            # 장비별 Check list 조회
            print(f"\n[항목] 장비별 Check list 조회 (equipment_id={equipment_id})...")
            equipment_checklist = checklist_service.get_equipment_checklist(equipment_id)
            print(f"[OK] 장비별 Check list: {len(equipment_checklist)}개")

            for item in equipment_checklist[:3]:  # 처음 3개만 출력
                print(f"  - {item['item_name']} ({item['severity_level']}) [출처: {item['source']}]")

            # 파라미터 검증 테스트
            print("\n[검색] 파라미터 Check list 검증 테스트...")
            validation_result = checklist_service.validate_parameter_against_checklist(
                equipment_id, "temperature_limit", "50.0"
            )
            print(f"  파라미터: temperature_limit = 50.0")
            print(f"  Check list 포함: {validation_result['is_checklist']}")
            print(f"  검증 통과: {validation_result['validation_passed']}")
            if validation_result['is_checklist']:
                print(f"  심각도: {validation_result['severity_level']}")

            # 테스트 데이터 정리
            print("\n[정리] 테스트 데이터 정리...")
            db_schema.delete_equipment_type(equipment_id)
            print("[OK] 테스트 데이터 정리 완료")

        return True

    except Exception as e:
        print(f"[FAIL] Check list 서비스 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_methods():
    """DBSchema의 Check list 관련 메서드 테스트"""
    print("\n[검색] 4. DBSchema Check list 메서드 테스트")
    print("=" * 60)

    try:
        from app.schema import DBSchema

        db_schema = DBSchema()

        # Check list 항목 추가 테스트
        print("[추가] Check list 항목 추가...")
        item_id = db_schema.add_checklist_item(
            item_name="압력 안전 범위",
            parameter_pattern=".*pressure.*",
            is_common=True,
            severity_level='HIGH',
            description="압력 관련 안전 파라미터"
        )

        if item_id:
            print(f"[OK] Check list 항목 추가 성공 (ID: {item_id})")
        else:
            print("[WARN] Check list 항목 추가 실패 (이미 존재)")

        # Check list 항목 조회 테스트
        print("\n[항목] Check list 항목 조회...")
        items = db_schema.get_checklist_items(common_only=True)
        print(f"[OK] 공통 Check list: {len(items)}개")

        # Audit Log 조회 테스트
        print("\n[로그] Audit Log 조회...")
        logs = db_schema.get_checklist_audit_log(limit=5)
        print(f"[OK] Audit Log: {len(logs)}개 (최근 5개)")
        for log in logs:
            print(f"  - {log[1]}: {log[2]} (사용자: {log[7]})")

        return True

    except Exception as e:
        print(f"[FAIL] DBSchema 메서드 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print(">> Phase 1 기능 테스트 시작")
    print("=" * 60)

    tests = [
        ("데이터베이스 스키마", test_database_schema),
        ("3단계 권한 시스템", test_access_control),
        ("Check list 관리 서비스", test_checklist_service),
        ("DBSchema Check list 메서드", test_schema_methods),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[FAIL] {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))

    # 결과 요약
    print("\n" + "=" * 60)
    print("[통계] 테스트 결과 요약")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "[OK] 성공" if result else "[FAIL] 실패"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print("=" * 60)
    print(f"전체 결과: {passed}/{len(results)} 성공")

    if passed == len(results):
        print("\n[성공] 모든 Phase 1 기능 테스트가 성공했습니다!")
        return True
    else:
        print(f"\n[WARN] {len(results) - passed}개 테스트가 실패했습니다.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
