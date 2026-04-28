"""
CTL模型检查器 (CTL Model Checker)
=================================
功能：实现CTL(Computational Tree Logic)模型检查算法
支持EX/EU/EG/AX/AU/AG/AF等路径量词和模态算子

CTL语法：
- AX φ: 所有路径下一步满足φ
- EX φ: 存在路径下一步满足φ
- AG φ: 所有路径所有步满足φ
- EG φ: 存在路径所有步满足φ
- AF φ: 所有路径最终满足φ
- EF φ: 存在路径最终满足φ
- A[φ U ψ]: 所有路径直到满足ψ
- E[φ U ψ]: 存在路径直到满足ψ

算法基础：
- EU: 最小不动点 μX. q ∨ (p ∧ EX)
- EG: 最小不动点 μX. p ∧ EX
- AF: 最大不动点 νX. q ∨ (p ∧ AX)
"""

from typing import Set, Dict, Callable, Optional, List, Any
from dataclasses import dataclass, field
from collections import deque
import copy


@dataclass
class KripkeStructure:
    """
    Kripke结构定义
    M = (S, S₀, R, L, AP)
    """
    states: Set[Any]                             # 状态集合
    init_states: Set[Any]                        # 初始状态集合
    transitions: Set[tuple]                     # 转移关系 R ⊆ S × S
    labels: Dict[Any, Set[str]]                  # 状态标签函数 L: S → 2^AP
    atomic_props: Set[str]                       # 原子命题集合


class CTLModelChecker:
    """
    CTL模型检查器
    
    使用不动点算法计算模态公式
    """
    
    def __init__(self, model: KripkeStructure):
        self.model = model
        self._build_graph()
    
    def _build_graph(self):
        """构建状态图的后继/前驱映射"""
        self.succ: Dict[Any, Set[Any]] = {}      # 后继状态映射
        self.pred: Dict[Any, Set[Any]] = {}      # 前驱状态映射
        
        for s, sp in self.model.transitions:
            # 后继
            if s not in self.succ:
                self.succ[s] = set()
            self.succ[s].add(sp)
            
            # 前驱
            if sp not in self.pred:
                self.pred[sp] = set()
            self.pred[sp].add(s)
    
    def get_successors(self, state: Any) -> Set[Any]:
        """获取状态的后继"""
        return self.succ.get(state, set())
    
    def get_predecessors(self, state: Any) -> Set[Any]:
        """获取状态的前驱"""
        return self.pred.get(state, set())
    
    def eval_atomic(self, prop: str) -> Set[Any]:
        """
        求值原子命题，返回满足该命题的状态集合
        
        Args:
            prop: 原子命题名
        
        Returns:
            满足prop的状态集合
        """
        result = set()
        for s, labels in self.model.labels.items():
            if prop in labels:
                result.add(s)
        return result
    
    # -------------------- 辅助函数 --------------------
    
    def _preimage(self, X: Set[Any]) -> Set[Any]:
        """
        计算前像 Pre(X) = {s | ∃s' ∈ X: (s, s') ∈ R}
        """
        result = set()
        for s in self.model.states:
            for sp in self.get_successors(s):
                if sp in X:
                    result.add(s)
                    break
        return result
    
    def _preimage_exact(self, Y: Set[Any]) -> Set[Any]:
        """
        精确前像计算（考虑所有后继都在Y中）
        """
        result = set()
        for s in self.model.states:
            succs = self.get_successors(s)
            if succs and succs.issubset(Y):
                result.add(s)
        return result
    
    # -------------------- CTL算子实现 --------------------
    
    def check_EF(self, p: Set[Any]) -> Set[Any]:
        """
        EF p = 存在路径最终满足p
        等价于: REACHABILITY(p) - 从初始状态可达且满足p的状态
        
        算法: 最大不动点 νY. p ∪ Pre(Y)
        """
        Y = p.copy()
        Y_new = p.copy()
        iteration = 0
        
        while Y != Y_new:
            Y = Y_new
            pre = self._preimage(Y)
            Y_new = p | pre
            iteration += 1
            if iteration > 1000:
                raise RuntimeError("EF不动点不收敛")
        
        return Y
    
    def check_EG(self, p: Set[Any]) -> Set[Any]:
        """
        EG p = 存在全局路径满足p
        即：存在一条无限路径，路径上所有状态都满足p
        
        算法: 最小不动点 μY. p ∩ Pre(Y)
        """
        if not p:
            return set()
        
        Y = self.model.states.copy()             # 初始：所有状态
        Y_new = Y.copy()
        iteration = 0
        
        while Y != Y_new:
            Y = Y_new
            pre = self._preimage(Y)
            Y_new = p & pre                       # 交集
            iteration += 1
            if iteration > 1000:
                raise RuntimeError("EG不动点不收敛")
        
        return Y
    
    def check_EU(self, p: Set[Any], q: Set[Any]) -> Set[Any]:
        """
        E[p U q] = 存在路径直到q满足p直到q
        
        算法: 最小不动点 μY. q ∪ (p ∩ Pre(Y))
        """
        if not q:
            return set()
        
        Y = q.copy()
        Y_new = q.copy()
        iteration = 0
        
        while True:
            pre = self._preimage(Y)
            candidate = q | (p & pre)
            
            if candidate == Y:
                return Y
            Y = candidate
            iteration += 1
            if iteration > 1000:
                raise RuntimeError("EU不动点不收敛")
    
    def check_EX(self, p: Set[Any]) -> Set[Any]:
        """
        EX p = 存在后继满足p
        
        算法: EX(p) = Pre({p})
        """
        result = set()
        for s in self.model.states:
            for sp in self.get_successors(s):
                if sp in p:
                    result.add(s)
                    break
        return result
    
    def check_AX(self, p: Set[Any]) -> Set[Any]:
        """
        AX p = 所有后继满足p
        
        算法: AX(p) = ¬EX(¬p)
        """
        not_p = self.model.states - p
        not_ex_not_p = self.check_EX(not_p)
        return self.model.states - not_ex_not_p
    
    def check_AF(self, p: Set[Any]) -> Set[Any]:
        """
        AF p = 所有路径最终满足p
        
        算法: AF(p) = ¬EG(¬p)
        """
        not_p = self.model.states - p
        eg_not_p = self.check_EG(not_p)
        return self.model.states - eg_not_p
    
    def check_AG(self, p: Set[Any]) -> Set[Any]:
        """
        AG p = 所有路径所有步满足p
        
        算法: AG(p) = ¬EF(¬p)
        """
        not_p = self.model.states - p
        ef_not_p = self.check_EF(not_p)
        return self.model.states - ef_not_p
    
    def check_AU(self, p: Set[Any], q: Set[Any]) -> Set[Any]:
        """
        A[p U q] = 所有路径直到q满足p
        
        算法: AU(p, q) = ¬E[¬q U ¬(p ∨ q)]
        """
        not_q = self.model.states - q
        not_p_or_q = self.model.states - p
        e_not_q_until = self.check_EU(not_q, not_p_or_q)
        return self.model.states - e_not_q_until
    
    # -------------------- 公式解析与检查 --------------------
    
    def check_formula(self, formula: str) -> Set[Any]:
        """
        检查CTL公式，返回满足该公式的状态集合
        
        Args:
            formula: CTL公式字符串
        
        Returns:
            满足公式的状态集合
        """
        print(f"[CTL] 检查公式: {formula}")
        
        # 解析并计算
        if formula.startswith("EF"):
            prop = formula[2:].strip()
            p = self.eval_atomic(prop)
            return self.check_EF(p)
        elif formula.startswith("EG"):
            prop = formula[2:].strip()
            p = self.eval_atomic(prop)
            return self.check_EG(p)
        elif formula.startswith("EU"):
            # E[p U q] 格式
            parts = formula[2:].strip().split("U")
            if len(parts) == 2:
                p_prop, q_prop = parts[0].strip(), parts[1].strip()
                p = self.eval_atomic(p_prop)
                q = self.eval_atomic(q_prop)
                return self.check_EU(p, q)
        elif formula.startswith("EX"):
            prop = formula[2:].strip()
            p = self.eval_atomic(prop)
            return self.check_EX(p)
        elif formula.startswith("AX"):
            prop = formula[2:].strip()
            p = self.eval_atomic(prop)
            return self.check_AX(p)
        elif formula.startswith("AF"):
            prop = formula[2:].strip()
            p = self.eval_atomic(prop)
            return self.check_AF(p)
        elif formula.startswith("AG"):
            prop = formula[2:].strip()
            p = self.eval_atomic(prop)
            return self.check_AG(p)
        else:
            # 原子命题
            return self.eval_atomic(formula)
    
    def check_property(self, formula: str) -> bool:
        """
        检查性质是否在模型中成立
        
        Args:
            formula: CTL性质公式
        
        Returns:
            是否在所有初始状态下成立
        """
        sat_states = self.check_formula(formula)
        result = self.model.init_states.issubset(sat_states)
        print(f"[CTL] 性质 {formula}: {'成立' if result else '不成立'}")
        if not result:
            counterexample = self.model.init_states - sat_states
            print(f"[CTL] 反例状态: {counterexample}")
        return result


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("CTL模型检查器测试")
    print("=" * 50)
    
    # 构建简单Kripke结构
    # 示例: 两个进程互斥模型
    states = {"s0", "s1", "s2", "s3"}
    init_states = {"s0"}
    transitions = {
        ("s0", "s1"), ("s1", "s2"), ("s2", "s3"), ("s3", "s0"),
        ("s0", "s2"), ("s2", "s0")
    }
    labels = {
        "s0": {"idle"},
        "s1": {"want_cs", "waiting"},
        "s2": {"in_cs"},                          # 临界区
        "s3": {"want_cs"}
    }
    ap = {"idle", "want_cs", "waiting", "in_cs"}
    
    model = KripkeStructure(
        states=states,
        init_states=init_states,
        transitions=transitions,
        labels=labels,
        atomic_props=ap
    )
    
    checker = CTLModelChecker(model)
    
    print("\n模型信息:")
    print(f"  状态数: {len(states)}")
    print(f"  转移数: {len(transitions)}")
    print(f"  原子命题: {ap}")
    
    # 测试原子命题
    print("\n原子命题求值:")
    print(f"  in_cs: {checker.eval_atomic('in_cs')}")
    print(f"  idle: {checker.eval_atomic('idle')}")
    
    # 测试CTL算子
    print("\nCTL算子测试:")
    
    print(f"  EG idle: {checker.check_formula('EG idle')}")
    print(f"  EF in_cs: {checker.check_formula('EF in_cs')}")
    print(f"  EX waiting: {checker.check_formula('EX waiting')}")
    print(f"  AF in_cs: {checker.check_formula('AF in_cs')}")
    
    # 测试性质
    print("\n性质验证:")
    checker.check_property("AG EF in_cs")         # 最终会进入临界区
    checker.check_property("EF EG idle")          # 可能一直空闲
    
    print("\n✓ CTL模型检查器测试完成")
