"""
反例生成与验证 (Counterexample Generation & Validation)
==================================================
功能：为模型检查生成和验证反例
支持有界/无界反例路径、抽象反例验证

核心概念：
1. 反例路径: 违反性质的状态序列
2. 反例验证: 确认反例在具体模型中实际可行
3. 反例抽象: 从具体反例提取抽象模式
4. 反例排序: 按长度/重要性排序反例

反例类型：
- 路径反例: AF/EF性质的违反路径
- 环反例: AG性质的违反（含环路）
- 无限反例: 无穷状态系统的违反
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import deque


@dataclass
class State:
    """状态"""
    id: Any
    label: Set[str] = field(default_factory=set)
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id


@dataclass
class Transition:
    """转移"""
    source: Any
    target: Any
    condition: str = ""
    action: str = ""


@dataclass
class Counterexample:
    """
    反例
    
    - path: 状态路径
    - transitions: 转移序列
    - is_valid: 是否有效（验证通过）
    - is_spurious: 是否虚假
    - path_length: 路径长度
    """
    path: List[State] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)
    is_valid: bool = False
    is_spurious: bool = True
    path_length: int = 0
    verification_info: str = ""
    
    def __str__(self):
        state_ids = [str(s.id) for s in self.path]
        result = f"反例路径: {' → '.join(state_ids)}"
        if self.is_spurious:
            result += " [疑似虚假]"
        elif self.is_valid:
            result += " [已验证]"
        return result


class CounterexampleGenerator:
    """
    反例生成器
    """
    
    def __init__(self, transitions: Dict[Any, Set[Any]]):
        self.transitions = transitions  # state → set of next states
        self.reverse_transitions: Dict[Any, Set[Any]] = {}  # for backward search
    
    def find_path_to_bad(
        self,
        init_states: Set[Any],
        bad_states: Set[Any],
        max_length: int = 20
    ) -> Optional[List[Any]]:
        """
        BFS搜索从初始状态到坏状态的路径
        
        Args:
            init_states: 初始状态集合
            bad_states: 坏状态集合
            max_length: 最大路径长度
        
        Returns:
            路径或None
        """
        print(f"[反例生成] BFS搜索 (max_length={max_length})")
        
        queue = deque()
        for s in init_states:
            queue.append(([s], {s}))  # (path, visited)
        
        for iteration in range(max_length):
            if not queue:
                break
            
            path, visited = queue.popleft()
            current = path[-1]
            
            if current in bad_states:
                print(f"[反例生成] ✓ 找到路径 (长度={len(path)})")
                return path
            
            if len(path) >= max_length:
                continue
            
            for succ in self.transitions.get(current, set()):
                if succ not in visited:
                    new_path = path + [succ]
                    new_visited = visited | {succ}
                    queue.append((new_path, new_visited))
        
        print(f"[反例生成] ✗ 未找到路径")
        return None
    
    def find_loop_counterexample(
        self,
        init_states: Set[Any],
        bad_states: Set[Any]
    ) -> Optional[List[Any]]:
        """
        寻找AG性质的反例（含环路）
        
        AG φ 违反当且仅当存在一条路径可以无限远离φ
        即：存在一条路径反复访问¬φ状态
        
        Returns:
            包含环路的路径
        """
        print(f"[反例生成] 搜索环反例")
        
        # 找到可达的¬φ状态
        non_phi_states = set()
        queue = deque(list(init_states))
        visited = set()
        
        while queue:
            s = queue.popleft()
            if s in visited:
                continue
            visited.add(s)
            
            if s in bad_states:
                non_phi_states.add(s)
            
            for succ in self.transitions.get(s, set()):
                if succ not in visited:
                    queue.append(succ)
        
        # 简化：在坏状态中找环路
        for s in non_phi_states:
            for succ in self.transitions.get(s, set()):
                if succ in non_phi_states:
                    # 找到环路
                    path = [s, succ]
                    print(f"[反例生成] ✓ 找到环: {s} → {succ}")
                    return path
        
        return None
    
    def generate_counterexample(
        self,
        init_states: Set[Any],
        property_type: str,
        bad_states: Set[Any]
    ) -> Optional[Counterexample]:
        """
        生成反例
        
        Args:
            init_states: 初始状态
            property_type: 性质类型 "EF", "AG", etc.
            bad_states: 坏状态集合
        
        Returns:
            Counterexample
        """
        print(f"[反例生成] 生成 {property_type} 反例")
        
        if property_type == "EF":
            # EF φ: 存在路径最终到达φ的补（即¬φ）
            path = self.find_path_to_bad(init_states, bad_states)
            if path:
                states = [State(id=s) for s in path]
                return Counterexample(
                    path=states,
                    path_length=len(path)
                )
        
        elif property_type == "AG":
            # AG φ: 所有路径所有状态满足φ
            # 反例：存在路径可以到达¬φ
            path = self.find_path_to_bad(init_states, bad_states)
            if path:
                states = [State(id=s) for s in path]
                # 检查是否形成环
                loop = self.find_loop_counterexample(init_states, bad_states)
                if loop:
                    return Counterexample(
                        path=states,
                        path_length=len(path)
                    )
        
        return None


class CounterexampleValidator:
    """
    反例验证器
    
    验证反例路径是否在实际模型中可行
    """
    
    def __init__(self, transitions: Dict[Any, Set[Any]]):
        self.transitions = transitions
    
    def validate_path(
        self,
        path: List[Any],
        trans_constraints: Dict[Tuple[Any, Any], str] = None
    ) -> Tuple[bool, str]:
        """
        验证路径可行性
        
        Args:
            path: 状态路径
            trans_constraints: 转移条件映射
        
        Returns:
            (是否有效, 信息)
        """
        if len(path) < 2:
            return True, "路径长度不足"
        
        for i in range(len(path) - 1):
            source, target = path[i], path[i+1]
            
            if target not in self.transitions.get(source, set()):
                return False, f"转移 {source} → {target} 不存在"
        
        return True, "路径有效"
    
    def validate_with_conditions(
        self,
        path: List[Any],
        conditions: List[str]
    ) -> Tuple[bool, str]:
        """
        带条件验证
        
        检查路径是否满足转移条件
        """
        if len(conditions) != len(path) - 1:
            return False, "条件数量与转移数量不匹配"
        
        for i, cond in enumerate(conditions):
            if not cond:
                continue
            
            # 简化：假设条件为真
            # 实际应解析条件表达式
            if "false" in cond.lower():
                return False, f"条件 {cond} 为假"
        
        return True, "条件验证通过"


class CounterexampleAnalyzer:
    """
    反例分析器
    """
    
    def __init__(self):
        self.counterexamples: List[Counterexample] = []
    
    def extract_pattern(self, path: List[Any]) -> str:
        """
        提取反例模式
        
        将具体状态抽象为模式
        例如: s0 → s1 → s2 → ... → sn
              ↓    ↓    ↓
              x=0  x=1  x=2  (提取变化)
        """
        if len(path) <= 1:
            return "空路径"
        
        pattern = []
        for i, s in enumerate(path):
            pattern.append(f"s{i}={s}")
        
        return " → ".join(pattern)
    
    def find_minimal_counterexample(
        self,
        cex: Counterexample
    ) -> Counterexample:
        """
        找最小反例
        
        去除反例路径中不必要的状态
        """
        if len(cex.path) <= 2:
            return cex
        
        # 简化：返回原始反例
        return cex
    
    def rank_counterexamples(
        self,
        counterexamples: List[Counterexample]
    ) -> List[Counterexample]:
        """
        对反例排序
        
        按长度排序（短的更重要）
        """
        return sorted(counterexamples, key=lambda c: c.path_length)


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("反例生成与验证测试")
    print("=" * 50)
    
    # 构建转移系统
    transitions = {
        0: {1, 2},
        1: {2, 3},
        2: {3},
        3: {4},
        4: {0},  # 环
        5: {6},
        6: {7},
        7: {7}
    }
    
    init_states = {0}
    bad_states = {4}
    
    # 生成反例
    print("\n--- EF反例生成 ---")
    generator = CounterexampleGenerator(transitions)
    cex = generator.generate_counterexample(init_states, "EF", bad_states)
    if cex:
        print(f"反例: {cex}")
    
    # 验证反例
    print("\n--- 反例验证 ---")
    validator = CounterexampleValidator(transitions)
    if cex:
        path = [s.id for s in cex.path]
        is_valid, msg = validator.validate_path(path)
        print(f"验证结果: {msg}")
    
    # 分析反例
    print("\n--- 反例分析 ---")
    analyzer = CounterexampleAnalyzer()
    if cex:
        pattern = analyzer.extract_pattern([s.id for s in cex.path])
        print(f"模式: {pattern}")
        
        minimal = analyzer.find_minimal_counterexample(cex)
        print(f"最小反例长度: {minimal.path_length}")
    
    # 环反例
    print("\n--- AG环反例 ---")
    loop_cex = generator.find_loop_counterexample({0}, {4})
    print(f"环反例: {loop_cex}")
    
    print("\n✓ 反例生成与验证测试完成")
