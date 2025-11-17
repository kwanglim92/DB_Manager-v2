#!/usr/bin/env python3
"""
사용자 정의 QC 검수 설정 모듈
DB와 독립적으로 사용자가 정의한 Equipment Type과 스펙 관리
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class CustomQCConfig:
    """사용자 정의 QC 설정 관리"""
    
    DEFAULT_CONFIG_PATH = 'config/custom_qc_specs.json'
    
    # 기본 Equipment Types (사용자 정의)
    DEFAULT_EQUIPMENT_TYPES = [
        "Standard Model",
        "Advanced Model", 
        "Custom Model",
        "Test Configuration",
        "Production Line A",
        "Production Line B"
    ]
    
    def __init__(self, config_path: str = None):
        """
        초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """설정 파일 로드"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"설정 파일 로드 오류: {e}")
                
        # 기본 설정 생성
        return self.create_default_config()
        
    def create_default_config(self) -> Dict:
        """기본 설정 생성"""
        config = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'equipment_types': self.DEFAULT_EQUIPMENT_TYPES,
            'specs': {}
        }
        
        # 각 Equipment Type에 대한 기본 스펙
        for eq_type in self.DEFAULT_EQUIPMENT_TYPES:
            config['specs'][eq_type] = self.get_default_specs()
            
        return config
        
    def get_default_specs(self) -> List[Dict]:
        """기본 QC 스펙 템플릿"""
        return [
            {
                'item_name': 'Temperature',
                'min_spec': 20,
                'max_spec': 25,
                'unit': '°C',
                'enabled': True
            },
            {
                'item_name': 'Pressure',
                'min_spec': 100,
                'max_spec': 200,
                'unit': 'kPa',
                'enabled': True
            },
            {
                'item_name': 'Flow_Rate',
                'min_spec': 10,
                'max_spec': 20,
                'unit': 'L/min',
                'enabled': True
            },
            {
                'item_name': 'Voltage',
                'min_spec': 3.2,
                'max_spec': 3.4,
                'unit': 'V',
                'enabled': True
            },
            {
                'item_name': 'Current',
                'min_spec': 0.8,
                'max_spec': 1.2,
                'unit': 'A',
                'enabled': True
            }
        ]
        
    def save_config(self):
        """설정 저장"""
        try:
            # 디렉토리가 있는 경우만 생성
            if self.config_path:
                dir_path = os.path.dirname(self.config_path)
                if dir_path:  # 디렉토리 경로가 있는 경우
                    os.makedirs(dir_path, exist_ok=True)
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                return True
            return False
        except Exception as e:
            print(f"설정 저장 오류: {e}")
            return False
            
    def get_equipment_types(self) -> List[str]:
        """Equipment Type 목록 반환"""
        return self.config.get('equipment_types', self.DEFAULT_EQUIPMENT_TYPES)
        
    def add_equipment_type(self, type_name: str) -> bool:
        """Equipment Type 추가"""
        if type_name not in self.config['equipment_types']:
            self.config['equipment_types'].append(type_name)
            self.config['specs'][type_name] = self.get_default_specs()
            return self.save_config()
        return False
        
    def remove_equipment_type(self, type_name: str) -> bool:
        """Equipment Type 제거"""
        if type_name in self.config['equipment_types']:
            self.config['equipment_types'].remove(type_name)
            if type_name in self.config['specs']:
                del self.config['specs'][type_name]
            return self.save_config()
        return False
        
    def get_specs(self, equipment_type: str) -> List[Dict]:
        """특정 Equipment Type의 스펙 반환"""
        return self.config.get('specs', {}).get(equipment_type, [])
        
    def update_specs(self, equipment_type: str, specs: List[Dict]) -> bool:
        """스펙 업데이트"""
        if 'specs' not in self.config:
            self.config['specs'] = {}
        self.config['specs'][equipment_type] = specs
        return self.save_config()
        
    def add_spec_item(self, equipment_type: str, item: Dict) -> bool:
        """스펙 항목 추가"""
        if equipment_type in self.config.get('specs', {}):
            self.config['specs'][equipment_type].append(item)
            return self.save_config()
        return False
        
    def remove_spec_item(self, equipment_type: str, item_name: str) -> bool:
        """스펙 항목 제거"""
        if equipment_type in self.config.get('specs', {}):
            specs = self.config['specs'][equipment_type]
            self.config['specs'][equipment_type] = [
                s for s in specs if s.get('item_name') != item_name
            ]
            return self.save_config()
        return False
        
    def export_to_file(self, filepath: str) -> bool:
        """설정을 파일로 내보내기"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"내보내기 오류: {e}")
            return False
            
    def import_from_file(self, filepath: str) -> bool:
        """파일에서 설정 가져오기"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported = json.load(f)
                
            # 유효성 검사
            if 'equipment_types' in imported and 'specs' in imported:
                self.config = imported
                return self.save_config()
                
            return False
        except Exception as e:
            print(f"가져오기 오류: {e}")
            return False