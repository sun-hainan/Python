# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / inlining

本文件实现 inlining 相关的算法功能。
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field

# ========== 调用点信息 ==========

@dataclass
class CallSite:
    """调用点"""
    caller: str               # 调用者函数名
    callee: str               # 被调用函数名
    call_id: int             # 调用点ID
    arguments: List[str] = field(default_factory=list)  # 实参
    return_var: Optional[str] = None  # 返回值变量
    is_recursive: bool = False  # 是否递归调用
    call_depth: int = 0         # 调用深度


@dataclass
class Function:
    """函数信息"""
    name: str
    params: List[str] = field(default_factory=list)
    local_vars: List[str] = field(default_factory=list)
    instructions: List = field(default_factory=list)
    call_sites: List[CallSite] = field(default_factory=list)
    size: int = 0  # 指令数
    is_leaf: bool = False  # 是否叶函数（不调用其他函数）
    
    def estimate_size(self) -> int:
        """估算函数大小"""
        return len(self.instructions)


@dataclass
class CallGraphNode:
    """调用图节点"""
    function: Function
    callers: Set[str] = field(default_factory=set)   # 调用该函数的函数
    callees: Set[str] = field(default_factory=set)  # 该函数调用的函数


class CallGraph:
    """
    调用图
    表示函数间的调用关系
    """
    
    def __init__(self):
        self.nodes: Dict[str, CallGraphNode] = {}
        self.functions: Dict[str, Function] = {}
    
    def add_function(self, func: Function):
        """添加函数"""
        self.functions[func.name] = func
        
        if func.name not in self.nodes:
            self.nodes[func.name] = CallGraphNode(function=func)
    
    def add_call(self, caller: str, callee: str, call_id: int):
        """添加调用边"""
        if caller not in self.nodes:
            self.add_function(Function(name=caller))
        if callee not in self.nodes:
            self.add_function(Function(name=callee))
        
        self.nodes[caller].callees.add(callee)
        self.nodes[callee].callers.add(caller)
    
    def get_callers(self, func_name: str) -> Set[str]:
        """获取调用者"""
        if func_name in self.nodes:
            return self.nodes[func_name].callers
        return set()
    
    def get_callees(self, func_name: str) -> Set[str]:
        """获取被调用者"""
        if func_name in self.nodes:
            return self.nodes[func_name].callees
        return set()
    
    def is_recursive(self, func_name: str) -> bool:
        """检查是否递归"""
        return func_name in self.get_callees(func_name)


# ========== 内联代价模型 ==========

@dataclass
class InlineDecision:
    """内联决策"""
    should_inline: bool
    reason: str
    benefit: float  # 收益估计
    cost: float     # 代价估计


class InlineCostModel:
    """
    内联代价模型
    决定是否应该内联一个函数调用
    """
    
    def __init__(self):
        # 阈值参数
        self.max_size = 50           # 最大内联大小（指令数）
        self.max_depth = 10          # 最大内联深度
        self.hotness_threshold = 0.8 # 热度阈值
        
        # 收益权重
        self.elimination_benefit = 1.0    # 调用消除收益
        self.constant_prop_benefit = 0.5   # 常量传播收益
        self.loop_benefit = 2.0            # 循环展开收益
        
        # 代价权重
        self.code_growth_cost = 0.3       # 代码膨胀代价
        self.compile_time_cost = 0.1       # 编译时间代价
    
    def should_inline(self, call_site: CallSite, caller_func: Function,
                     callee_func: Function, call_count: float) -> InlineDecision:
        """
        决定是否内联
        """
        # 检查基本条件
        if self._is_recursive(call_site, callee_func):
            return InlineDecision(False, "递归调用不建议内联", 0, 0)
        
        if self._exceeds_size_limit(callee_func):
            return InlineDecision(False, f"函数过大({callee_func.size})", 0, 0)
        
        if self._exceeds_depth_limit(call_site):
            return InlineDecision(False, "内联深度超限", 0, 0)
        
        # 计算代价收益
        benefit = self._compute_benefit(call_site, caller_func, callee_func, call_count)
        cost = self._compute_cost(call_site, caller_func, callee_func)
        
        # 决定
        should_inline = benefit > cost
        
        return InlineDecision(
            should_inline=should_inline,
            reason=f"benefit={benefit:.2f}, cost={cost:.2f}",
            benefit=benefit,
            cost=cost
        )
    
    def _is_recursive(self, call_site: CallSite, callee_func: Function) -> bool:
        """检查是否递归"""
        if call_site.caller == call_site.callee:
            return True
        return callee_func.name in self._get_transitive_callers(call_site.caller)
    
    def _get_transitive_callers(self, func_name: str) -> Set[str]:
        """获取传递调用者"""
        # 简化
        return set()
    
    def _exceeds_size_limit(self, func: Function) -> bool:
        """检查是否超过大小限制"""
        return func.size > self.max_size
    
    def _exceeds_depth_limit(self, call_site: CallSite) -> bool:
        """检查是否超过深度限制"""
        return call_site.call_depth >= self.max_depth
    
    def _compute_benefit(self, call_site: CallSite, caller: Function,
                        callee: Function, call_count: float) -> float:
        """计算内联收益"""
        benefit = 0.0
        
        # 调用消除收益
        benefit += self.elimination_benefit * call_count
        
        # 检查常量实参
        for arg in call_site.arguments:
            if arg.startswith("const_"):
                benefit += self.constant_prop_benefit
        
        # 检查是否是热路径
        if call_count > 100:
            benefit += self.loop_benefit * call_count / 100
        
        return benefit
    
    def _compute_cost(self, call_site: CallSite, caller: Function,
                     callee: Function) -> float:
        """计算内联代价"""
        cost = 0.0
        
        # 代码膨胀代价
        cost += callee.size * self.code_growth_cost
        
        # 编译时间代价
        cost += callee.size * self.compile_time_cost
        
        return cost


# ========== 内联器 ==========

class Inliner:
    """
    内联器
    执行函数内联
    """
    
    def __init__(self, call_graph: CallGraph):
        self.call_graph = call_graph
        self.cost_model = InlineCostModel()
        self.inlined_count = 0
        self.inline_history: List[Tuple[str, str, str]] = []  # (caller, callee, reason)
    
    def inline_all(self, functions: Dict[str, Function], 
                   call_counts: Dict[Tuple[str, str], float]) -> Dict[str, Function]:
        """
        执行所有可以内联的调用
        """
        changed = True
        
        while changed:
            changed = False
            
            for func_name, func in functions.items():
                for call_site in func.call_sites:
                    callee_func = functions.get(call_site.callee)
                    if not callee_func:
                        continue
                    
                    # 获取调用次数
                    call_key = (func_name, call_site.callee)
                    count = call_counts.get(call_key, 1.0)
                    
                    # 决定是否内联
                    decision = self.cost_model.should_inline(
                        call_site, func, callee_func, count
                    )
                    
                    if decision.should_inline:
                        self._inline_call_site(func, call_site, callee_func)
                        self.inlined_count += 1
                        changed = True
        
        return functions
    
    def _inline_call_site(self, caller: Function, call_site: CallSite,
                          callee: Function):
        """内联单个调用点"""
        # 1. 参数映射
        param_map = dict(zip(callee.params, call_site.arguments))
        
        # 2. 复制callee的指令，替换参数
        new_instrs = []
        for instr in callee.instructions:
            new_instr = self._substitute_params(instr, param_map)
            new_instrs.append(new_instr)
        
        # 3. 处理返回值
        if call_site.return_var:
            # 将返回值赋值给返回变量
            pass
        
        # 记录历史
        self.inline_history.append((
            call_site.caller,
            call_site.callee,
            f"depth={call_site.call_depth}"
        ))
    
    def _substitute_params(self, instr, param_map: Dict[str, str]):
        """替换参数"""
        import copy
        new_instr = copy.copy(instr)
        
        if new_instr.arg1 in param_map:
            new_instr.arg1 = param_map[new_instr.arg1]
        if new_instr.arg2 in param_map:
            new_instr.arg2 = param_map[new_instr.arg2]
        
        return new_instr


class HeuristicInliner:
    """
    基于启发式的内联器
    使用简单的规则决定内联
    """
    
    def __init__(self):
        self.small_function_threshold = 10  # 小函数阈值（指令数）
        self.hot_call_threshold = 0.5       # 热调用阈值（相对调用频率）
    
    def should_inline(self, callee: Function, call_count_ratio: float) -> bool:
        """
        使用启发式规则决定是否内联
        """
        # 规则1：小函数总是内联
        if callee.size <= self.small_function_threshold:
            return True
        
        # 规则2：热调用内联
        if call_count_ratio > self.hot_call_threshold:
            return True
        
        # 规则3：叶函数可以内联
        if callee.is_leaf and callee.size <= 20:
            return True
        
        # 规则4：递归不内联
        if callee.name in callee.call_sites:
            return False
        
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("内联展开（Inlining）演示")
    print("=" * 60)
    
    # 构建调用图
    print("\n--- 调用图 ---")
    cg = CallGraph()
    
    cg.add_function(Function(name="main", instructions=[], size=10))
    cg.add_function(Function(name="helper", instructions=[], size=5))
    cg.add_function(Function(name="calc", instructions=[], size=30))
    
    cg.add_call("main", "helper", 1)
    cg.add_call("main", "calc", 2)
    cg.add_call("calc", "helper", 3)
    
    print("调用关系:")
    for func_name, node in cg.nodes.items():
        print(f"  {func_name}: 调用 {node.callees}, 被 {node.callers} 调用")
    
    # 代价模型
    print("\n--- 内联代价模型 ---")
    model = InlineCostModel()
    
    call_site = CallSite(
        caller="main",
        callee="helper",
        call_id=1,
        arguments=["a", "b"],
        call_depth=0
    )
    
    caller_func = Function(name="main", instructions=[], size=10)
    callee_func = Function(name="helper", instructions=[], size=5)
    
    decision = model.should_inline(call_site, caller_func, callee_func, call_count=100)
    
    print(f"内联决策: {decision.should_inline}")
    print(f"原因: {decision.reason}")
    print(f"收益: {decision.benefit:.2f}, 代价: {decision.cost:.2f}")
    
    # 启发式内联
    print("\n--- 启发式内联 ---")
    inliner = HeuristicInliner()
    
    small_func = Function(name="small", instructions=[], size=8)
    large_func = Function(name="large", instructions=[], size=100)
    
    print(f"小函数 (size=8) 是否内联: {inliner.should_inline(small_func, 0.5)}")
    print(f"大函数 (size=100) 是否内联: {inliner.should_inline(large_func, 0.5)}")
    print(f"热调用 (ratio=0.9) 是否内联: {inliner.should_inline(large_func, 0.9)}")
    
    print("\n内联优化要点:")
    print("  1. 消除函数调用开销（栈帧、参数传递）")
    print("  2. 使常量传播更有效")
    print("  3. 暴露更多优化机会")
    print("  4. 避免代码膨胀（内联过大的函数）")
    print("  5. 递归通常不内联（除非有特殊优化如TCO）")
