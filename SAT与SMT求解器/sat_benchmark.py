# -*- coding: utf-8 -*-
"""
SAT基准测试和性能评估
功能：提供标准SAT实例测试框架

包含基准：
1. 随机k-SAT实例
2. 实际应用实例（数独、N皇后等）
3. 困难实例（相变区域）

作者：SAT Benchmark Team
"""

from typing import List, Tuple, Optional, Callable
import random
import time


class SATBenchmark:
    """
    SAT求解器基准测试
    """

    def __init__(self, solver_fn: Callable):
        """
        Args:
            solver_fn: SAT求解器函数，输入CNF返回解或None
        """
        self.solver_fn = solver_fn
        self.results: List[dict] = []

    def benchmark_random(self, n_vars: int, n_clauses: int, 
                        n_instances: int = 10) -> dict:
        """基准测试随机实例"""
        times = []
        solved = 0
        
        for i in range(n_instances):
            cnf = self._generate_random_cnf(n_vars, n_clauses)
            
            start = time.time()
            result = self.solver_fn(cnf)
            elapsed = time.time() - start
            
            times.append(elapsed)
            if result is not None:
                solved += 1
        
        return {
            'type': 'random',
            'n_vars': n_vars,
            'n_clauses': n_clauses,
            'solved': solved,
            'total': n_instances,
            'avg_time': sum(times) / len(times) if times else 0,
            'times': times
        }

    def benchmark_n_queens(self, sizes: List[int]) -> dict:
        """N皇后问题基准"""
        from sat_encoder import NQueensEncoder
        from dpll_solver import DPLLSolver
        
        results = []
        
        for n in sizes:
            encoder = NQueensEncoder(n)
            solver = DPLLSolver(encoder.cnf)
            
            start = time.time()
            result = solver.solve()
            elapsed = time.time() - start
            
            results.append({
                'n': n,
                'clauses': len(encoder.cnf),
                'vars': encoder.next_var - 1,
                'solved': result is not None,
                'time': elapsed
            })
        
        return {'type': 'n_queens', 'results': results}

    def benchmark_sudoku(self) -> dict:
        """数独问题基准"""
        from sat_encoder import SudokuEncoder
        from dpll_solver import DPLLSolver
        
        # 简单数独
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
        solver = DPLLSolver(encoder.cnf)
        
        start = time.time()
        result = solver.solve()
        elapsed = time.time() - start
        
        return {
            'type': 'sudoku',
            'clauses': len(encoder.cnf),
            'vars': encoder.next_var - 1,
            'solved': result is not None,
            'time': elapsed
        }

    def _generate_random_cnf(self, n_vars: int, n_clauses: int, 
                             clause_size: int = 3) -> List[List[int]]:
        """生成随机CNF"""
        cnf = []
        for _ in range(n_clauses):
            clause = []
            seen = set()
            while len(clause) < clause_size:
                var = random.randint(1, n_vars)
                lit = var if random.random() > 0.5 else -var
                if var not in seen:
                    clause.append(lit)
                    seen.add(var)
            cnf.append(clause)
        return cnf

    def run_all(self) -> dict:
        """运行所有基准"""
        return {
            'n_queens': self.benchmark_n_queens([4, 8]),
            'sudoku': self.benchmark_sudoku(),
            'random_easy': self.benchmark_random(20, 80),
        }


def simple_solver(cnf: List[List[int]]):
    """简单测试求解器"""
    from dpll_solver import DPLLSolver
    solver = DPLLSolver(cnf)
    return solver.solve()


def example_benchmark():
    """基准测试示例"""
    benchmark = SATBenchmark(simple_solver)
    
    print("运行基准测试...")
    results = benchmark.run_all()
    
    print("\n结果:")
    for key, val in results.items():
        print(f"  {key}: {val}")


if __name__ == "__main__":
    print("=" * 50)
    print("SAT基准测试")
    print("=" * 50)
    example_benchmark()
