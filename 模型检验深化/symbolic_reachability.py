"""
符号可达性分析 (Symbolic Reachability Analysis)
================================================
功能：使用BDD/符号技术分析状态转移系统的可达状态集合
支持前向/后向可达性、不动点检测、极小/极大不动点计算

核心算法：
1. 前向可达性: 从初始状态沿转移方向展开
2. 后向可达性: 从目标状态逆转移方向回推
3. 不动点检测: 当Y_{n+1} = Y_n时终止
4. 图像前像: Pre(T, X) = {s | ∃s': T(s,s') ∧ X(s')}
"""

from typing import Set, Dict, Callable, Optional, Tuple, Any, List
from dataclasses import dataclass, field
import itertools


@dataclass
class TransitionRelation:
    """
    转移关系表示
    - succ_func: 状态→后继状态集合函数
    - pred_func: 状态→前驱状态集合函数
    - trans_pairs: 转移对集合 (s, s')
    """
    succ_func: Optional[Callable[[Any], Set[Any]]] = None
    pred_func: Optional[Callable[[Any], Set[Any]]] = None
    trans_pairs: Set[Tuple[Any, Any]] = field(default_factory=set)


@dataclass  
class SymbolicReachableSet:
    """
    可达状态集合的符号表示
    - state_set: 状态集合（使用显式集合简化）
    - bound: 边界状态
    - iteration: 迭代次数
    """
    state_set: Set[Any]
    bound: Set[Any] = field(default_factory=set)
    iteration: int = 0


class SymbolicReachabilityAnalyzer:
    """
    符号可达性分析器
    
    使用集合操作实现状态空间遍历
    实际应用中使用BDD提高效率
    """
    
    def __init__(self, all_states: Set[Any], trans: TransitionRelation):
        self.all_states = all_states
        self.trans = trans
        self._build_maps()
    
    def _build_maps(self):
        """构建后继/前驱映射"""
        self.succ_map: Dict[Any, Set[Any]] = {}
        self.pred_map: Dict[Any, Set[Any]] = {}
        
        if self.trans.trans_pairs:
            for s, sp in self.trans.trans_pairs:
                # 后继
                if s not in self.succ_map:
                    self.succ_map[s] = set()
                self.succ_map[s].add(sp)
                
                # 前驱
                if sp not in self.pred_map:
                    self.pred_map[sp] = set()
                self.pred_map[sp].add(s)
        elif self.trans.succ_func:
            for s in self.all_states:
                self.succ_map[s] = self.trans.succ_func(s)
                for sp in self.succ_map[s]:
                    if sp not in self.pred_map:
                        self.pred_map[sp] = set()
                    self.pred_map[sp].add(s)
    
    def get_successors(self, state: Any) -> Set[Any]:
        """获取后继状态"""
        return self.succ_map.get(state, set())
    
    def get_predecessors(self, state: Any) -> Set[Any]:
        """获取前驱状态"""
        return self.pred_map.get(state, set())
    
    # -------------------- 可达性算法 --------------------
    
    def forward_reachability(
        self,
        init_states: Set[Any],
        max_iterations: int = 1000,
        stop_on_fixpoint: bool = True
    ) -> SymbolicReachableSet:
        """
        前向可达性分析
        计算: Reach = μY. I ∪ Post(Y)
        
        Args:
            init_states: 初始状态集合
            max_iterations: 最大迭代次数
            stop_on_fixpoint: 检测到不动点时停止
        
        Returns:
            SymbolicReachableSet: 可达状态集合
        """
        print("[可达性] 前向可达性分析开始")
        
        Y = set(init_states)                      # 当前可达集
        Y_new = Y.copy()
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            new_states = set()
            
            # Post(Y) = 所有Y中状态的后继
            for s in Y_new:
                new_states |= self.get_successors(s)
            
            # Y = Y ∪ Post(Y)
            Y_new = Y | new_states
            
            print(f"  迭代 {iteration}: |Y|={len(Y)}, |Y_new|={len(Y_new)}")
            
            if stop_on_fixpoint and Y_new == Y:
                print(f"[可达性] 达到不动点 (迭代 {iteration})")
                break
            
            Y = Y_new.copy()
        
        return SymbolicReachableSet(
            state_set=Y,
            bound=Y - set(init_states),
            iteration=iteration
        )
    
    def backward_reachability(
        self,
        target_states: Set[Any],
        max_iterations: int = 1000
    ) -> SymbolicReachableSet:
        """
        后向可达性分析
        计算: BReach = νY. T ∪ Pre(Y)
        
        Args:
            target_states: 目标状态集合
            max_iterations: 最大迭代次数
        
        Returns:
            SymbolicReachableSet: 可达（回推）状态集合
        """
        print("[可达性] 后向可达性分析开始")
        
        Y = set(target_states)                     # 当前集合
        Y_new = Y.copy()
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            new_states = set()
            
            # Pre(Y) = 所有Y中状态的前驱
            for s in Y_new:
                new_states |= self.get_predecessors(s)
            
            Y_new = Y | new_states
            
            print(f"  迭代 {iteration}: |Y|={len(Y)}, |Y_new|={len(Y_new)}")
            
            if Y_new == Y:
                print(f"[可达性] 达到不动点 (迭代 {iteration})")
                break
            
            Y = Y_new.copy()
        
        return SymbolicReachableSet(
            state_set=Y,
            bound=Y - target_states,
            iteration=iteration
        )
    
    def compute_preimage(self, X: Set[Any]) -> Set[Any]:
        """
        计算前像 Pre(T, X)
        Pre(T, X) = {s | ∃s' ∈ X: T(s, s')}
        
        Args:
            X: 目标状态集合
        
        Returns:
            前像状态集合
        """
        preimage = set()
        for s in self.all_states:
            # 检查是否存在后继在X中
            succs = self.get_successors(s)
            if succs & X:                          # 交集非空
                preimage.add(s)
        return preimage
    
    def compute_postimage(self, X: Set[Any]) -> Set[Any]:
        """
        计算后像 Post(T, X)
        Post(T, X) = {s' | ∃s ∈ X: T(s, s')}
        
        Args:
            X: 源状态集合
        
        Returns:
            后像状态集合
        """
        postimage = set()
        for s in X:
            postimage |= self.get_successors(s)
        return postimage
    
    # -------------------- 性质检查 --------------------
    
    def check_safety(
        self,
        init_states: Set[Any],
        bad_states: Set[Any],
        invariant: Optional[Callable[[Any], bool]] = None
    ) -> Tuple[bool, Optional[List[Any]]]:
        """
        检查安全性性质：是否不存在从初始状态到坏状态的路�
        
        Args:
            init_states: 初始状态集合
            bad_states: 坏状态集合
            invariant: 可选的不变式检测函数
        
        Returns:
            (是否安全, 反例路径如果有)
        """
        print(f"[安全性检查] 初始状态: {len(init_states)}, 坏状态: {len(bad_states)}")
        
        # 前向展开搜索坏状态
        visited = set()
        queue = [(s, [s]) for s in init_states]    # (当前状态, 路径)
        
        while queue:
            current, path = queue.pop(0)
            
            if current in visited:
                continue
            visited.add(current)
            
            # 检查是否到达坏状态
            if current in bad_states:
                print(f"[安全性检查] 发现坏状态路径!")
                return False, path
            
            # 展开后继
            for succ in self.get_successors(current):
                if succ not in visited:
                    queue.append((succ, path + [succ]))
        
        print(f"[安全性检查] 安全 (检查了 {len(visited)} 个状态)")
        return True, None
    
    def check_liveness(
        self,
        init_states: Set[Any],
        target_condition: Callable[[Any], bool],
        max_fair_paths: int = 1
    ) -> bool:
        """
        检查活跃性性质：是否存在到目标状态的公平路径
        
        Args:
            init_states: 初始状态集合
            target_condition: 目标条件检测函数
            max_fair_paths: 需要找到的公平路径数
        
        Returns:
            是否存在活跃路径
        """
        print(f"[活跃性检查] 搜索目标状态...")
        
        found_paths = 0
        visited = set()
        queue = [(s, [s]) for s in init_states]
        
        while queue and found_paths < max_fair_paths:
            current, path = queue.pop(0)
            
            if current in visited:
                continue
            visited.add(current)
            
            # 检查目标
            if target_condition(current):
                found_paths += 1
                print(f"[活跃性检查] 找到路径 #{found_paths}")
                if found_paths >= max_fair_paths:
                    return True
            
            # 展开
            for succ in self.get_successors(current):
                if succ not in visited:
                    queue.append((succ, path + [succ]))
        
        return found_paths >= max_fair_paths


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("符号可达性分析测试")
    print("=" * 50)
    
    # 构建简单转移系统
    all_states = set(range(20))
    trans_pairs = set()
    for i in range(19):
        trans_pairs.add((i, i+1))                 # i → i+1
        if i < 18:
            trans_pairs.add((i, i+2))             # i → i+2
    trans_pairs.add((19, 0))                       # 循环
    
    trans = TransitionRelation(trans_pairs=trans_pairs)
    analyzer = SymbolicReachabilityAnalyzer(all_states, trans)
    
    print(f"\n转移系统:")
    print(f"  状态数: {len(all_states)}")
    print(f"  转移数: {len(trans_pairs)}")
    
    # 测试前向可达性
    print("\n前向可达性测试:")
    result = analyzer.forward_reachability({0}, stop_on_fixpoint=True)
    print(f"  可达状态数: {len(result.state_set)}")
    print(f"  迭代次数: {result.iteration}")
    
    # 测试后向可达性
    print("\n后向可达性测试:")
    result = analyzer.backward_reachability({19})
    print(f"  可达状态数: {len(result.state_set)}")
    
    # 测试安全性检查
    print("\n安全性检查测试:")
    is_safe, cex = analyzer.check_safety({0}, {15})
    print(f"  安全: {is_safe}")
    if cex:
        print(f"  反例路径: {cex}")
    
    # 测试前像/后像
    print("\n图像计算测试:")
    pre = analyzer.compute_preimage({18, 19})
    post = analyzer.compute_postimage({0, 1})
    print(f"  Pre({{18,19}}): {pre}")
    print(f"  Post({{0,1}}): {post}")
    
    print("\n✓ 符号可达性分析测试完成")
