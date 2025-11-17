#!/usr/bin/env python3
"""
간소화된 QC 검수 UI 프로토타입
Phase 1: 독립적인 테스트 모듈
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
import json
import os

class SimplifiedQCTab:
    """간소화된 QC 검수 UI - 프로토타입"""
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.selected_files = []
        self.qc_results = []
        
        # UI 생성
        self.create_ui()
        
        # 샘플 스펙 데이터 (실제는 QC_Spec_Master에서 로드)
        self.sample_specs = {
            'Temperature': {'min': 20, 'max': 25},
            'Pressure': {'min': 100, 'max': 200},
            'Flow_Rate': {'min': 10, 'max': 20},
            'Voltage': {'min': 3.2, 'max': 3.4},
            'Current': {'min': 0.8, 'max': 1.2}
        }
    
    def create_ui(self):
        """간소화된 UI 생성"""
        
        # 1. 제어 패널 (한 줄)
        control_panel = ttk.Frame(self.frame)
        control_panel.pack(fill=tk.X, padx=10, pady=5)
        
        # Equipment Type 선택
        ttk.Label(control_panel, text="Equipment Type:", 
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.equipment_var = tk.StringVar()
        self.equipment_combo = ttk.Combobox(control_panel, 
                                           textvariable=self.equipment_var,
                                           values=["Model A", "Model B", "Model C"],
                                           width=20, state="readonly")
        self.equipment_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.equipment_combo.set("Model A")
        
        # 파일 선택 버튼
        self.select_btn = ttk.Button(control_panel, text="📁 파일 선택",
                                    command=self.select_files)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 새로고침 버튼
        self.refresh_btn = ttk.Button(control_panel, text="🔄 새로고침",
                                     command=self.refresh_results)
        self.refresh_btn.pack(side=tk.LEFT)
        
        # 선택된 파일 표시
        self.file_label = ttk.Label(control_panel, text="파일 미선택",
                                   font=("Segoe UI", 9), foreground="gray")
        self.file_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # 2. 결과 테이블
        result_frame = ttk.LabelFrame(self.frame, text="📊 검수 결과", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 트리뷰 생성
        columns = ('item_name', 'measured', 'min_spec', 'max_spec', 'result')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, 
                                       show='headings', height=15)
        
        # 컬럼 헤더 설정
        headers = {
            'item_name': 'Item Name',
            'measured': '측정값',
            'min_spec': 'Min Spec',
            'max_spec': 'Max Spec',
            'result': '결과'
        }
        
        widths = {
            'item_name': 150,
            'measured': 100,
            'min_spec': 80,
            'max_spec': 80,
            'result': 80
        }
        
        for col in columns:
            self.result_tree.heading(col, text=headers[col])
            self.result_tree.column(col, width=widths[col])
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical",
                                command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 3. 요약 패널
        summary_frame = ttk.LabelFrame(self.frame, text="📈 검수 요약", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 요약 정보
        self.summary_label = ttk.Label(summary_frame, 
                                      text="대기 중...",
                                      font=("Segoe UI", 11))
        self.summary_label.pack(side=tk.LEFT)
        
        # 내보내기 버튼
        self.export_btn = ttk.Button(summary_frame, text="📥 결과 내보내기",
                                    command=self.export_results, state='disabled')
        self.export_btn.pack(side=tk.RIGHT)
        
        # Pass 항목만 보기 체크박스
        self.show_fail_only = tk.BooleanVar()
        ttk.Checkbutton(summary_frame, text="Fail 항목만 보기",
                       variable=self.show_fail_only,
                       command=self.filter_results).pack(side=tk.RIGHT, padx=(0, 20))
    
    def select_files(self):
        """파일 선택"""
        files = filedialog.askopenfilenames(
            title="QC 검수할 파일 선택",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), 
                      ("All files", "*.*")]
        )
        
        if files:
            self.selected_files = files
            # 파일명 표시
            if len(files) == 1:
                filename = os.path.basename(files[0])
                self.file_label.config(text=filename, foreground="black")
            else:
                self.file_label.config(text=f"{len(files)}개 파일 선택됨", 
                                     foreground="black")
            
            # 자동으로 검수 실행
            self.run_qc_inspection()
    
    def run_qc_inspection(self):
        """QC 검수 실행"""
        if not self.selected_files:
            messagebox.showwarning("경고", "파일을 먼저 선택하세요")
            return
        
        # 결과 초기화
        self.qc_results = []
        
        # 샘플 데이터 생성 (실제는 파일에서 읽음)
        import random
        for item_name, spec in self.sample_specs.items():
            # 측정값 생성 (일부는 스펙 벗어나게)
            if random.random() > 0.8:  # 20% 확률로 Fail
                measured = spec['min'] - random.uniform(1, 5)
            else:
                measured = random.uniform(spec['min'], spec['max'])
            
            # Pass/Fail 판정
            pass_fail = "✅ Pass" if spec['min'] <= measured <= spec['max'] else "❌ Fail"
            
            self.qc_results.append({
                'item_name': item_name,
                'measured': round(measured, 2),
                'min_spec': spec['min'],
                'max_spec': spec['max'],
                'result': pass_fail
            })
        
        # 결과 표시
        self.display_results()
    
    def display_results(self):
        """결과 표시"""
        # 트리뷰 초기화
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 필터링
        show_fail = self.show_fail_only.get()
        
        # 결과 추가
        pass_count = 0
        fail_count = 0
        
        for result in self.qc_results:
            if show_fail and "Pass" in result['result']:
                continue
                
            # Pass/Fail 카운트
            if "Pass" in result['result']:
                pass_count += 1
                tag = 'pass'
            else:
                fail_count += 1
                tag = 'fail'
            
            # 트리뷰에 추가
            self.result_tree.insert('', 'end', 
                                   values=(result['item_name'],
                                          result['measured'],
                                          result['min_spec'],
                                          result['max_spec'],
                                          result['result']),
                                   tags=(tag,))
        
        # 태그 색상 설정
        self.result_tree.tag_configure('pass', foreground='green')
        self.result_tree.tag_configure('fail', foreground='red', 
                                      background='#ffeeee')
        
        # 요약 업데이트
        if not show_fail:
            total = len(self.qc_results)
        else:
            total = fail_count
            
        pass_rate = (pass_count / max(1, pass_count + fail_count)) * 100
        
        summary_text = f"Total: {pass_count + fail_count} | "
        summary_text += f"Pass: {pass_count} ({pass_rate:.1f}%) | "
        summary_text += f"Fail: {fail_count}"
        
        self.summary_label.config(text=summary_text)
        
        # 내보내기 버튼 활성화
        self.export_btn.config(state='normal' if self.qc_results else 'disabled')
    
    def filter_results(self):
        """결과 필터링"""
        self.display_results()
    
    def refresh_results(self):
        """결과 새로고침"""
        if self.selected_files:
            self.run_qc_inspection()
        else:
            messagebox.showinfo("알림", "선택된 파일이 없습니다")
    
    def export_results(self):
        """결과 내보내기"""
        if not self.qc_results:
            return
        
        # 파일 저장 다이얼로그
        filename = filedialog.asksaveasfilename(
            title="검수 결과 저장",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        
        if filename:
            # DataFrame 생성
            df = pd.DataFrame(self.qc_results)
            
            # 저장
            if filename.endswith('.xlsx'):
                df.to_excel(filename, index=False)
            else:
                df.to_csv(filename, index=False)
            
            messagebox.showinfo("완료", f"결과가 저장되었습니다:\n{filename}")


def main():
    """독립 실행 테스트"""
    root = tk.Tk()
    root.title("간소화된 QC 검수 UI - 프로토타입")
    root.geometry("800x600")
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')
    
    # 탭 생성
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 간소화 탭
    simplified_tab = SimplifiedQCTab(notebook)
    notebook.add(simplified_tab.frame, text="간소화 QC 검수 (Beta)")
    
    # 비교용 빈 탭 (기존 UI 자리)
    legacy_frame = ttk.Frame(notebook)
    ttk.Label(legacy_frame, text="기존 QC 검수 UI 위치\n(비교 테스트용)",
             font=("Segoe UI", 14)).pack(pady=50)
    notebook.add(legacy_frame, text="기존 QC 검수")
    
    # 정보 표시
    info_text = """
    🧪 간소화된 QC 검수 UI 프로토타입
    
    주요 특징:
    • 한 줄 제어 패널
    • 자동 검수 실행
    • 간단한 Pass/Fail 표시
    • Fail 항목 필터링
    
    테스트 방법:
    1. Equipment Type 선택
    2. 파일 선택 클릭
    3. 결과 자동 표시
    4. Fail 항목만 보기 체크
    5. 결과 내보내기
    """
    
    info_frame = ttk.Frame(root)
    info_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(info_frame, text=info_text, justify=tk.LEFT,
             font=("Segoe UI", 9)).pack()
    
    root.mainloop()

if __name__ == "__main__":
    main()