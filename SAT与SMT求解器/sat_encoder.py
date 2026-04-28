# -*- coding: utf-8 -*-
"""
SAT编码器：将约束问题编码为CNF公式
功能：将各种约束问题（数独、图着色、N皇后等）转换为SAT的CNF格式

编码技术：
1. Tseitin编码：将任意布尔公式转换为CNF（线性大小增长）
2. 基数约束：AtMostOne, ExactlyOne, AtLeastK 等
3. 域变量编码：每个变量有多个可能值时使用one-hot或对数编码

作者：Constraint Encoder Team
"""

from typing import List, Dict, Set, Tuple


class SATEncoder:
    """SAT编码器基类"""

    def __init__(self):
        self.cnf: List[List[int]] = []  # 编码后的CNF
        self.next_var = 1  # 下一个可用变量ID
        self.var_map: Dict[Tuple, int] = {}  # 映射→变量

    def new_var(self) -> int:
        """分配新变量"""
        var = self.next_var
        self.next_var += 1
        return var

    def add_clause(self, lits: List[int]):
        """添加子句"""
        self.cnf.append(lits)

    def var(self, name: str) -> int:
        """获取或创建命名变量"""
        if name not in self.var_map:
            self.var_map[name] = self.new_var()
        return self.var_map[name]


class SudokuEncoder(SATEncoder):
    """
    数独编码器
    9x9数独 → 9*9*9 = 729 个布尔变量
    variable(i, j, v) = 第i行第j列的值为v
    """

    def __init__(self, grid: List[List[int]]):
        """
        初始化数独编码器
        
        Args:
            grid: 9x9网格，0表示空格，1-9表示已知数字
        """
        super().__init__()
        self.grid = grid
        self.n = 9
        self.encode()

    def cell_var(self, row: int, col: int, val: int) -> int:
        """获取格子(row,col)的值val对应的变量"""
        key = ('cell', row, col, val)
        if key not in self.var_map:
            self.var_map[key] = self.new_var()
        return self.var_map[key]

    def encode(self):
        """生成数独的CNF编码"""
        # 约束1：每个格子至少有一个值
        for r in range(9):
            for c in range(9):
                self.add_clause([self.cell_var(r, c, v) for v in range(1, 10)])
        
        # 约束2：每个格子至多有一个值（pairwise互斥）
        for r in range(9):
            for c in range(9):
                for v1 in range(1, 10):
                    for v2 in range(v1 + 1, 10):
                        lit1 = -self.cell_var(r, c, v1)
                        lit2 = -self.cell_var(r, c, v2)
                        self.add_clause([lit1, lit2])
        
        # 约束3：每行每个值只能出现一次
        for r in range(9):
            for v in range(1, 10):
                for c1 in range(9):
                    for c2 in range(c1 + 1, 9):
                        lit1 = -self.cell_var(r, c1, v)
                        lit2 = -self.cell_var(r, c2, v)
                        self.add_clause([lit1, lit2])
        
        # 约束4：每列每个值只能出现一次
        for c in range(9):
            for v in range(1, 10):
                for r1 in range(9):
                    for r2 in range(r1 + 1, 9):
                        lit1 = -self.cell_var(r1, c, v)
                        lit2 = -self.cell_var(r2, c, v)
                        self.add_clause([lit1, lit2])
        
        # 约束5：每个3x3子矩阵每个值只能出现一次
        for bi in range(3):
            for bj in range(3):
                for v in range(1, 10):
                    cells = [(bi * 3 + i, bj * 3 + j) 
                              for i in range(3) for j in range(3)]
                    for idx1 in range(len(cells)):
                        for idx2 in range(idx1 + 1, len(cells)):
                            r1, c1 = cells[idx1]
                            r2, c2 = cells[idx2]
                            lit1 = -self.cell_var(r1, c1, v)
                            lit2 = -self.cell_var(r2, c2, v)
                            self.add_clause([lit1, lit2])
        
        # 约束6：填入已知数字
        for r in range(9):
            for c in range(9):
                if self.grid[r][c] != 0:
                    self.add_clause([self.cell_var(r, c, self.grid[r][c])])

    def decode(self, assignment: Dict[int, bool]) -> List[List[int]]:
        """从SAT解解码为数独解"""
        result = [[0] * 9 for _ in range(9)]
        for (kind, r, c, v), var in self.var_map.items():
            if kind == 'cell' and assignment.get(var, False):
                result[r][c] = v
        return result


class GraphColoringEncoder(SATEncoder):
    """图着色问题编码"""

    def __init__(self, edges: List[Tuple[int, int]], n_colors: int):
        """
        Args:
            edges: 边列表，如[(0,1), (1,2)]表示无向图边
            n_colors: 颜色数量
        """
        super().__init__()
        self.edges = edges
        self.n_colors = n_colors
        self.n_nodes = max(max(e) for e in edges) + 1 if edges else 0
        self.encode()

    def node_color_var(self, node: int, color: int) -> int:
        """节点node使用颜色color的变量"""
        key = ('color', node, color)
        if key not in self.var_map:
            self.var_map[key] = self.new_var()
        return self.var_map[key]

    def encode(self):
        """生成图着色CNF"""
        # 每个节点至少一种颜色
        for node in range(self.n_nodes):
            self.add_clause([self.node_color_var(node, c) for c in range(self.n_colors)])
        
        # 每个节点至多一种颜色
        for node in range(self.n_nodes):
            for c1 in range(self.n_colors):
                for c2 in range(c1 + 1, self.n_colors):
                    lit1 = -self.node_color_var(node, c1)
                    lit2 = -self.node_color_var(node, c2)
                    self.add_clause([lit1, lit2])
        
        # 相邻节点不能同色
        for u, v in self.edges:
            for c in range(self.n_colors):
                lit1 = -self.node_color_var(u, c)
                lit2 = -self.node_color_var(v, c)
                self.add_clause([lit1, lit2])


class CardinalityEncoder(SATEncoder):
    """基数约束编码：AtMostK, ExactlyK, AtLeastK"""

    @staticmethod
    def at_most_one(lits: List[int], encoder: SATEncoder):
        """
        编码 AtMostOne 约束：至多一个文字为真
        
        方法：pairwise比较（O(n²)子句）
        优点：编码简单，适合小规模约束
        """
        n = len(lits)
        for i in range(n):
            for j in range(i + 1, n):
                encoder.add_clause([-lits[i], -lits[j]])

    @staticmethod
    def exactly_one(lits: List[int], encoder: SATEncoder):
        """编码 ExactlyOne 约束：恰好一个为真"""
        # 至少一个
        encoder.add_clause(lits)
        # 至多一个
        CardinalityEncoder.at_most_one(lits, encoder)

    @staticmethod
    def at_least_k(lits: List[int], k: int, encoder: SATEncoder):
        """
        编码 AtLeastK 约束：至少k个文字为真
        
        方法：暴力枚举所有n-k+1个组合
        """
        n = len(lits)
        from itertools import combinations
        for combo in combinations(range(n), n - k + 1):
            encoder.add_clause([lits[i] for i in combo])

    @staticmethod
    def pairwise_at_most_k(lits: List[int], k: int, encoder: SATEncoder):
        """
        编码 Cardinality(at_most_k): 至多k个为真
        
        方法：对于每对文字组合强制排除
        """
        n = len(lits)
        from itertools import combinations
        for combo in combinations(range(n), k + 1):
            encoder.add_clause([-lits[i] for i in combo])


class NQueensEncoder(SATEncoder):
    """N皇后编码"""

    def __init__(self, n: int):
        super().__init__()
        self.n = n
        self.encode()

    def queen_var(self, row: int, col: int) -> int:
        """(row, col)有皇后"""
        key = ('queen', row, col)
        if key not in self.var_map:
            self.var_map[key] = self.new_var()
        return self.var_map[key]

    def encode(self):
        n = self.n
        # 每行恰好一个皇后
        for row in range(n):
            self.add_clause([self.queen_var(row, col) for col in range(n)])
            CardinalityEncoder.at_most_one(
                [self.queen_var(row, col) for col in range(n)], self)
        
        # 每列至多一个皇后
        for col in range(n):
            CardinalityEncoder.at_most_one(
                [self.queen_var(row, col) for row in range(n)], self)
        
        # 主对角线至多一个
        for d in range(-(n - 1), n):
            diag = [(row, d + row) for row in range(n) 
                    if 0 <= d + row < n]
            if len(diag) >= 2:
                CardinalityEncoder.at_most_one(
                    [self.queen_var(r, c) for r, c in diag], self)
        
        # 副对角线至多一个
        for d in range(0, 2 * n - 1):
            diag = [(row, d - row) for row in range(n) 
                    if 0 <= d - row < n]
            if len(diag) >= 2:
                CardinalityEncoder.at_most_one(
                    [self.queen_var(r, c) for r, c in diag], self)


def example_sudoku():
    """数独编码示例"""
    # 简单数独实例（0=空格）
    grid = [
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
    
    encoder = SudokuEncoder(grid)
    print(f"数独编码: {len(encoder.cnf)} 个子句, {encoder.next_var - 1} 个变量")
    print(f"原始空格数: {sum(1 for r in grid for c in r if c == 0)}")


def example_queens():
    """N皇后编码示例"""
    for n in [4, 8]:
        encoder = NQueensEncoder(n)
        print(f"{n}皇后: {len(encoder.cnf)} 子句, {encoder.next_var - 1} 变量")


def example_graph_coloring():
    """图着色示例"""
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
    for colors in [2, 3, 4]:
        encoder = GraphColoringEncoder(edges, colors)
        print(f"{len(colors)}色: {len(encoder.cnf)} 子句, {encoder.next_var - 1} 变量")


if __name__ == "__main__":
    print("=" * 50)
    print("SAT编码器 测试")
    print("=" * 50)
    
    example_sudoku()
    print()
    example_queens()
    print()
    example_graph_coloring()
