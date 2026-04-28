# -*- coding: utf-8 -*-
"""
伪布尔约束求解（Pseudo-Boolean Solving）
功能：处理带系数的布尔约束（CNF的泛化）

伪布尔约束格式：
Σ(ai * li) ≥ k  （至少k个文字为真）
Σ(ai * li) = k  （恰好k个文字为真）

当所有系数ai=1时，退化为基数约束（AtMostK, AtLeastK, ExactlyK）

方法：
1. 编码为CNF：使用加法器电路或序贯编码
2. 直接求解：推广的DPLL/CDCL，支持计数传播

作者：Pseudo-Boolean Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class PseudoBooleanConstraint:
    """伪布尔约束"""
    
    def __init__(self, terms: List[Tuple[int, int]], rel: str, rhs: int):
        """
        Args:
            terms: [(coeff1, lit1), (coeff2, lit2), ...]
            rel: '>=', '=', '<='
            rhs: 右端常数
        """
        self.terms = terms  # 文字及其系数
        self.rel = rel
        self.rhs = rhs
    
    def __repr__(self):
        terms_str = " + ".join(f"{a}*{l}" for a, l in self.terms)
        return f"{terms_str} {self.rel} {self.rhs}"


class PBEncoder:
    """伪布尔约束编码器：转换为CNF"""

    def __init__(self):
        self.cnf: List[List[int]] = []
        self.next_var = 1

    def new_var(self) -> int:
        var = self.next_var
        self.next_var += 1
        return var

    def add_clause(self, lits: List[int]):
        self.cnf.append(lits)

    def encode_at_most_k(self, lits: List[int], k: int):
        """
        编码 AtMostK: 至多k个文字为真
        
        方法：pairwise排除（当k=1时就是AtMostOne）
        """
        if k >= len(lits):
            return
        
        if k == 1:
            # AtMostOne: 所有pairwise互斥
            n = len(lits)
            for i in range(n):
                for j in range(i + 1, n):
                    self.add_clause([-lits[i], -lits[j]])
        else:
            # 通用方法：加法器编码
            self._sequential_counter(lits, k)

    def _sequential_counter(self, lits: List[int], k: int):
        """
        序贯计数器编码
        
        将累加器逐比特进位，限制总和小于等于k
        """
        n = len(lits)
        
        # 每行一个计数器，进位逐步传递
        # carry[i][b] = 第i个输入后，第b位的进位
        carries = []
        
        prev_carries = []
        for b in range(n.bit_length()):
            prev_carries.append(self.new_var())
        
        for i, lit in enumerate(lits):
            # 计算新的进位
            new_carries = []
            total = 1 if i > 0 else 0  # 输入值 + 之前进位
            
            for b in range(len(prev_carries)):
                bit_val = (total >> b) & 1
                if bit_val == 0:
                    # 需要新的辅助变量
                    carry_var = self.new_var()
                else:
                    carry_var = prev_carries[b]
                new_carries.append(carry_var)
            
            carries.append(new_carries)
        
        # 最终进位必须为0（约束总和不超过k）
        for carry in carries[-1]:
            self.add_clause([-carry])

    def encode_exactly_k(self, lits: List[int], k: int):
        """ExactlyK: 编码为 AtMostK ∧ AtLeastK"""
        n = len(lits)
        self.encode_at_most_k(lits, k)
        # AtLeastK: 使用否定形式
        neg_lits = [-lit for lit in lits]
        self.encode_at_most_k(neg_lits, n - k)

    def encode_pb(self, pb: PseudoBooleanConstraint) -> List[List[int]]:
        """
        将伪布尔约束编码为CNF
        
        使用排序网络方法
        """
        terms = pb.terms
        k = pb.rhs
        
        if pb.rel == '>=':
            # Σ ai*li >= k 等价于 Σ ai*li <= sum-k 对否定文字
            neg_terms = [(-ai, -lit) for ai, lit in terms]
            neg_pb = PseudoBooleanConstraint(neg_terms, '<=', sum(ai for ai, _ in terms) - k)
            return self._encode_le(neg_pb)
        
        return []

    def _encode_le(self, pb: PseudoBooleanConstraint) -> List[List[int]]:
        """编码小于等于约束"""
        # 简化：仅处理单位系数
        if all(ai == 1 for ai, _ in pb.terms):
            lits = [lit for _, lit in pb.terms]
            self.encode_at_most_k(lits, pb.rhs)
            return self.cnf
        return []


class PBSolver:
    """
    伪布尔求解器（直接法）
    
    使用推广的BCP（布尔约束传播）+ 计数传播
    """

    def __init__(self, constraints: List[PseudoBooleanConstraint]):
        self.constraints = constraints
        self.assignment: Dict[int, bool] = {}
        self.n_vars = self._count_vars()

    def _count_vars(self) -> int:
        max_var = 0
        for c in self.constraints:
            for _, lit in c.terms:
                max_var = max(max_var, abs(lit))
        return max_var

    def _eval_constraint(self, c: PseudoBooleanConstraint) -> Optional[int]:
        """
        求值伪布尔约束
        
        Returns:
            >0: 约束已满足（多余量为满足度）
            =0: 约束恰好满足
            <0: 约束违反（负值表示违反量）
            None: 有未赋值变量
        """
        total = 0
        has_unassigned = False
        
        for coeff, lit in c.terms:
            var = abs(lit)
            if var not in self.assignment:
                has_unassigned = True
                continue
            
            val = self.assignment[var]
            if (lit > 0 and val) or (lit < 0 and not val):
                total += coeff
        
        if has_unassigned:
            return None
        
        if c.rel == '>=':
            return total - c.rhs
        elif c.rel == '==':
            return -(abs(total - c.rhs))
        elif c.rel == '<=':
            return c.rhs - total
        
        return None

    def _find_unit(self, c: PseudoBooleanConstraint) -> Optional[int]:
        """
        检测单元伪布尔约束
        
        若约束仅剩1个未赋值文字，返回该文字（必须设为真）
        """
        unassigned = []
        for coeff, lit in c.terms:
            var = abs(lit)
            if var not in self.assignment:
                unassigned.append((coeff, lit))
        
        if len(unassigned) == 1:
            coeff, lit = unassigned[0]
            var = abs(lit)
            
            # 计算其他已赋值部分的总和
            sum_assigned = 0
            for c2, l in c.terms:
                v = abs(l)
                if v in self.assignment:
                    if (l > 0 and self.assignment[v]) or (l < 0 and not self.assignment[v]):
                        sum_assigned += c2
            
            if c.rel == '>=':
                needed = c.rhs - sum_assigned
                if needed <= 0:
                    return None
                if coeff >= needed:
                    return lit if lit > 0 else lit
        
        return None

    def solve(self) -> Optional[Dict[int, bool]]:
        """求解"""
        return self._dpll_pb()

    def _dpll_pb(self) -> Optional[Dict[int, bool]]:
        """DPLL for PB"""
        # 传播
        while True:
            made_progress = False
            
            for c in self.constraints:
                eval_result = self._eval_constraint(c)
                
                if eval_result is not None and eval_result < 0:
                    return None  # 冲突
                
                if eval_result is not None and eval_result >= 0:
                    # 约束已满足
                    continue
                
                # 检查单元
                unit_lit = self._find_unit(c)
                if unit_lit is not None:
                    var = abs(unit_lit)
                    val = unit_lit > 0
                    if var not in self.assignment:
                        self.assignment[var] = val
                        made_progress = True
                    elif self.assignment[var] != val:
                        return None
            
            if not made_progress:
                break
        
        # 检查是否完成
        if len(self.assignment) == self.n_vars:
            return self.assignment
        
        # 选择未赋值变量
        var = next(v for v in range(1, self.n_vars + 1) if v not in self.assignment)
        
        # 尝试True
        self.assignment[var] = True
        result = self._dpll_pb()
        if result is not None:
            return result
        
        # 尝试False
        self.assignment[var] = False
        return self._dpll_pb()


def example_at_most_k():
    """AtMostK编码示例"""
    encoder = PBEncoder()
    
    lits = [1, 2, 3, 4]
    encoder.encode_at_most_k(lits, 2)
    
    print(f"AtMost(2): {len(encoder.cnf)} 子句")
    for clause in encoder.cnf[:5]:
        print(f"  {clause}")

    from dpll_solver import DPLLSolver
    solver = DPLLSolver(encoder.cnf)
    result = solver.solve()
    print(f"SAT: {'是' if result else '否'}")


def example_exactly_k():
    """ExactlyK编码示例"""
    encoder = PBEncoder()
    
    lits = [1, 2, 3]
    encoder.encode_exactly_k(lits, 2)
    
    print(f"Exactly(2): {len(encoder.cnf)} 子句")
    
    from dpll_solver import DPLLSolver
    solver = DPLLSolver(encoder.cnf)
    result = solver.solve()
    print(f"SAT: {'是' if result else '否'}")


def example_pb_solver():
    """PB求解器示例"""
    constraints = [
        PseudoBooleanConstraint([(1, 1), (1, 2), (1, 3)], '>=', 2),  # x1+x2+x3 >= 2
        PseudoBooleanConstraint([(1, 2), (1, 3), (1, 4)], '>=', 2),  # x2+x3+x4 >= 2
    ]
    
    solver = PBSolver(constraints)
    result = solver.solve()
    print(f"PB求解: {'SAT' if result else 'UNSAT'}")
    if result:
        print(f"  解: {result}")


if __name__ == "__main__":
    print("=" * 50)
    print("伪布尔约束求解器 测试")
    print("=" * 50)
    
    example_at_most_k()
    print()
    example_exactly_k()
    print()
    example_pb_solver()
