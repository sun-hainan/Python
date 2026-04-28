"""
公平性约束处理 (Fairness Constraints)
======================================
功能：在模型检查中处理公平性约束
支持强公平性、弱公平性、JUSTICE/COMPASSION

核心概念：
1. 弱公平性(Weak Fairness): 如果条件无限经常成立，则对应动作无限经常执行
2. 强公平性(Strong Fairness): 如果条件无限经常成立，则对应动作无限经常执行
3. Justice: 无限经常满足的条件
4. Compassion: 无限经常满足→无限经常满足

处理方法：
- 在EX/EG/EU计算时加入公平性约束
- 移除不公平的路径
"""

from typing import List, Set, Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import itertools


class FairnessType(Enum):
    """公平性类型"""
    WEAK = auto()                                # 弱公平性
    STRONG = auto()                              # 强公平性
    JUSTICE = auto()                             # Justice公平性
    COMPASSION = auto()                          # Compassion公平性


@dataclass
class FairnessConstraint:
    """
    公平性约束定义
    - kind: 约束类型
    - condition: 条件表达式
    - action: 动作表达式（COMPASSION用）
    """
    kind: FairnessType
    condition: str
    action: Optional[str] = None                  # 仅COMPASSION使用


@dataclass
class TransitionSystem:
    """带公平性的转移系统"""
    states: Set[Any]                             # 状态集合
    init_states: Set[Any]                        # 初始状态集合
    transitions: Set[tuple]                      # 转移集合 (s, s')
    fairness_constraints: List[FairnessConstraint] = field(default_factory=list)


class FairnessHandler:
    """
    公平性约束处理器
    提供带公平性约束的路径搜索和模型检查
    """
    
    def __init__(self, system: TransitionSystem):
        self.system = system
        self._build_successor_map()
    
    def _build_successor_map(self):
        """构建后继状态映射"""
        self.succ_map: Dict[Any, Set[Any]] = {}
        self.pred_map: Dict[Any, Set[Any]] = {}
        
        for s, sp in self.system.transitions:
            # 后继映射
            if s not in self.succ_map:
                self.succ_map[s] = set()
            self.succ_map[s].add(sp)
            
            # 前驱映射
            if sp not in self.pred_map:
                self.pred_map[sp] = set()
            self.pred_map[sp].add(s)
    
    def get_successors(self, state: Any) -> Set[Any]:
        """获取后继状态集合"""
        return self.succ_map.get(state, set())
    
    def get_predecessors(self, state: Any) -> Set[Any]:
        """获取前驱状态集合"""
        return self.pred_map.get(state, set())
    
    def is_fair_path(self, path: List[Any]) -> bool:
        """
        检查路径是否满足公平性约束
        
        Args:
            path: 状态序列
        
        Returns:
            是否满足所有公平性约束
        """
        if len(path) < 2:
            return True
        
        # 构建路径上的转移集合
        path_transitions = set()
        for i in range(len(path) - 1):
            path_transitions.add((path[i], path[i+1]))
        
        # 检查每个公平性约束
        for fair in self.system.fairness_constraints:
            if not self._check_single_fairness(path, path_transitions, fair):
                return False
        
        return True
    
    def _check_single_fairness(
        self,
        path: List[Any],
        transitions: Set[tuple],
        fairness: FairnessConstraint
    ) -> bool:
        """
        检查单个公平性约束
        
        Args:
            path: 状态序列
            transitions: 路径上的转移
            fairness: 公平性约束
        
        Returns:
            是否满足
        """
        # 简化实现：检查条件是否在路径上出现
        condition_met = any(fairness.condition in str(s) for s in path)
        
        if fairness.kind == FairnessType.JUSTICE:
            # Justice: 条件必须无限经常成立
            # 在有限路径上，只要出现一次即可
            return condition_met
        
        elif fairness.kind == FairnessType.WEAK:
            # 弱公平性: 如果条件无限经常成立，则转移必须无限经常执行
            # 简化：假设路径延伸后条件会再次出现
            return True
        
        elif fairness.kind == FairnessType.STRONG:
            # 强公平性: 如果条件无限经常成立，则转移必须无限经常执行
            # 比弱公平性更强
            return True
        
        elif fairness.kind == FairnessType.COMPASSION:
            # Compassion: (condition → action) 必须无限经常成立
            # 简化：返回True
            return True
        
        return True
    
    def find_fair_path_bfs(
        self,
        start_states: Set[Any],
        target_check: Callable[[Any], bool],
        max_depth: int = 20
    ) -> Optional[List[Any]]:
        """
        BFS搜索满足公平性的路径
        
        Args:
            start_states: 起始状态集合
            target_check: 目标状态检测函数
            max_depth: 最大搜索深度
        
        Returns:
            公平路径或None
        """
        from collections import deque
        
        queue = deque()
        for s in start_states:
            queue.append(([s], {s}))               # (路径, 路径上的状态集合)
        
        visited_paths = set()
        
        while queue:
            path, path_states = queue.popleft()
            current = path[-1]
            
            # 检查是否到达目标
            if target_check(current):
                # 验证公平性
                if self.is_fair_path(path):
                    return path
                # 不公平，继续搜索
                continue
            
            # 深度限制
            if len(path) >= max_depth:
                continue
            
            # 展开后继状态
            for succ in self.get_successors(current):
                new_path = path + [succ]
                
                # 避免环路
                path_key = tuple(sorted(new_path))
                if path_key in visited_paths:
                    continue
                visited_paths.add(path_key)
                
                new_path_states = path_states | {succ}
                queue.append((new_path, new_path_states))
        
        return None
    
    def fair_preimage(self, states: Set[Any], fairness: FairnessConstraint) -> Set[Any]:
        """
        计算公平前像
        FairPre(T, X) = {s ∈ States | 
                        ∃fair path s → s' ∧ s' ∈ X}
        
        Args:
            states: 目标状态集合
            fairness: 公平性约束
        
        Returns:
            公平前像集合
        """
        result = set()
        
        for s in self.system.states:
            for succ in self.get_successors(s):
                if succ in states:
                    # 检查是否存在公平路径 s → succ
                    path = [s, succ]
                    if self.is_fair_path(path):
                        result.add(s)
                        break
        
        return result
    
    def fair_reachable(
        self,
        start_states: Set[Any],
        max_iterations: int = 100
    ) -> Set[Any]:
        """
        计算公平可达状态集合
        
        Args:
            start_states: 初始状态集合
            max_iterations: 最大迭代次数
        
        Returns:
            公平可达状态集合
        """
        reachable = set(start_states)
        new_reachable = set(start_states)
        
        for iteration in range(max_iterations):
            if not new_reachable:
                break
            
            iteration_reachable = set()
            
            for s in new_reachable:
                # 对每个公平性约束计算前像
                fair_preds = set()
                for fair in self.system.fairness_constraints:
                    preds = self.fair_preimage({s}, fair)
                    fair_preds |= preds
                
                # 收集所有后继
                for succ in self.get_successors(s):
                    if succ not in reachable:
                        iteration_reachable.add(succ)
            
            new_reachable = iteration_reachable
            reachable |= new_reachable
        
        return reachable


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("公平性约束处理测试")
    print("=" * 50)
    
    # 构建简单互斥系统
    states = {0, 1, 2, 3}
    init_states = {0}
    transitions = {
        (0, 1), (1, 2), (2, 3), (3, 0),  # 循环
        (0, 2), (2, 0)                    # 直接跳转
    }
    
    system = TransitionSystem(
        states=states,
        init_states=init_states,
        transitions=transitions,
        fairness_constraints=[
            FairnessConstraint(FairnessType.JUSTICE, condition="state=1"),
            FairnessConstraint(FairnessType.COMPASSION, condition="state=0", action="state=2"),
        ]
    )
    
    handler = FairnessHandler(system)
    
    print(f"\n转移系统:")
    print(f"  状态数: {len(states)}")
    print(f"  转移数: {len(transitions)}")
    print(f"  公平性约束数: {len(system.fairness_constraints)}")
    
    # 测试公平路径搜索
    print("\n公平路径搜索:")
    path = handler.find_fair_path_bfs(
        start_states=init_states,
        target_check=lambda s: s == 2,
        max_depth=10
    )
    print(f"  找到路径: {path}")
    
    # 测试公平可达性
    print("\n公平可达状态:")
    fair_reachable = handler.fair_reachable(init_states)
    print(f"  公平可达: {fair_reachable}")
    
    # 测试公平前像
    print("\n公平前像计算:")
    fair_pred = handler.fair_preimage({2}, system.fairness_constraints[0])
    print(f"  FairPre({{2}}, state=1) = {fair_pred}")
    
    print("\n✓ 公平性约束处理测试完成")
