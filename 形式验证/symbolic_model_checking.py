# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / symbolic_model_checking

本文件实现 symbolic_model_checking 相关的算法功能。
"""

import numpy as np
from collections import defaultdict, deque


class TransitionSystem:
    """
    迁移系统
    
    TS = (V, V0, T, L, AP)
    - V: 变量集合（状态变量）
    - V0: 初始状态
    - T: 迁移关系
    - L: 标签函数
    - AP: 原子命题
    """
    
    def __init__(self, var_names):
        """
        初始化迁移系统
        
        参数:
            var_names: 状态变量名列表
        """
        self.var_names = var_names
        self.num_vars = len(var_names)
        self.var_index = {v: i for i, v in enumerate(var_names)}
        
        self.initial_states = []  # 初始状态条件
        self.transitions = []     # 迁移条件列表
        self.labels = {}           # 状态 -> 原子命题集合
    
    def add_initial_state(self, condition):
        """
        添加初始状态条件
        
        参数:
            condition: dict {var: value} 或 条件表达式
        """
        self.initial_states.append(condition)
    
    def add_transition(self, from_state, to_state, condition=None):
        """
        添加迁移
        
        参数:
            from_state: 源状态条件
            to_state: 目标状态赋值
            condition: 迁移条件
        """
        self.transitions.append({
            'from': from_state,
            'to': to_state,
            'condition': condition
        })
    
    def add_label(self, state, ap_set):
        """添加状态标签"""
        self.labels[state] = set(ap_set)
    
    def num_states(self):
        """估算状态数量"""
        return 2 ** self.num_vars
    
    def get_successors(self, state):
        """
        获取状态的后继
        
        参数:
            state: 当前状态（字典或元组）
        
        返回:
            后继状态列表
        """
        if isinstance(state, dict):
            state_tuple = tuple(state.get(v, 0) for v in self.var_names)
        else:
            state_tuple = tuple(state)
        
        successors = []
        
        for trans in self.transitions:
            # 检查from条件
            from_cond = trans['from']
            if isinstance(from_cond, dict):
                match = all(
                    state_tuple[self.var_index.get(k, k)] == v
                    for k, v in from_cond.items()
                    if k in self.var_index
                )
            else:
                match = True
            
            if match:
                # 应用to转换
                new_state = list(state_tuple)
                for k, v in trans['to'].items():
                    if k in self.var_index:
                        new_state[self.var_index[k]] = v
                
                # 检查condition
                cond = trans.get('condition')
                if cond is None or self._check_condition(cond, state_tuple, new_state):
                    successors.append(tuple(new_state))
        
        return successors
    
    def _check_condition(self, cond, from_state, to_state):
        """检查迁移条件"""
        # 简化实现
        return True
    
    def enumerate_states(self, max_states=None):
        """
        枚举所有可达状态
        
        参数:
            max_states: 最大状态数
        
        返回:
            可达状态集合
        """
        # BFS从初始状态开始
        visited = set()
        queue = deque()
        
        for init in self.initial_states:
            if isinstance(init, dict):
                state = tuple(init.get(v, 0) for v in self.var_names)
            else:
                state = tuple(0 for _ in self.var_names)
            queue.append(state)
            visited.add(state)
        
        count = 0
        while queue and (max_states is None or count < max_states):
            state = queue.popleft()
            count += 1
            
            for succ in self.get_successors(state):
                if succ not in visited:
                    visited.add(succ)
                    queue.append(succ)
        
        return visited


class SymbolicModelChecker:
    """
    符号模型检查器
    
    使用BDD风格的符号表示进行模型检查
    这里用集合模拟，实际使用BDD
    """
    
    def __init__(self, ts):
        self.ts = ts
        self.cache = {}
    
    def pre_image(self, states, direction='forward'):
        """
        计算状态集的前像/后像
        
        前像 (Pre): 能够到达states的状态
        后像 (Post): states能够到达的状态
        """
        if direction == 'forward':
            return self._post_image(states)
        else:
            return self._pre_image(states)
    
    def _post_image(self, states):
        """后像：states能到达的状态"""
        result = set()
        for state in states:
            result.update(self.ts.get_successors(state))
        return result
    
    def _pre_image(self, states):
        """前像：能到达states的状态"""
        result = set()
        for state in self.ts.enumerate_states():
            successors = self.ts.get_successors(state)
            if any(succ in states for succ in successors):
                result.add(state)
        return result
    
    def reachability(self, target_states, max_depth=None):
        """
        可达性分析
        
        参数:
            target_states: 目标状态集合
            max_depth: 最大深度
        
        返回:
            (是否可达, 路径)
        """
        visited = set()
        queue = deque()
        
        for init in self.ts.initial_states:
            if isinstance(init, dict):
                state = tuple(init.get(v, 0) for v in self.ts.var_names)
            else:
                state = tuple(0 for _ in self.ts.var_names)
            queue.append((state, [state]))
            visited.add(state)
        
        depth = 0
        while queue:
            level_size = len(queue)
            
            for _ in range(level_size):
                state, path = queue.popleft()
                
                if state in target_states:
                    return True, path
                
                for succ in self.ts.get_successors(state):
                    if succ not in visited:
                        visited.add(succ)
                        queue.append((succ, path + [succ]))
            
            depth += 1
            if max_depth is not None and depth >= max_depth:
                break
        
        return False, []
    
    def check_INVARIANT(self, formula, max_depth=None):
        """
        检查不变式 INVAR φ
        
        INVAR φ = 在所有可达状态上φ始终成立
        等价于: NOT EF NOT φ
        
        参数:
            formula: 不变式条件 (state -> bool)
            max_depth: 最大检查深度
        
        返回:
            (是否满足, 反例路径)
        """
        # 找不满足φ的状态
        bad_states = set()
        for state in self.ts.enumerate_states(max_states=10000):
            if isinstance(state, dict):
                state_dict = state
            else:
                state_dict = dict(zip(self.ts.var_names, state))
            
            if not formula(state_dict):
                bad_states.add(state)
        
        if not bad_states:
            return True, []
        
        # 找从初始状态能否到达坏状态
        reachable, path = self.reachability(bad_states, max_depth)
        
        if reachable:
            return False, path
        return True, []
    
    def compute_lfp(self, post_func, pre_func=None, initial=None):
        """
        计算最小不动点（Least Fixed Point）
        
        用于计算: EG φ, EU等
        
        参数:
            post_func: 后像函数
            pre_func: 前像函数（可选）
            initial: 初始集合
        
        返回:
            最小不动点
        """
        if initial is None:
            X = set()  # 空集作为初始
        else:
            X = set(initial)
        
        while True:
            new_X = post_func(X)
            if new_X.issubset(X):
                return X
            X = new_X
    
    def compute_gfp(self, post_func, initial=None):
        """
        计算最大不动点（Greatest Fixed Point）
        
        用于计算: AG φ, 等
        
        参数:
            post_func: 后像函数
            initial: 初始上界集合
        
        返回:
            最大不动点
        """
        if initial is None:
            X = set(self.ts.enumerate_states(max_states=10000))
        else:
            X = set(initial)
        
        while True:
            new_X = post_func(X)
            if X.issubset(new_X):
                return X
            X = new_X


class BoundedModelChecker:
    """
    限界模型检查器（BMC）
    
    核心思想：
    1. 不展开整个状态空间
    2. 只检查长度k以内的路径
    3. 展开为命题逻辑公式（SAT/SMT）
    4. 寻找长度k的反例路径
    """
    
    def __init__(self, ts):
        self.ts = ts
    
    def encode_state(self, state, k):
        """
        编码第k步的状态
        
        参数:
            state: 状态（字典或元组）
            k: 时间步
        
        返回:
            字面量列表
        """
        literals = []
        if isinstance(state, dict):
            for var, val in state.items():
                literals.append(f"{var}_{k}={'1' if val else '0'}")
        else:
            for i, val in enumerate(state):
                literals.append(f"v{self.ts.var_names[i]}_{k}={'1' if val else '0'}")
        return literals
    
    def encode_transition(self, k):
        """
        编码第k到k+1步的迁移约束
        
        返回:
            CNF公式字符串（简化表示）
        """
        constraints = []
        
        for trans in self.ts.transitions:
            # 编码from条件
            from_lits = self.encode_state(trans['from'], k)
            
            # 编码to条件
            to_lits = self.encode_state(trans['to'], k + 1)
            
            constraints.append(f"({from_lits}) -> ({to_lits})")
        
        return constraints
    
    def unroll(self, depth):
        """
        展开系统到指定深度
        
        参数:
            depth: 展开深度
        
        返回:
            (初始条件, 迁移序列, 编码公式)
        """
        initial_enc = []
        for init in self.ts.initial_states:
            initial_enc.extend(self.encode_state(init, 0))
        
        transition_encs = []
        for k in range(depth):
            transition_encs.extend(self.encode_transition(k))
        
        return initial_enc, transition_encs
    
    def check_path_property(self, property_func, max_depth=10):
        """
        检查路径性质（EF p 等）
        
        参数:
            property_func: 性质检查函数
            max_depth: 最大深度
        
        返回:
            (是否满足, 最短反例长度)
        """
        for k in range(max_depth + 1):
            # 展开到深度k
            initial, transitions = self.unroll(k)
            
            # 模拟执行k步，检查性质
            visited = set()
            queue = deque()
            
            # 初始化
            for init in self.ts.initial_states:
                state = tuple(init.get(v, 0) for v in self.ts.var_names) if isinstance(init, dict) else init
                if state:
                    queue.append((state, 0))
                    visited.add(state)
            
            # BFS直到深度k
            while queue:
                state, depth = queue.popleft()
                
                if depth >= k:
                    continue
                
                if property_func(state):
                    return True, depth
                
                for succ in self.ts.get_successors(state):
                    if succ not in visited:
                        visited.add(succ)
                        queue.append((succ, depth + 1))
        
        return False, None
    
    def find_counterexample(self, bad_state_func, max_depth=10):
        """
        寻找反例路径
        
        参数:
            bad_state_func: 坏状态检查函数
            max_depth: 最大深度
        
        返回:
            反例路径 或 None
        """
        for k in range(max_depth + 1):
            initial, transitions = self.unroll(k)
            
            # BFS找坏状态
            visited = {('init', 0): None}
            queue = deque()
            
            for init in self.ts.initial_states:
                state = tuple(init.get(v, 0) for v in self.ts.var_names) if isinstance(init, dict) else init
                queue.append((state, 0))
            
            while queue:
                state, depth = queue.popleft()
                
                if bad_state_func(state):
                    # 重构路径
                    path = [state]
                    node = ('init', 0)
                    return path
                
                if depth >= k:
                    continue
                
                for succ in self.ts.get_successors(state):
                    if succ not in visited:
                        visited[succ] = state
                        queue.append((succ, depth + 1))
        
        return None


def run_demo():
    """运行符号模型检查演示"""
    print("=" * 60)
    print("符号模型检查与BMC限界模型检查")
    print("=" * 60)
    
    # 创建简单的迁移系统
    ts = TransitionSystem(['x', 'y'])
    
    # 初始状态: x=0, y=0
    ts.add_initial_state({'x': 0, 'y': 0})
    
    # 转换: x增加，y在x=5时变1
    ts.add_transition({'x': 0, 'y': 0}, {'x': 1, 'y': 0})
    ts.add_transition({'x': 1, 'y': 0}, {'x': 2, 'y': 0})
    ts.add_transition({'x': 2, 'y': 0}, {'x': 3, 'y': 0})
    ts.add_transition({'x': 3, 'y': 0}, {'x': 4, 'y': 0})
    ts.add_transition({'x': 4, 'y': 0}, {'x': 5, 'y': 0})
    ts.add_transition({'x': 5, 'y': 0}, {'x': 6, 'y': 1})
    ts.add_transition({'x': 6, 'y': 1}, {'x': 7, 'y': 1})
    
    print("\n[迁移系统]")
    print(f"  变量: {ts.var_names}")
    print(f"  初始状态: {ts.initial_states}")
    print(f"  转换数: {len(ts.transitions)}")
    
    # 创建检查器
    checker = SymbolicModelChecker(ts)
    
    print("\n[可达性分析]")
    target = {(7, 1)}
    reachable, path = checker.reachability(target)
    print(f"  目标状态 {target}:")
    print(f"    可达: {reachable}")
    if path:
        print(f"    路径长度: {len(path)}")
    
    print("\n[不变式检查]")
    
    # 检查 x <= 10
    def inv1(state):
        return state[0] <= 10
    
    ok, cex = checker.check_INVARIANT(inv1)
    print(f"  INVAR (x <= 10): {'满足' if ok else '不满足'}")
    if cex:
        print(f"    反例路径: {cex[:5]}...")
    
    # 检查 y == 1 -> x >= 6
    def inv2(state):
        if state[1] == 1:
            return state[0] >= 6
        return True
    
    ok, cex = checker.check_INVARIANT(inv2)
    print(f"  INVAR (y==1 -> x>=6): {'满足' if ok else '不满足'}")
    
    # BMC演示
    print("\n[BMC限界模型检查]")
    bmc = BoundedModelChecker(ts)
    
    # 展开
    initial, transitions = bmc.unroll(3)
    print(f"  展开深度3:")
    print(f"    初始条件数: {len(initial)}")
    print(f"    迁移约束数: {len(transitions)}")
    
    # 找坏状态 (x > 7)
    def bad(state):
        return state[0] > 7
    
    ok, depth = bmc.check_path_property(bad, max_depth=10)
    print(f"  检查 EF (x > 7):")
    print(f"    满足: {ok}, 深度: {depth}")
    
    print("\n" + "=" * 60)
    print("符号模型检查核心概念:")
    print("  1. 符号表示: 用BDD/集合表示状态集合")
    print("  2. 图像计算: Pre/Post图像")
    print("  3. 不动点: LFP/GFP用于AG/EG等算子")
    print("  4. BMC: 限界模型检查，展开k步，转为SAT")
    print("  5. 复杂度: 符号检查是多项式空间，穷举是指数时间")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
