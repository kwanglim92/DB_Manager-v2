#!/usr/bin/env python3
"""
Refactor update_grid_view into smaller methods
Split 174 lines into 4 methods (~40-50 lines each)
"""

def generate_refactored_code():
    """Generate refactored code for update_grid_view"""

    code = '''
    def _configure_grid_view_tags(self):
        """계층별 스타일 태그 설정 (Grid View)"""
        # 모듈 레벨 - 가장 크고 굵게 (기본 파란색)
        self.grid_tree.tag_configure("module",
                                    font=("Arial", 11, "bold"),
                                    background="#F5F5F5",
                                    foreground="#1565C0")

        # 모듈 레벨 - 차이 있음 (빨간색 강조)
        self.grid_tree.tag_configure("module_diff",
                                    font=("Arial", 11, "bold"),
                                    background="#F5F5F5",
                                    foreground="#D32F2F")

        # 파트 레벨 - 중간 크기, 볼드
        self.grid_tree.tag_configure("part",
                                    font=("Arial", 10, "bold"),
                                    background="#FAFAFA",
                                    foreground="#424242")

        # 파트 레벨 - 모든 값 동일 (초록색)
        self.grid_tree.tag_configure("part_clean",
                                    font=("Arial", 10, "bold"),
                                    background="#FAFAFA",
                                    foreground="#2E7D32")

        # 파트 레벨 - 차이 있음 (빨간색 강조)
        self.grid_tree.tag_configure("part_diff",
                                    font=("Arial", 10, "bold"),
                                    background="#FAFAFA",
                                    foreground="#D32F2F")

        # 파라미터 레벨 - 기본 크기
        self.grid_tree.tag_configure("parameter_same",
                                    font=("Arial", 9),
                                    background="white",
                                    foreground="black")

        # 차이점이 있는 파라미터 - 전체 목록 탭과 동일한 색상
        self.grid_tree.tag_configure("parameter_different",
                                    font=("Arial", 9),
                                    background="#FFECB3",
                                    foreground="#E65100")

    def _build_grid_hierarchy_data(self, columns):
        """계층 구조 데이터 구성 (Grid View)

        Returns:
            tuple: (modules_data, total_params, diff_count)
        """
        modules_data = {}
        total_params = 0
        diff_count = 0

        grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])

        for (module, part, item_name), group in grouped:
            if module not in modules_data:
                modules_data[module] = {}
            if part not in modules_data[module]:
                modules_data[module][part] = {}

            # 각 파일별 값 수집
            values = []
            for model in self.file_names:
                model_data = group[group["Model"] == model]
                if not model_data.empty:
                    values.append(str(model_data["ItemValue"].iloc[0]))
                else:
                    values.append("-")

            # 값 차이 확인 (빈 값 제외)
            non_empty_values = [v for v in values if v != "-"]
            has_difference = len(set(non_empty_values)) > 1 if len(non_empty_values) > 1 else False

            modules_data[module][part][item_name] = {
                "values": values,
                "has_difference": has_difference
            }
            total_params += 1
            if has_difference:
                diff_count += 1

        return modules_data, total_params, diff_count

    def _populate_grid_tree(self, modules_data, columns, diff_count):
        """트리뷰에 계층 구조로 데이터 추가 및 통계 업데이트"""
        # 트리뷰에 계층 구조로 데이터 추가
        for module_name in sorted(modules_data.keys()):
            # 모듈 레벨 통계 계산
            module_total = sum(len(modules_data[module_name][part]) for part in modules_data[module_name])
            module_diff = sum(1 for part in modules_data[module_name]
                            for item in modules_data[module_name][part]
                            if modules_data[module_name][part][item]["has_difference"])

            # 모듈 표시 - 파란색 통일
            if module_diff == 0:
                module_text = f"📁 {module_name} ({module_total})"
            else:
                module_text = f"📁 {module_name} ({module_total}) Diff: {module_diff}"
            module_tag = "module"

            # 모듈 노드 추가
            module_node = self.grid_tree.insert("", "end",
                                               text=module_text,
                                               values=[""] * len(columns),
                                               open=True,
                                               tags=(module_tag,))

            for part_name in sorted(modules_data[module_name].keys()):
                # 파트 레벨 통계 계산
                part_total = len(modules_data[module_name][part_name])
                part_diff = sum(1 for item in modules_data[module_name][part_name]
                              if modules_data[module_name][part_name][item]["has_difference"])

                # 파트 표시 - 차이가 없으면 초록색, 있으면 회색
                if part_diff == 0:
                    part_text = f"📂 {part_name} ({part_total})"
                    part_tag = "part_clean"
                else:
                    part_text = f"📂 {part_name} ({part_total}) Diff: {part_diff}"
                    part_tag = "part_diff"

                # 파트 노드 추가
                part_node = self.grid_tree.insert(module_node, "end",
                                                 text=part_text,
                                                 values=[""] * len(columns),
                                                 open=True,
                                                 tags=(part_tag,))

                for item_name in sorted(modules_data[module_name][part_name].keys()):
                    # 파라미터 노드 추가 - 기본 크기, 차이점에 따라 색상 구분
                    item_data = modules_data[module_name][part_name][item_name]
                    values = item_data["values"]
                    has_difference = item_data["has_difference"]

                    # 태그 선택
                    tag = "parameter_different" if has_difference else "parameter_same"

                    self.grid_tree.insert(part_node, "end",
                                        text=item_name,
                                        values=values,
                                        tags=(tag,))

        # 통계 정보 업데이트
        total_params = sum(len(parts_data)
                          for module_data in modules_data.values()
                          for parts_data in module_data.values())

        if hasattr(self, 'grid_total_label'):
            self.grid_total_label.config(text=f"총 파라미터: {total_params}")
            self.grid_modules_label.config(text=f"모듈 수: {len(modules_data)}")

            total_parts = sum(len(parts) for parts in modules_data.values())
            self.grid_parts_label.config(text=f"파트 수: {total_parts}")

            # 차이점 개수도 표시
            if hasattr(self, 'grid_diff_label'):
                self.grid_diff_label.config(text=f"값이 다른 항목: {diff_count}")

    def update_grid_view(self):
        """격자뷰 데이터 업데이트 - 트리뷰 구조 (리팩토링됨)"""
        if not hasattr(self, 'grid_tree'):
            return

        # 기존 데이터 삭제
        self._clear_treeview(self.grid_tree)

        if self.merged_df is None or self.merged_df.empty:
            # 통계 정보 초기화
            if hasattr(self, 'grid_total_label'):
                self.grid_total_label.config(text="총 파라미터: 0개")
                self.grid_modules_label.config(text="모듈 수: 0개")
                self.grid_parts_label.config(text="파트 수: 0개")
            return

        # 동적 컬럼 업데이트
        columns = tuple(self.file_names) if self.file_names else ("값",)
        self.grid_tree["columns"] = columns

        # 컬럼 헤딩 업데이트
        for col in columns:
            self.grid_tree.heading(col, text=col, anchor="center")
            self.grid_tree.column(col, width=150, anchor="center")

        # 계층별 스타일 태그 설정
        self._configure_grid_view_tags()

        # 계층 구조 데이터 구성
        modules_data, total_params, diff_count = self._build_grid_hierarchy_data(columns)

        # 트리뷰에 계층 구조로 데이터 추가 및 통계 업데이트
        self._populate_grid_tree(modules_data, columns, diff_count)
'''

    return code

if __name__ == '__main__':
    print("Generated refactored code for update_grid_view:")
    print(generate_refactored_code())
