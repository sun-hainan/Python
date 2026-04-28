"""
时序推理算法 (Temporal Reasoning - CTL/先验时序逻辑)
=================================================
实现时序知识图谱的推理能力，支持CTL（计算树逻辑）风格的时序查询。

支持的时序操作符：
- EX: 存在一条路径，下一时刻...
- EG: 存在一条路径，所有时刻...
- AX: 所有路径，下一时刻...
- AG: 所有路径，所有时刻...
- EF: 存在一条路径，最终...
- AF: 所有路径，最终...

参考：
    - Baader, F. et al. (2003). An Introduction to Description Logic.
    - Logic for Temporal Knowledge Graphs: CTL-based reasoning.
"""

from typing import List, Dict, Set, Tuple, Optional, Callable
from collections import defaultdict, deque
from enum import Enum


class TemporalLogicType(Enum):
    """时序逻辑类型"""
    EX = "EX"       # 存在next
    AX = "AX"       # 所有next
    EG = "EG"       # 存在globally
    AG = "AG"       # 所有globally
    EF = "EF"       # 存在finally
    AF = "AF"       # 所有finally
    EU = "EU"       # 存在until
    AU = "AU"       # 所有until


class TemporalState:
    """时序状态（世界状态）"""
    def __init__(self, id: str, facts: Set[Tuple[str, str, str]]):
        self.id = id
        self.facts = facts
        self.next_states = []  # 后继状态列表
        self.prev_states = []   # 前驱状态列表
        self.time = None       # 状态对应的时间戳


class TemporalModel:
    """
    时序模型（状态转移系统）
    
    结构: (S, R, L) 其中S是状态集合，R是转移关系，L是标签函数
    """
    def __init__(self, name: str = "TemporalModel"):
        self.name = name
        self.states = {}  # state_id -> TemporalState
        self.initial_state = None
    
    def add_state(self, state_id: str, facts: Set[Tuple], time=None):
        """添加状态"""
        self.states[state_id] = TemporalState(state_id, facts)
        if time is not None:
            self.states[state_id].time = time
        if self.initial_state is None:
            self.initial_state = state_id
    
    def add_transition(self, from_id: str, to_id: str):
        """添加转移"""
        if from_id in self.states and to_id in self.states:
            self.states[from_id].next_states.append(to_id)
            self.states[to_id].prev_states.append(from_id)
    
    def get_state(self, state_id: str) -> Optional[TemporalState]:
        return self.states.get(state_id)


class CTLReasoner:
    """
    CTL时序推理器
    
    参数:
        model: 时序模型
    """
    
    def __init__(self, model: TemporalModel):
        self.model = model
        self.cache = {}  # 缓存计算结果
    
    def _evaluate_atomic(self, state: TemporalState, predicate: Callable) -> bool:
        """评估原子命题"""
        return predicate(state.facts)
    
    def _eval_EX(self, state_id: str, predicate: Callable) -> bool:
        """
        EX φ: 存在一个后继状态满足φ
        
        参数:
            state_id: 当前状态
            predicate: φ条件
        
        返回:
            是否满足
        """
        state = self.model.get_state(state_id)
        if not state:
            return False
        
        for next_id in state.next_states:
            next_state = self.model.get_state(next_id)
            if next_state and self._evaluate_atomic(next_state, predicate):
                return True
        
        return False
    
    def _eval_EG(self, state_id: str, predicate: Callable) -> bool:
        """
        EG φ: 存在一条路径，所有状态满足φ
        
        参数:
            state_id: 当前状态
            predicate: φ条件
        
        返回:
            是否满足
        """
        # 使用递归+记忆化
        cache_key = ("EG", state_id, id(predicate))
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        state = self.model.get_state(state_id)
        if not state:
            self.cache[cache_key] = False
            return False
        
        # 检查当前状态
        if not self._evaluate_atomic(state, predicate):
            self.cache[cache_key] = False
            return False
        
        # 递归检查路径
        def has_eg_path(current_id: str, visited: Set[str]) -> bool:
            if current_id in visited:
                return True  # 找到一条无穷路径
            
            current = self.model.get_state(current_id)
            if not self._evaluate_atomic(current, predicate):
                return False
            
            visited.add(current_id)
            
            for next_id in current.next_states:
                if has_eg_path(next_id, visited.copy()):
                    return True
            
            return False
        
        result = has_eg_path(state_id, set())
        self.cache[cache_key] = result
        return result
    
    def _eval_EF(self, state_id: str, predicate: Callable) -> bool:
        """
        EF φ: 存在一条路径，最终状态满足φ
        
        等价于 EG true U φ
        
        参数:
            state_id: 当前状态
            predicate: φ条件
        
        返回:
            是否满足
        """
        cache_key = ("EF", state_id, id(predicate))
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # BFS搜索满足条件的状态
        queue = deque([state_id])
        visited = {state_id}
        
        while queue:
            current_id = queue.popleft()
            current = self.model.get_state(current_id)
            
            if self._evaluate_atomic(current, predicate):
                self.cache[cache_key] = True
                return True
            
            for next_id in current.next_states:
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append(next_id)
        
        self.cache[cache_key] = False
        return False
    
    def _eval_EU(self, state_id: str, phi_predicate: Callable, 
                 psi_predicate: Callable) -> bool:
        """
        E[φ U ψ]: 存在一条路径，φ一直成立直到ψ成立
        
        参数:
            state_id: 当前状态
            phi_predicate: φ条件
            psi_predicate: ψ条件
        
        返回:
            是否满足
        """
        cache_key = ("EU", state_id, id(phi_predicate), id(psi_predicate))
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 计算满足ψ的状态集合
        psi_states = set()
        for sid, state in self.model.states.items():
            if self._evaluate_atomic(state, psi_predicate):
                psi_states.add(sid)
        
        # 从ψ状态反向传播
        changed = True
        while changed:
            changed = False
            for sid, state in self.model.states.items():
                if sid in psi_states:
                    continue
                
                # 检查是否所有后继都在当前ψ集合中，且满足φ
                if self._evaluate_atomic(state, phi_predicate):
                    for next_id in state.next_states:
                        if next_id in psi_states:
                            psi_states.add(sid)
                            changed = True
                            break
        
        result = state_id in psi_states
        self.cache[cache_key] = result
        return result
    
    def evaluate(self, formula: str, state_id: str) -> bool:
        """
        评估CTL公式
        
        参数:
            formula: CTL公式字符串
            state_id: 评估状态
        
        返回:
            布尔结果
        """
        # 简单解析器
        # 格式: "EX", "EG", "EF", "EU(phi,psi)"
        
        if formula == "EX":
            return self._eval_EX(state_id, lambda f: True)
        elif formula == "EG":
            return self._eval_EG(state_id, lambda f: True)
        elif formula == "EF":
            return self._eval_EF(state_id, lambda f: True)
        elif formula.startswith("EU("):
            # EU(phi,psi) - 需要更多上下文
            return False
        else:
            # 原子命题
            state = self.model.get_state(state_id)
            if state:
                return formula in [t[1] for t in state.facts]
            return False
    
    def model_check(self, formula: str) -> Set[str]:
        """
        模型检测：找出所有满足公式的状态
        
        参数:
            formula: CTL公式
        
        返回:
            满足状态ID集合
        """
        results = set()
        for state_id in self.model.states:
            if self.evaluate(formula, state_id):
                results.add(state_id)
        return results


class TemporalRuleReasoner:
    """
    时序规则推理器
    
    基于规则的时序推理，支持：
    - 传递性: (s,p,o,t1) ∧ (o,p,r,t2) → (s,p,r,t2) if t1 < t2
    - 包含: (s,p,o,t) → (s,p,o,t') for all t' in [t.start, t.end]
    """
    
    def __init__(self, kg):
        self.kg = kg
        self.rules = []
    
    def add_rule(self, name: str, antecedent: Callable, consequent: Callable):
        """添加推理规则"""
        self.rules.append({
            "name": name,
            "antecedent": antecedent,
            "consequent": consequent
        })
    
    def forward_chain(self, time_start, time_end) -> Set[Tuple]:
        """
        前向链推理
        
        参数:
            time_start: 推理开始时间
            time_end: 推理结束时间
        
        返回:
            推导出的新事实集合
        """
        inferred = set()
        
        # 获取时间窗口内的事实
        window_facts = self.kg.query_between(time_start, time_end)
        
        # 应用每条规则
        for rule in self.rules:
            antecedent = rule["antecedent"]
            consequent = rule["consequent"]
            
            # 简单实现：检查规则是否适用
            new_facts = consequent(window_facts)
            inferred.update(new_facts)
        
        return inferred
    
    def temporal_transitivity_rule(self, facts: Set[Tuple]) -> Set[Tuple]:
        """
        时序传递规则
        
        如果 A --[p]--> B at t1 且 B --[p]--> C at t2 且 t1 < t2
        则 A --[p]--> C at t2
        """
        inferred = set()
        
        for s1, p1, o1, t1 in facts:
            for s2, p2, o2, t2 in facts:
                if p1 == p2 and o1 == s2 and t1 < t2:
                    # 传递
                    inferred.add((s1, p1, o2, t2))
        
        return inferred
    
    def temporal_composition_rule(self, facts: Set[Tuple]) -> Set[Tuple]:
        """
        时序组合规则
        
        如果 A --[p1]--> B at t 且 B --[p2]--> C at t
        则 A --[p1∘p2]--> C at t
        """
        inferred = set()
        
        for s1, p1, o1, t1 in facts:
            for s2, p2, o2, t2 in facts:
                if o1 == s2 and t1 == t2:
                    composed = (s1, f"{p1}∘{p2}", o2, t1)
                    inferred.add(composed)
        
        return inferred


if __name__ == "__main__":
    print("=== 时序推理测试 ===")
    
    # 构建时序模型
    model = TemporalModel("SimpleTKG")
    
    # 状态1: 2020年
    state1_facts = {
        ("Alice", "knows", "Bob"),
        ("Bob", "knows", "Charlie"),
        ("Alice", "age", "30")
    }
    model.add_state("s0", state1_facts, time=2020)
    
    # 状态2: 2021年
    state2_facts = {
        ("Alice", "knows", "Bob"),
        ("Bob", "knows", "Charlie"),
        ("Alice", "knows", "David"),  # 新增
        ("Alice", "age", "31")         # 更新
    }
    model.add_state("s1", state2_facts, time=2021)
    model.add_transition("s0", "s1")
    
    # 状态3: 2022年
    state3_facts = {
        ("Alice", "knows", "Bob"),
        ("Bob", "knows", "Charlie"),
        ("Alice", "knows", "David"),
        ("David", "knows", "Charlie"),  # 新增
    }
    model.add_state("s2", state3_facts, time=2022)
    model.add_transition("s1", "s2")
    
    print("时序模型:")
    print(f"  状态数: {len(model.states)}")
    print(f"  初始状态: {model.initial_state}")
    
    # CTL推理
    reasoner = CTLReasoner(model)
    
    print("\n\nCTL模型检测:")
    
    # EX: 在某个下一状态存在knows关系
    ex_result = reasoner.model_check("EX")
    print(f"  EX φ 满足的状态: {ex_result}")
    
    # EF: 最终状态
    ef_result = reasoner.model_check("EF")
    print(f"  EF φ 满足的状态: {ef_result}")
    
    # EG: 存在全局路径
    eg_result = reasoner.model_check("EG")
    print(f"  EG φ 满足的状态: {eg_result}")
    
    # 时序规则推理
    print("\n\n时序规则推理:")
    from temporal_knowledge_graph import TemporalKG
    
    kg = TemporalKG()
    kg.add_triple("A", "knows", "B", 2020)
    kg.add_triple("B", "knows", "C", 2021)
    kg.add_triple("A", "knows", "B", 2021)
    kg.add_triple("B", "knows", "C", 2022)
    
    rule_reasoner = TemporalRuleReasoner(kg)
    
    # 添加传递规则
    rule_reasoner.add_rule(
        "transitivity",
        lambda f: True,
        rule_reasoner.temporal_transitivity_rule
    )
    
    inferred = rule_reasoner.forward_chain(2020, 2022)
    print(f"  推理出的新事实: {inferred}")
    
    print("\n=== 测试完成 ===")
