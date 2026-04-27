# -*- coding: utf-8 -*-

"""

算法实现：约束求解 / sudoku_solver



本文件实现 sudoku_solver 相关的算法功能。

"""



from typing import List, Dict, Set, Optional, Tuple

from collections import defaultdict





class SudokuSolver:

    """

    数独求解器

    使用回溯搜索配合约束传播(候选数消除)来求解数独

    """

    

    def __init__(self, board: List[List[int]]):

        """

        初始化求解器

        

        Args:

            board: 9x9数独棋盘,0表示空格

        """

        self.original_board = [row[:] for row in board]

        self.size = 9

        self.box_size = 3

        

        # 初始化候选数:每个单元格的可用数字集合

        self.candidates: Dict[Tuple[int, int], Set[int]] = {}

        self.initialize_candidates()

    

    def initialize_candidates(self):

        """初始化所有单元格的候选数"""

        for row in range(self.size):

            for col in range(self.size):

                if self.original_board[row][col] == 0:

                    self.candidates[(row, col)] = self.get_allowed_values(row, col)

    

    def get_allowed_values(self, row: int, col: int) -> Set[int]:

        """

        获取某单元格的合法数字集合

        

        Args:

            row: 行索引

            col: 列索引

        

        Returns:

            可用数字集合

        """

        if self.original_board[row][col] != 0:

            return set()

        

        # 获取行、列、宫已使用的数字

        used = set()

        

        # 行

        for c in range(self.size):

            val = self.original_board[row][c]

            if val != 0:

                used.add(val)

        

        # 列

        for r in range(self.size):

            val = self.original_board[r][col]

            if val != 0:

                used.add(val)

        

        # 宫

        box_row = (row // self.box_size) * self.box_size

        box_col = (col // self.box_size) * self.box_size

        for r in range(box_row, box_row + self.box_size):

            for c in range(box_col, box_col + self.box_size):

                val = self.original_board[r][c]

                if val != 0:

                    used.add(val)

        

        return {1, 2, 3, 4, 5, 6, 7, 8, 9} - used

    

    def get_row_cells(self, row: int) -> List[Tuple[int, int]]:

        """获取某行的所有单元格"""

        return [(row, c) for c in range(self.size)]

    

    def get_col_cells(self, col: int) -> List[Tuple[int, int]]:

        """获取某列的所有单元格"""

        return [(r, col) for r in range(self.size)]

    

    def get_box_cells(self, row: int, col: int) -> List[Tuple[int, int]]:

        """获取某宫的所有单元格"""

        box_row = (row // self.box_size) * self.box_size

        box_col = (col // self.box_size) * self.box_size

        return [(r, c) for r in range(box_row, box_row + self.box_size)

                           for c in range(box_col, box_col + self.box_size)]

    

    def eliminate_candidates(self, row: int, col: int, value: int) -> bool:

        """

        消除候选数:当某单元格被确定后,从同行列宫的其他单元格中移除该数字

        

        Args:

            row: 行

            col: 列

            value: 确定的值

        

        Returns:

            是否成功

        """

        # 从同行的其他单元格中移除

        for c in range(self.size):

            if c != col and self.original_board[row][c] == 0:

                if value in self.candidates[(row, c)]:

                    self.candidates[(row, c)].discard(value)

                    # 如果候选数变为空,则冲突

                    if not self.candidates[(row, c)]:

                        return False

        

        # 从同列的其他单元格中移除

        for r in range(self.size):

            if r != row and self.original_board[r][col] == 0:

                if value in self.candidates[(r, col)]:

                    self.candidates[(r, col)].discard(value)

                    if not self.candidates[(r, col)]:

                        return False

        

        # 从同宫的其他单元格中移除

        box_cells = self.get_box_cells(row, col)

        for r, c in box_cells:

            if (r, c) != (row, col) and self.original_board[r][c] == 0:

                if value in self.candidates[(r, c)]:

                    self.candidates[(r, c)].discard(value)

                    if not self.candidates[(r, c)]:

                        return False

        

        return True

    

    def naked_singles(self) -> bool:

        """

        裸单胞策略:如果某单元格的候选数只有一个,则该值被确定

        反复应用直到没有新的确定值

        

        Returns:

            是否成功(没有冲突)

        """

        changed = True

        while changed:

            changed = False

            

            for row in range(self.size):

                for col in range(self.size):

                    if self.original_board[row][col] == 0:

                        cand = self.candidates[(row, col)]

                        

                        # 裸单胞:只有一个候选数

                        if len(cand) == 1:

                            value = cand.pop()

                            self.original_board[row][col] = value

                            del self.candidates[(row, col)]

                            

                            if not self.eliminate_candidates(row, col, value):

                                return False

                            changed = True

        

        return True

    

    def hidden_singles(self) -> bool:

        """

        隐单胞策略:如果某行/列/宫中只有一个单元格可以填某数字,则该数字属于这个单元格

        

        Returns:

            是否成功

        """

        changed = True

        while changed:

            changed = False

            

            # 检查行

            for row in range(self.size):

                for value in range(1, 10):

                    # 找出可以填value的单元格

                    candidates_for_value = []

                    for col in range(self.size):

                        if self.original_board[row][col] == 0 and value in self.candidates[(row, col)]:

                            candidates_for_value.append(col)

                    

                    # 如果只有一个,则确定

                    if len(candidates_for_value) == 1:

                        col = candidates_for_value[0]

                        self.original_board[row][col] = value

                        del self.candidates[(row, col)]

                        

                        if not self.eliminate_candidates(row, col, value):

                            return False

                        changed = True

            

            # 检查列

            for col in range(self.size):

                for value in range(1, 10):

                    candidates_for_value = []

                    for row in range(self.size):

                        if self.original_board[row][col] == 0 and value in self.candidates[(row, col)]:

                            candidates_for_value.append(row)

                    

                    if len(candidates_for_value) == 1:

                        row = candidates_for_value[0]

                        self.original_board[row][col] = value

                        del self.candidates[(row, col)]

                        

                        if not self.eliminate_candidates(row, col, value):

                            return False

                        changed = True

            

            # 检查宫

            for box_row in range(3):

                for box_col in range(3):

                    for value in range(1, 10):

                        candidates_for_value = []

                        cells = self.get_box_cells(box_row * 3, box_col * 3)

                        for row, col in cells:

                            if self.original_board[row][col] == 0 and value in self.candidates[(row, col)]:

                                candidates_for_value.append((row, col))

                        

                        if len(candidates_for_value) == 1:

                            row, col = candidates_for_value[0]

                            self.original_board[row][col] = value

                            del self.candidates[(row, col)]

                            

                            if not self.eliminate_candidates(row, col, value):

                                return False

                            changed = True

        

        return True

    

    def propagate_constraints(self) -> bool:

        """

        约束传播:应用所有策略

        

        Returns:

            是否成功

        """

        if not self.naked_singles():

            return False

        if not self.hidden_singles():

            return False

        return True

    

    def select_unassigned_cell(self) -> Optional[Tuple[int, int]]:

        """

        选择一个未填写的单元格(MRV启发式:候选数最少)

        

        Returns:

            单元格坐标或None

        """

        min_candidates = 10

        best_cell = None

        

        for row in range(self.size):

            for col in range(self.size):

                if self.original_board[row][col] == 0:

                    num_candidates = len(self.candidates[(row, col)])

                    if num_candidates < min_candidates:

                        min_candidates = num_candidates

                        best_cell = (row, col)

        

        return best_cell

    

    def solve_backtrack(self) -> bool:

        """

        回溯搜索

        

        Returns:

            是否找到解

        """

        # 检查是否完成

        if self.is_complete():

            return True

        

        # 选择一个单元格

        cell = self.select_unassigned_cell()

        if cell is None:

            return False

        

        row, col = cell

        

        # 保存状态

        saved_board = [row[:] for row in self.original_board]

        saved_candidates = {k: v.copy() for k, v in self.candidates.items()}

        

        # 尝试每个候选数

        for value in sorted(self.candidates[(row, col)]):

            self.original_board[row][col] = value

            del self.candidates[(row, col)]

            

            if self.eliminate_candidates(row, col, value):

                if self.propagate_constraints():

                    if self.solve_backtrack():

                        return True

            

            # 回溯

            self.original_board = [row[:] for row in saved_board]

            self.candidates = {k: v.copy() for k, v in saved_candidates.items()}

        

        return False

    

    def is_complete(self) -> bool:

        """检查是否完成(所有单元格都已填写)"""

        for row in range(self.size):

            for col in range(self.size):

                if self.original_board[row][col] == 0:

                    return False

        return True

    

    def is_valid(self) -> bool:

        """检查当前状态是否有效"""

        # 检查行

        for row in range(self.size):

            seen = set()

            for col in range(self.size):

                val = self.original_board[row][col]

                if val != 0:

                    if val in seen:

                        return False

                    seen.add(val)

        

        # 检查列

        for col in range(self.size):

            seen = set()

            for row in range(self.size):

                val = self.original_board[row][col]

                if val != 0:

                    if val in seen:

                        return False

                    seen.add(val)

        

        # 检查宫

        for box_row in range(3):

            for box_col in range(3):

                seen = set()

                for r in range(box_row * 3, box_row * 3 + 3):

                    for c in range(box_col * 3, box_col * 3 + 3):

                        val = self.original_board[r][c]

                        if val != 0:

                            if val in seen:

                                return False

                            seen.add(val)

        

        return True

    

    def solve(self) -> bool:

        """

        求解数独

        

        Returns:

            是否找到解

        """

        # 先进行约束传播

        if not self.propagate_constraints():

            return False

        

        # 再进行回溯搜索

        return self.solve_backtrack()

    

    def get_solution(self) -> List[List[int]]:

        """获取解"""

        return [row[:] for row in self.original_board]

    

    def print_board(self, board: Optional[List[List[int]]] = None):

        """打印棋盘"""

        if board is None:

            board = self.original_board

        

        print("  +-------+-------+-------+")

        for i, row in enumerate(board):

            if i % 3 == 0 and i > 0:

                print("  +-------+-------+-------+")

            row_str = " ".join(str(v) if v != 0 else "." for v in row)

            print(f"  | {row_str[:2]} {row_str[3:5]} {row_str[6:8]} |")

        print("  +-------+-------+-------+")





def solve_sudoku(board: List[List[int]]) -> Optional[List[List[int]]]:

    """

    数独求解的便捷函数

    

    Args:

        board: 9x9棋盘,0表示空格

    

    Returns:

        解或None

    """

    solver = SudokuSolver(board)

    if solver.solve():

        return solver.get_solution()

    return None





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单数独

    print("测试1 - 简单数独:")

    easy_sudoku = [

        [5, 3, 0, 0, 7, 0, 0, 0, 0],

        [6, 0, 0, 1, 9, 5, 0, 0, 0],

        [0, 9, 8, 0, 0, 0, 0, 6, 0],

        [8, 0, 0, 0, 6, 0, 0, 0, 3],

        [4, 0, 0, 8, 0, 3, 0, 0, 1],

        [7, 0, 0, 0, 2, 0, 0, 0, 6],

        [0, 6, 0, 0, 0, 0, 2, 8, 0],

        [0, 0, 0, 4, 1, 9, 0, 0, 5],

        [0, 0, 0, 0, 8, 0, 0, 7, 9]

    ]

    

    solver1 = SudokuSolver(easy_sudoku)

    print("原始:")

    solver1.print_board()

    

    if solver1.solve():

        print("\n解:")

        solver1.print_board()

    else:

        print("无解")

    

    # 测试2: 中等难度

    print("\n测试2 - 中等难度:")

    medium_sudoku = [

        [0, 0, 0, 2, 6, 0, 7, 0, 1],

        [6, 8, 0, 0, 7, 0, 0, 9, 0],

        [1, 9, 0, 0, 0, 4, 5, 0, 0],

        [8, 2, 0, 1, 0, 0, 0, 0, 0],

        [0, 0, 4, 6, 0, 2, 9, 0, 0],

        [0, 0, 0, 0, 0, 3, 0, 2, 8],

        [0, 0, 9, 3, 0, 0, 0, 7, 4],

        [0, 4, 0, 0, 5, 0, 0, 3, 6],

        [7, 0, 3, 0, 1, 8, 0, 0, 0]

    ]

    

    solver2 = SudokuSolver(medium_sudoku)

    print("原始:")

    solver2.print_board()

    

    if solver2.solve():

        print("\n解:")

        solver2.print_board()

    else:

        print("无解")

    

    # 测试3: 困难数独

    print("\n测试3 - 困难数独:")

    hard_sudoku = [

        [0, 0, 0, 0, 0, 0, 2, 0, 0],

        [0, 8, 0, 0, 0, 7, 0, 9, 0],

        [7, 0, 2, 6, 0, 0, 0, 0, 0],

        [0, 7, 0, 0, 0, 0, 5, 0, 0],

        [0, 0, 0, 0, 9, 0, 4, 0, 0],

        [1, 0, 0, 0, 0, 8, 0, 0, 0],

        [0, 3, 1, 0, 0, 0, 0, 0, 6],

        [9, 0, 0, 0, 1, 0, 0, 0, 0],

        [0, 2, 0, 0, 0, 0, 0, 0, 0]

    ]

    

    solver3 = SudokuSolver(hard_sudoku)

    print("原始:")

    solver3.print_board()

    

    if solver3.solve():

        print("\n解:")

        solver3.print_board()

    else:

        print("无解")

    

    # 测试4: 验证解的有效性

    print("\n测试4 - 解的有效性验证:")

    if solver3.solve():

        print("解有效:", solver3.is_valid())

    

    print("\n所有测试完成!")

