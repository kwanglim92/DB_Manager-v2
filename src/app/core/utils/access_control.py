"""
3단계 권한 관리 시스템

생산 엔지니어 (기본) -> QC 엔지니어 -> 관리자
"""

import hashlib
import json
import os
from enum import Enum

class AccessLevel(Enum):
    """권한 레벨 정의"""
    PRODUCTION = 1  # 생산 엔지니어 (기본, 읽기 전용)
    QC = 2          # QC 엔지니어 (QC 검수, Check list 조회/제안)
    ADMIN = 3       # 관리자 (모든 기능 + Default DB 관리)

class AccessControl:
    """3단계 권한 관리"""

    def __init__(self, config_path=None):
        """
        Args:
            config_path: settings.json 경로 (None이면 기본 경로 사용)
        """
        if config_path is None:
            # 기본 경로: config/settings.json
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            config_path = os.path.join(project_root, 'config', 'settings.json')

        self.config_path = config_path
        self.current_level = AccessLevel.PRODUCTION
        self._load_config()

    def _load_config(self):
        """설정 파일에서 비밀번호 해시 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 3단계 권한 해시
            access_control = config.get('access_control', {})
            self.qc_password_hash = access_control.get('qc_password_hash', '')
            self.admin_password_hash = access_control.get('admin_password_hash', '')

            # 레거시 호환성
            if not self.admin_password_hash:
                self.admin_password_hash = config.get('maint_password_hash', '')

        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
            self.qc_password_hash = ''
            self.admin_password_hash = ''

    def _hash_password(self, password):
        """비밀번호 SHA256 해시 생성"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate_qc(self, password):
        """
        QC 엔지니어 인증

        Args:
            password: 입력된 비밀번호

        Returns:
            bool: 인증 성공 여부
        """
        if not self.qc_password_hash:
            return False

        if self._hash_password(password) == self.qc_password_hash:
            self.current_level = AccessLevel.QC
            return True
        return False

    def authenticate_admin(self, password):
        """
        관리자 인증

        Args:
            password: 입력된 비밀번호

        Returns:
            bool: 인증 성공 여부
        """
        if not self.admin_password_hash:
            return False

        if self._hash_password(password) == self.admin_password_hash:
            self.current_level = AccessLevel.ADMIN
            return True
        return False

    def logout(self):
        """로그아웃 (생산 엔지니어 모드로 복귀)"""
        self.current_level = AccessLevel.PRODUCTION

    def get_current_level(self):
        """현재 권한 레벨 조회"""
        return self.current_level

    def get_current_level_name(self):
        """현재 권한 레벨 이름 조회"""
        names = {
            AccessLevel.PRODUCTION: "생산 엔지니어",
            AccessLevel.QC: "QC 엔지니어",
            AccessLevel.ADMIN: "관리자"
        }
        return names.get(self.current_level, "알 수 없음")

    def can_access_qc(self):
        """QC 기능 접근 가능 여부"""
        return self.current_level.value >= AccessLevel.QC.value

    def can_access_default_db(self):
        """Default DB 관리 기능 접근 가능 여부 (관리자만)"""
        return self.current_level == AccessLevel.ADMIN

    def can_manage_checklist(self):
        """Check list 관리 기능 접근 가능 여부 (관리자만)"""
        return self.current_level == AccessLevel.ADMIN

    def can_propose_checklist(self):
        """Check list 제안 기능 접근 가능 여부 (QC 엔지니어 이상)"""
        return self.current_level.value >= AccessLevel.QC.value

    def has_write_access(self):
        """쓰기 권한 여부 (QC 엔지니어 이상)"""
        return self.current_level.value >= AccessLevel.QC.value

    def validate_access(self, required_level):
        """
        특정 권한 레벨 요구사항 검증

        Args:
            required_level: 필요한 권한 레벨 (AccessLevel)

        Returns:
            bool: 접근 가능 여부

        Raises:
            PermissionError: 권한 부족 시
        """
        if self.current_level.value < required_level.value:
            raise PermissionError(
                f"이 기능은 {required_level.name} 권한이 필요합니다. "
                f"현재 권한: {self.get_current_level_name()}"
            )
        return True


# 전역 싱글톤 인스턴스
_access_control_instance = None

def get_access_control():
    """전역 AccessControl 인스턴스 조회"""
    global _access_control_instance
    if _access_control_instance is None:
        _access_control_instance = AccessControl()
    return _access_control_instance
