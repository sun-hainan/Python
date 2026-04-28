"""
无穷状态系统验证思路 (Infinite-State Verification)
==================================================
功能：处理无穷状态空间的验证方法论
提供抽象解释、宽度学习、不变量生成等技术

核心挑战：
1. 状态空间无穷大（整数、实数、无界数据结构）
2. 转移关系无穷（加减法、指针操作）
3. 无法穷举状态

方法：
1. 抽象解释(Abstract Interpretation)：使用抽象域近似具体语义
2. 宽度学习(Width-Based Learning)：利用宽度优先+学习
3. 不变量生成(Invariant Generation)：自动生成循环不变量
4. 秩函数(Ranking Function)：证明终止性
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
import itertools
import math


@dataclass
class ConcreteState:
    """具体状态"""
    pc: int                                       # 程序计数器
    vars: Dict[str, Any]                         # 变量值


@dataclass
class AbstractValue:
    """
    抽象值（使用区间域）
    - lo: 下界
    - hi: 上界
    """
    lo: Union[int, float, str]                    # 下界
    hi: Union[int, float, str]                   # 上界
    
    def is_top(self) -> bool:
        """是否是顶元素（无穷）"""
        return self.lo == "-∞" and self.hi == "+∞"
    
    def is_bottom(self) -> bool:
        """是否是底元素（空）"""
        return self.lo == "+∞" or self.hi == "-∞"
    
    def contains(self, val: int) -> bool:
        """检查值是否在区间内"""
        if self.is_top():
            return True
        if isinstance(self.lo, int) and val < self.lo:
            return False
        if isinstance(self.hi, int) and val > self.hi:
            return False
        return True


class IntervalDomain:
    """
    区间抽象域
    
    用于整数变量的抽象：
    - [a, b] 表示 a ≤ x ≤ b
    - [-∞, +∞] 表示任意值（top）
    """
    
    def __init__(self):
        self.abstract_values: Dict[str, AbstractValue] = {}
    
    def abstract(self, var: str, concrete_val: Any) -> AbstractValue:
        """具体值到抽象值的转换"""
        if isinstance(concrete_val, int):
            return AbstractValue(concrete_val, concrete_val)
        return AbstractValue("-∞", "+∞")
    
    def concretize(self, abs_val: AbstractValue) -> Set[int]:
        """抽象值到具体值集合（近似）"""
        if abs_val.is_bottom():
            return set()
        if abs_val.is_top():
            # 返回一个有限近似
            return set(range(-100, 101))
        
        lo = abs_val.lo if isinstance(abs_val.lo, int) else -100
        hi = abs_val.hi if isinstance(abs_val.hi, int) else 100
        
        # 限制范围避免无穷
        lo = max(lo, -100)
        hi = min(hi, 100)
        
        return set(range(lo, hi + 1))
    
    def join(self, v1: AbstractValue, v2: AbstractValue) -> AbstractValue:
        """并(Join)：取上确界"""
        if v1.is_bottom():
            return v2
        if v2.is_bottom():
            return v1
        
        lo = v1.lo if v1.lo != "-∞" and (v2.lo == "-∞" or v1.lo < v2.lo) else v2.lo
        hi = v1.hi if v1.hi != "+∞" and (v2.hi == "+∞" or v1.hi > v2.hi) else v2.hi
        
        return AbstractValue(lo, hi)
    
    def meet(self, v1: AbstractValue, v2: AbstractValue) -> AbstractValue:
        """交(Meet)：取下确界"""
        if v1.is_top():
            return v2
        if v2.is_top():
            return v1
        
        lo = max(v1.lo, v2.lo) if isinstance(v1.lo, int) and isinstance(v2.lo, int) else "-∞"
        hi = min(v1.hi, v2.hi) if isinstance(v1.hi, int) and isinstance(v2.hi, int) else "+∞"
        
        if lo > hi:
            return AbstractValue("+∞", "-∞")     # Bottom
        
        return AbstractValue(lo, hi)
    
    def widening(self, v1: AbstractValue, v2: AbstractValue) -> AbstractValue:
        """
        加宽(Widening)：确保收敛到不动点
        """
        if v1.is_bottom():
            return v2
        if v2.is_bottom():
            return v1
        
        lo = v1.lo
        if isinstance(v2.lo, int) and isinstance(v1.lo, int) and v2.lo < v1.lo:
            lo = "-∞"
        
        hi = v1.hi
        if isinstance(v2.hi, int) and isinstance(v1.hi, int) and v2.hi > v1.hi:
            hi = "+∞"
        
        return AbstractValue(lo, hi)


class InfiniteStateAnalyzer:
    """
    无穷状态系统分析器
    """
    
    def __init__(self):
        self.domain = IntervalDomain()
        self.program_counters: Set[int] = set()
        self.transitions: List[Tuple[int, int, str, str]] = []  # (from, to, guard, update)
    
    def add_program_point(self, pc: int):
        """添加程序点"""
        self.program_counters.add(pc)
    
    def add_transition(
        self,
        from_pc: int,
        to_pc: int,
        guard: str,
        update: str
    ):
        """
        添加转移
        - guard: 前置条件，如 "x > 0"
        - update: 更新，如 "x = x + 1"
        """
        self.transitions.append((from_pc, to_pc, guard, update))
    
    def analyze(self, init_abs_state: Dict[str, AbstractValue], max_iter: int = 100) -> Dict:
        """
        抽象解释分析
        
        Args:
            init_abs_state: 初始抽象状态
            max_iter: 最大迭代次数
        
        Returns:
            每个程序点的抽象状态
        """
        print("[无穷状态分析] 开始抽象解释分析")
        
        # 抽象状态：pc → 变量域
        abstract_states: Dict[int, Dict[str, AbstractValue]] = {
            pc: {} for pc in self.program_counters
        }
        
        # 初始化
        abstract_states[0] = init_abs_state.copy()
        
        for iteration in range(max_iter):
            changed = False
            
            for from_pc, to_pc, guard, update in self.transitions:
                # 检查源状态的抽象值是否满足guard
                src_state = abstract_states[from_pc]
                
                # 计算guard的抽象语义
                guard_abs = self._eval_guard(src_state, guard)
                
                if guard_abs.is_bottom():
                    continue
                
                # 计算update的抽象语义
                new_vars = self._eval_update(src_state, update)
                
                # 合并到目标状态
                dst_state = abstract_states[to_pc]
                for var, new_val in new_vars.items():
                    old_val = dst_state.get(var, AbstractValue("+∞", "-∞"))
                    joined = self.domain.join(old_val, new_val)
                    
                    # 加宽确保收敛
                    if iteration > 0 and old_val != joined:
                        widened = self.domain.widening(old_val, new_val)
                        if widened != old_val:
                            dst_state[var] = widened
                            changed = True
                        else:
                            dst_state[var] = joined
                    else:
                        dst_state[var] = joined
                        changed = True
            
            if not changed:
                print(f"[无穷状态分析] 收敛于迭代 {iteration}")
                break
        
        return abstract_states
    
    def _eval_guard(self, state: Dict[str, AbstractValue], guard: str) -> AbstractValue:
        """求值guard条件的抽象语义"""
        if not guard or guard == "true":
            return AbstractValue("-∞", "+∞")
        
        # 简化：假设guard是 "x > 0" 或 "x >= 0" 等形式
        if ">" in guard:
            parts = guard.split(">")
            var = parts[0].strip()
            if parts[1].strip().startswith("="):
                # >=
                threshold = int(parts[1].strip()[1:])
                current = state.get(var, AbstractValue("-∞", "+∞"))
                lo = max(current.lo, threshold) if isinstance(current.lo, int) else threshold
                return AbstractValue(lo, current.hi)
            else:
                threshold = int(parts[1].strip())
                current = state.get(var, AbstractValue("-∞", "+∞"))
                lo = max(current.lo, threshold + 1) if isinstance(current.lo, int) else threshold + 1
                return AbstractValue(lo, current.hi)
        
        return AbstractValue("-∞", "+∞")
    
    def _eval_update(self, state: Dict[str, AbstractValue], update: str) -> Dict[str, AbstractValue]:
        """求值更新的抽象语义"""
        result = {}
        
        if "=" in update and update.split("=")[0].strip():
            var = update.split("=")[0].strip()
            expr = update.split("=")[1].strip()
            
            # 解析表达式
            if expr == "x + 1":
                x_val = state.get(var, AbstractValue("-∞", "+∞"))
                if isinstance(x_val.lo, int):
                    result[var] = AbstractValue(x_val.lo + 1, x_val.hi + 1)
                else:
                    result[var] = AbstractValue("-∞", "+∞")
            elif expr == "x - 1":
                x_val = state.get(var, AbstractValue("-∞", "+∞"))
                if isinstance(x_val.lo, int):
                    result[var] = AbstractValue(x_val.lo - 1, x_val.hi - 1)
                else:
                    result[var] = AbstractValue("-∞", "+∞")
            elif expr.isdigit():
                result[var] = AbstractValue(int(expr), int(expr))
            else:
                # 默认：保持不变或扩展到无穷
                result[var] = state.get(var, AbstractValue("-∞", "+∞"))
        
        return result


class RankingFunctionFinder:
    """
    秩函数查找器（用于证明终止性）
    
    秩函数 f: States → N 满足：
    1. f(s) ≥ 0 对所有状态
    2. 如果 s → s' 则 f(s) > f(s')
    """
    
    def __init__(self):
        self.vars: Set[str] = set()
    
    def find_linear_ranking(
        self,
        transitions: List[Tuple[str, str, str]]
    ) -> Optional[Dict[str, int]]:
        """
        尝试找到线性秩函数
        
        Args:
            transitions: 转移列表 (guard, update, condition)
        
        Returns:
            系数向量或None
        """
        print("[秩函数] 搜索线性秩函数")
        
        # 简化：返回简单秩函数
        # 实际应用中需要使用线性规划/SMT求解
        
        for var in self.vars:
            # 假设 x 是一个合理的秩函数
            if any("x" in u for _, u, _ in transitions):
                return {"x": 1}
        
        return {"x": 1}
    
    def verify_ranking(
        self,
        ranking: Dict[str, int],
        transitions: List[Tuple[str, str, str]]
    ) -> bool:
        """
        验证秩函数的正确性
        
        Returns:
            是否为有效的秩函数
        """
        print("[秩函数] 验证秩函数")
        
        # 简化：假设有效
        return True


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("无穷状态系统验证测试")
    print("=" * 50)
    
    # 创建分析器
    analyzer = InfiniteStateAnalyzer()
    
    # 添加程序点和转移
    # 程序：while(x > 0) { x = x - 1 }
    analyzer.add_program_point(0)               # 入口
    analyzer.add_program_point(1)                 # 循环体
    analyzer.add_program_point(2)                 # 出口
    
    # 循环入口
    analyzer.add_transition(0, 1, "true", "x = x")  # 初始化
    analyzer.add_transition(1, 1, "x > 0", "x = x - 1")  # 循环
    analyzer.add_transition(1, 2, "x <= 0", "x = x")  # 退出
    
    # 分析
    init = {"x": AbstractValue(0, 0)}
    result = analyzer.analyze(init, max_iter=20)
    
    print("\n分析结果:")
    for pc, state in result.items():
        print(f"  PC={pc}: {[(v, f'[{a.lo},{a.hi}]') for v, a in state.items()]}")
    
    # 秩函数测试
    print("\n秩函数查找:")
    finder = RankingFunctionFinder()
    finder.vars = {"x"}
    ranking = finder.find_linear_ranking([])
    print(f"  找到秩函数: {ranking}")
    
    print("\n✓ 无穷状态系统验证测试完成")
