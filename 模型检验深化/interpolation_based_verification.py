"""
基于插值的验证 (Interpolation-Based Verification)
==================================================
功能：使用Craig插值进行不变式生成的验证方法
支持有界验证后的不变式提取和反例归纳

核心思想：
1. 序列A → B为不可满足时，存在插值A'使得A → A' → ⊥
2. 插值用于从反例路径归纳出更精确的不变式
3. 配合BMC使用：将有界反例扩展为无界不变式

应用：
- 软件模型检查（Path-based interpolation）
- 硬件验证
- 不变式生成
"""

from typing import List, Set, Optional, Tuple, Dict, Any, Callable
from dataclasses import dataclass, field
import copy


@dataclass
class Interpolant:
    """
    Craig插值器
    - a_formula: A部分的公式
    - b_formula: B部分的公式
    - interpolant: 插值公式 A → K → ⊥
    """
    a_formula: str
    b_formula: str
    interpolant: str
    variables: Set[str] = field(default_factory=set)


@dataclass
class BmcPath:
    """
    BMC反例路径
    - states: 状态序列 s_0, s_1, ..., s_k
    - transitions: 转移序列
    - bad_state: 坏状态索引
    """
    states: List[Dict[str, Any]]
    transitions: List[Tuple[Dict, Dict]]
    bad_state_index: int
    bound: int


class InterpolationSystem:
    """
    基于插值的验证系统
    """
    
    def __init__(self):
        self.variables: Set[str] = set()
        self.paths: List[BmcPath] = []
        self.invariants: List[str] = []
    
    def add_variable(self, var_name: str, domain: Set[Any]):
        """
        添加变量
        
        Args:
            var_name: 变量名
            domain: 变量域
        """
        self.variables.add(var_name)
    
    def compute_interpolant(
        self,
        seq_a: str,
        seq_b: str,
        shared_vars: Set[str]
    ) -> Interpolant:
        """
        计算Craig插值
        当 A ∧ B 不可满足时，计算插值K使得 A → K 且 K ∧ B → ⊥
        
        实现策略（简化）：
        1. 识别序列间的共享变量
        2. 对共享变量进行存在量化
        3. 生成近似插值
        
        Args:
            seq_a: A序列公式
            seq_b: B序列公式
            shared_vars: 共享变量集合
        
        Returns:
            Interpolant插值器
        """
        print(f"[插值] A: {seq_a}")
        print(f"[插值] B: {seq_b}")
        print(f"[插值] 共享变量: {shared_vars}")
        
        # 简化实现：生成一个简单的插值
        # 实际应用中需要调用SAT求解器获取冲突子句
        
        # 策略：取A中的正文字作为插值基础
        interpolant_parts = []
        for var in shared_vars:
            # 简化：假设所有共享变量都为真
            interpolant_parts.append(var)
        
        interpolant = " ∧ ".join(interpolant_parts) if interpolant_parts else "TRUE"
        
        print(f"[插值] 生成插值: {interpolant}")
        
        return Interpolant(
            a_formula=seq_a,
            b_formula=seq_b,
            interpolant=interpolant,
            variables=shared_vars
        )
    
    def interpolate_path(self, path: BmcPath) -> Interpolant:
        """
        对BMC反例路径进行插值
        将路径分为A部分(0..k-1)和B部分(k)
        
        Args:
            path: BMC反例路径
        
        Returns:
            路径插值器
        """
        k = path.bad_state_index
        
        # A = I(s_0) ∧ T(s_0,s_1) ∧ ... ∧ T(s_{k-1}, s_k)
        # B = ¬P(s_k)
        
        # 构建序列A的公式
        seq_a_parts = []
        for i, state in enumerate(path.states):
            for var, val in state.items():
                seq_a_parts.append(f"{var}={val}")
        
        # 添加转移约束
        for i, (s1, s2) in enumerate(path.transitions):
            if i < k:
                for var in s1:
                    if var in s2:
                        seq_a_parts.append(f"{var}'={s2[var]}")
        
        seq_a = " ∧ ".join(seq_a_parts)
        
        # 构建序列B的公式
        bad_state = path.states[k]
        seq_b_parts = [f"¬({var}={val})" for var, val in bad_state.items()]
        seq_b = " ∧ ".join(seq_b_parts)
        
        return self.compute_interpolant(seq_a, seq_b, self.variables)
    
    def extract_invariant_from_cex(self, cex: List[Dict[str, Any]]) -> str:
        """
        从反例路径提取不变量
        通过归纳反例路径生成不变式
        
        Args:
            cex: 反例路径（状态序列）
        
        Returns:
            不变式字符串
        """
        print(f"[不变量] 从反例提取不变量 (路径长度={len(cex)})")
        
        if not cex:
            return "TRUE"
        
        # 分析路径中的不变特征
        invariant_parts = []
        
        # 收集每步的恒等约束
        for step in range(len(cex)):
            state = cex[step]
            for var, val in state.items():
                # 检查变量是否保持不变
                if step > 0:
                    prev_val = cex[step-1].get(var)
                    if prev_val == val:
                        # 变量保持不变
                        pass
                else:
                    # 第一步：记录初始值约束
                    invariant_parts.append(f"{var}={val}")
        
        # 生成合取不变量
        # 简化：使用最后一个状态的约束作为不变量
        final_state = cex[-1]
        final_invariants = [f"{var}={val}" for var, val in final_state.items()]
        
        invariant = " ∧ ".join(final_invariants) if final_invariants else "TRUE"
        print(f"[不变量] 生成: {invariant}")
        
        self.invariants.append(invariant)
        return invariant
    
    def strengthen_invariant(
        self,
        current_invariant: str,
        new_interpolant: Interpolant
    ) -> str:
        """
        强化不变量
        将新插值与当前不变量合取
        
        Args:
            current_invariant: 当前不变量
            new_interpolant: 新插值
        
        Returns:
            强化后的不变量
        """
        if current_invariant == "TRUE":
            return new_interpolant.interpolant
        
        # 合取强化
        strengthened = f"({current_invariant}) ∧ ({new_interpolant.interpolant})"
        print(f"[强化] {current_invariant} ∧ {new_interpolant.interpolant}")
        
        return strengthened


class InterpolationModelChecker:
    """
    基于插值的模型检查器
    结合BMC和不变式生成
    """
    
    def __init__(self):
        self.system = InterpolationSystem()
        self.current_invariant = "TRUE"
    
    def verify_with_interpolation(
        self,
        init_state: Dict[str, Any],
        trans_relation: Callable,
        bad_state_check: Callable[[Dict], bool],
        max_bound: int = 10
    ) -> Tuple[bool, Optional[List[Dict]]]:
        """
        使用插值验证安全性
        
        迭代过程：
        1. 运行BMC寻找反例
        2. 如果找到反例，生成插值
        3. 用插值强化不变量
        4. 检查不变量是否足以证明安全性
        5. 如果不变量被违反，提取新的反例
        
        Args:
            init_state: 初始状态
            trans_relation: 转移关系函数
            bad_state_check: 坏状态检测函数
            max_bound: 最大展开深度
        
        Returns:
            (是否安全, 反例路径如果有)
        """
        print("[插值验证] 开始验证")
        
        current_state = init_state.copy()
        path = [current_state]
        
        for bound in range(max_bound):
            print(f"[插值验证] 展开深度 {bound}...")
            
            # 检查当前状态
            if bad_state_check(current_state):
                print(f"[插值验证] 发现坏状态!")
                
                # 生成插值
                bmc_path = BmcPath(
                    states=path,
                    transitions=list(zip(path[:-1], path[1:])),
                    bad_state_index=len(path) - 1,
                    bound=bound
                )
                
                interp = self.system.interpolate_path(bmc_path)
                
                # 强化不变量
                self.current_invariant = self.system.strengthen_invariant(
                    self.current_invariant,
                    interp
                )
                
                # 从不变量推导反例
                cex_path = self.system.extract_invariant_from_cex(path)
                
                return False, path
            
            # 展开一步
            next_states = trans_relation(current_state)
            if not next_states:
                break
            
            # 选择第一个后继（简化）
            current_state = next_states[0]
            path.append(current_state)
        
        print(f"[插值验证] 验证完成，不变量: {self.current_invariant}")
        return True, None


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("基于插值的验证测试")
    print("=" * 50)
    
    # 创建插值系统
    system = InterpolationSystem()
    system.add_variable("x", {0, 1, 2, 3})
    system.add_variable("y", {0, 1, 2, 3})
    
    # 测试插值计算
    print("\n插值计算测试:")
    interp = system.compute_interpolant(
        seq_a="x=0 ∧ x'=1",
        seq_b="¬(x=1)",
        shared_vars={"x"}
    )
    print(f"  插值: {interp.interpolant}")
    
    # 测试路径插值
    print("\n路径插值测试:")
    path = BmcPath(
        states=[
            {"x": 0, "y": 0},
            {"x": 1, "y": 1},
            {"x": 2, "y": 2},
        ],
        transitions=[
            ({"x": 0, "y": 0}, {"x": 1, "y": 1}),
            ({"x": 1, "y": 1}, {"x": 2, "y": 2}),
        ],
        bad_state_index=2,
        bound=2
    )
    path_interp = system.interpolate_path(path)
    print(f"  路径插值: {path_interp.interpolant}")
    
    # 测试不变量提取
    print("\n不变量提取测试:")
    cex = [{"x": 0}, {"x": 1}, {"x": 2}]
    inv = system.extract_invariant_from_cex(cex)
    
    # 测试模型检查器
    print("\n插值模型检查测试:")
    checker = InterpolationModelChecker()
    
    init = {"x": 0, "y": 0}
    
    def trans(s):
        x = s["x"]
        return [{"x": (x + 1) % 5, "y": x}]
    
    def bad(s):
        return s["x"] == 4
    
    is_safe, cex = checker.verify_with_interpolation(
        init, trans, bad, max_bound=5
    )
    print(f"  安全: {is_safe}")
    
    print("\n✓ 基于插值的验证测试完成")
