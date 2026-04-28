"""
Bounded Model Checking (BMC) 限界模型检查器
=============================================
核心思想：将时序逻辑验证问题转换为命题SAT问题
通过展开有限步数的状态转移，检测反例路径

算法步骤：
1. 展开：从初始状态展开k步转移
2. 编码：将状态转移系统编码为CNF公式
3. 求解：使用SAT求解器检查路径存在性
4. 增长：逐步增加k直到找到反例或证明无反例

应用场景：硬件模型检验、协议验证、嵌入式系统
"""

from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TransitionSystem:
    """
    状态转移系统定义
    - state_vars: 状态变量集合
    - init_states: 初始状态谓词
    - trans_relation: 转移关系谓词
    - atomic_props: 原子命题集合
    """
    state_vars: Set[str]                          # 状态变量集合
    init_states: str                              # 初始状态公式
    trans_relation: str                           # 转移关系公式
    atomic_props: Set[str]                        # 原子命题集合


@dataclass
class BmcResult:
    """BMC验证结果"""
    is_cex: bool                                  # 是否找到反例
    counterexample: Optional[List[Dict]]          # 反例路径（状态序列）
    max_depth: int                                # 检查的最大深度
    sat_assignment: Optional[Dict]                # SAT求解结果


def encode_state_var(var_name: str, time_step: int) -> str:
    """
    对状态变量进行时间展开编码
    将变量v在时刻t编码为v_t形式
    
    Args:
        var_name: 变量名，如 "x"
        time_step: 时间步，如 0,1,2,...
    
    Returns:
        编码后的变量名，如 "x_0"
    """
    return f"{var_name}_{time_step}"


def build_unrolling_formula(
    system: TransitionSystem,
    target_prop: str,
    bound: int
) -> Tuple[str, Set[str]]:
    """
    构建展开的BMC公式
    整体公式: I(s_0) ∧ T(s_0,s_1) ∧ ... ∧ T(s_{k-1},s_k) ∧ (¬P(s_k) ∨ Q(s_k,...))
    
    Args:
        system: 转移系统
        target_prop: 要验证的目标性质（支持AG/AF/AF等路径量词）
        bound: 展开深度k
    
    Returns:
        (编码后的CNF字符串, 使用的变量集合)
    """
    clauses = []                                  # 合取范式子句列表
    var_pool = set()                              # 变量池
    
    # Step 1: 编码初始状态约束 I(s_0)
    for var in system.state_vars:
        encoded = encode_state_var(var, 0)        # 编码变量名 v_0
        var_pool.add(encoded)
    
    clauses.append(f"I({encode_state_var('s', 0)})")  # 初始条件
    
    # Step 2: 编码转移关系 T(s_i, s_{i+1}) for i in [0, k-1]
    for step in range(bound):
        clauses.append(f"T({encode_state_var('s', step)}, {encode_state_var('s', step+1)})")
    
    # Step 3: 编码目标属性
    # AF p: 存在一条路径，所有状态都满足p
    # 翻译为: 存在k使得 s_k 满足 p 且路径可达
    if target_prop.startswith("AF"):
        prop_var = target_prop[2:].strip("() ")
        final_var = encode_state_var(prop_var, bound)
        clauses.append(f"P({final_var})")
    
    return " ∧ ".join(f"({c})" for c in clauses), var_pool


def encode_transition_binary(bit_width: int) -> List[str]:
    """
    编码二元转移系统（两个状态的转移）
    生成转移关系的CNF编码
    
    Args:
        bit_width: 状态编码位数
    
    Returns:
        CNF子句列表
    """
    clauses = []
    s_vars = [f"s_{i}" for i in range(bit_width)]    # 当前状态变量
    sp_vars = [f"s'_{i}" for i in range(bit_width)]   # 下一状态变量
    
    # 简单编码：next_state = current_state XOR 1 (翻转)
    for i in range(bit_width):
        # s_i' = ¬s_i (翻转)
        clauses.append(f"(¬{s_vars[i]} ∨ {sp_vars[i]})")  # ¬s_i ∨ s_i'
        clauses.append(f"({s_vars[i]} ∨ ¬{sp_vars[i]})")  # s_i ∨ ¬s_i'
    
    return clauses


def sat_check(formula: str, var_count: int) -> Tuple[bool, Optional[Dict]]:
    """
    简化的SAT检查（模拟实现）
    实际应用中应调用真实SAT求解器如z3/pysat
    
    Args:
        formula: CNF公式字符串
        var_count: 变量数量
    
    Returns:
        (可满足性, 变量赋值字典)
    """
    # 模拟SAT求解：检测特定模式
    if "∧" in formula and "∨" in formula:
        # 简单启发式：如果存在矛盾模式则不可满足
        if formula.count("¬") > var_count * 2:
            return False, None
        else:
            # 返回一个随机赋值作为示例
            assignment = {f"x_{i}": (i % 2 == 0) for i in range(var_count)}
            return True, assignment
    return False, None


def bounded_model_check(
    system: TransitionSystem,
    property_formula: str,
    max_bound: int = 10,
    target_prop: str = "AF(p)"
) -> BmcResult:
    """
    限界模型检查主算法
    
    Args:
        system: 状态转移系统
        property_formula: 待验证LTL/CTL性质
        max_bound: 最大展开深度
        target_prop: 目标属性表达式
    
    Returns:
        BmcResult: 包含反例路径或验证成功标志
    """
    print(f"[BMC] 验证属性: {target_prop}")
    print(f"[BMC] 最大深度: {max_bound}")
    
    for k in range(1, max_bound + 1):
        print(f"[BMC] 展开深度 k={k}...")
        
        # Step 1: 构建展开公式
        unrolled_formula, var_pool = build_unrolling_formula(system, target_prop, k)
        var_count = len(var_pool)
        
        # Step 2: 调用SAT求解
        is_sat, assignment = sat_check(unrolled_formula, var_count)
        
        if is_sat:
            # 找到反例路径
            print(f"[BMC] ✓ 发现反例（深度={k}）")
            
            # 从赋值中提取状态序列
            counterexample = []
            for step in range(k + 1):
                state = {}
                for var in system.state_vars:
                    key = encode_state_var(var, step)
                    state[var] = assignment.get(key, False)
                counterexample.append(state)
            
            return BmcResult(
                is_cex=True,
                counterexample=counterexample,
                max_depth=k,
                sat_assignment=assignment
            )
    
    # 所有深度都检查完，未找到反例
    print(f"[BMC] ✓ 未找到反例（深度1-{max_bound}内）")
    return BmcResult(
        is_cex=False,
        counterexample=None,
        max_depth=max_bound,
        sat_assignment=None
    )


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    # 构建一个简单的二进制计数器系统
    test_system = TransitionSystem(
        state_vars={"x", "y"},                   # 两个状态变量
        init_states="x=0 ∧ y=0",                  # 初始状态 (0,0)
        trans_relation="x'=(x+1) mod 2 ∧ y'=(y+1) mod 2",  # 翻转转移
        atomic_props={"p", "q"}
    )
    
    print("=" * 50)
    print("Bounded Model Checking 测试")
    print("=" * 50)
    
    # 测试1: 验证 AF(p) 属性
    result = bounded_model_check(
        system=test_system,
        property_formula="AF p",
        max_bound=5,
        target_prop="AF(p)"
    )
    
    print(f"\n结果: {'找到反例' if result.is_cex else '验证通过'}")
    if result.counterexample:
        print("反例路径:")
        for i, state in enumerate(result.counterexample):
            print(f"  状态 {i}: x={state['x']}, y={state['y']}")
    
    # 测试2: 编码验证
    print("\n" + "=" * 50)
    unrolled, vars_used = build_unrolling_formula(test_system, "AF(p)", 3)
    print(f"展开公式(深度3): {unrolled}")
    print(f"变量集合: {vars_used}")
