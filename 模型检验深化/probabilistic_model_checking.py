"""
概率模型检查 (Probabilistic Model Checking)
============================================
功能：对概率转移系统（DTMC/CTMC）进行模型检查
支持PCTL/CSL等概率时序逻辑

核心概念：
1. DTMC (Discrete-Time Markov Chain): 离散时间马尔可夫链
2. CTMC (Continuous-Time Markov Chain): 连续时间马尔可夫链
3. PCTL: 概率计算树逻辑（DTMC上的CTL扩展）
4. CSL: 连续随机逻辑（CTMC上的CTL扩展）

概率算子：
- P_{≥λ}[φ]: φ成立的概率至少为λ
- S_{≥λ}[φ]: 稳态概率至少为λ
- R_{≥λ}[φ]: 回报率至少为λ
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
import math


@dataclass
class DTMC:
    """
    离散时间马尔可夫链
    - states: 状态集合
    - init_states: 初始状态
    - trans_probs: 转移概率矩阵 P[s][s'] = 概率
    - labels: 状态标签
    """
    states: Set[Any]
    init_states: Set[Any]
    trans_probs: Dict[Any, Dict[Any, float]]
    labels: Dict[Any, Set[str]]


@dataclass
class CTMC:
    """
    连续时间马尔可夫链
    - states: 状态集合
    - init_states: 初始状态
    - rate_matrix: 速率矩阵 R[s][s'] = 转移速率
    - exit_rates: 退出速率 E[s]
    - labels: 状态标签
    """
    states: Set[Any]
    init_states: Set[Any]
    rate_matrix: Dict[Any, Dict[Any, float]]
    exit_rates: Dict[Any, float]
    labels: Dict[Any, Set[str]]


@dataclass
class PCTLState:
    """PCTL公式求值结果状态"""
    sat_states: Set[Any]                          # 满足公式的状态
    prob_bounds: Dict[Any, float]                  # 状态→概率下界


class ProbabilisticModelChecker:
    """
    概率模型检查器
    
    支持：
    - DTMC上的PCTL模型检查
    - CTMC上的CSL模型检查
    - 概率有界可达性
    """
    
    def __init__(self):
        self.model = None
        self.model_type = None
    
    def load_dtmc(self, dtmc: DTMC):
        """加载DTMC模型"""
        self.model = dtmc
        self.model_type = "DTMC"
        self._build_successor_map()
    
    def load_ctmc(self, ctmc: CTMC):
        """加载CTMC模型"""
        self.model = ctmc
        self.model_type = "CTMC"
        self._build_ctmc_maps()
    
    def _build_successor_map(self):
        """构建后继映射"""
        self.succ_map: Dict[Any, Set[Any]] = {}
        
        if self.model_type == "DTMC":
            for s in self.model.trans_probs:
                self.succ_map[s] = set(self.model.trans_probs[s].keys())
    
    def _build_ctmc_maps(self):
        """构建CTMC映射"""
        self.rate_map: Dict[Any, Dict[Any, float]] = {}
        self.exit_rate: Dict[Any, float] = {}
        
        if self.model_type == "CTMC":
            self.rate_map = self.model.rate_matrix
            self.exit_rate = self.model.exit_rates
    
    def eval_atomic(self, prop: str) -> Set[Any]:
        """求值原子命题"""
        if self.model_type == "DTMC":
            return {s for s, labels in self.model.labels.items() if prop in labels}
        elif self.model_type == "CTMC":
            return {s for s, labels in self.model.labels.items() if prop in labels}
        return set()
    
    # -------------------- DTMC PCTL检查 --------------------
    
    def check_P_U(
        self,
        p_set: Set[Any],
        q_set: Set[Any],
        dtmc: DTMC
    ) -> Dict[Any, float]:
        """
        检查 E[p U ≤k q] 或 A[p U ≤k q]
        返回每个状态的概率下界/上界
        
        使用动态规划计算
        P(s, q, k) = Σ_{s'} P(s,s') × P(s', q, k-1)
        """
        probs = {}
        k = len(dtmc.states)                       # 最大步数
        
        for s in dtmc.states:
            if s in q_set:
                probs[s] = 1.0
            elif s in p_set:
                # 计算直到q的概率
                prob = self._compute_until_prob(s, p_set, q_set, dtmc, k)
                probs[s] = prob
            else:
                probs[s] = 0.0
        
        return probs
    
    def _compute_until_prob(
        self,
        s: Any,
        p_set: Set[Any],
        q_set: Set[Any],
        dtmc: DTMC,
        k: int
    ) -> float:
        """计算P(s, p U q)"""
        if k == 0:
            return 1.0 if s in q_set else 0.0
        
        if s in q_set:
            return 1.0
        
        prob = 0.0
        trans = dtmc.trans_probs.get(s, {})
        
        for sp, p in trans.items():
            # 递归计算
            sub_prob = self._compute_until_prob(sp, p_set, q_set, dtmc, k - 1)
            prob += p * sub_prob
        
        return prob
    
    def check_prob_reachability(
        self,
        target_set: Set[Any],
        bound: Optional[int] = None
    ) -> Dict[Any, float]:
        """
        计算概率有界可达性
        
        Args:
            target_set: 目标状态集合
            bound: 有界深度，None表示无界
        
        Returns:
            每个状态到目标的概率
        """
        print(f"[概率检查] 可达性: {len(target_set)} 目标状态")
        
        if self.model_type != "DTMC":
            raise ValueError("仅支持DTMC")
        
        dtmc = self.model
        
        # 迭代计算不动点
        probs = {s: 1.0 if s in target_set else 0.0 for s in dtmc.states}
        
        if bound is not None:
            # 有界迭代
            for step in range(bound):
                new_probs = {}
                for s in dtmc.states:
                    if s in target_set:
                        new_probs[s] = 1.0
                    else:
                        p = 0.0
                        for sp, trans_prob in dtmc.trans_probs.get(s, {}).items():
                            p += trans_prob * probs[sp]
                        new_probs[s] = p
                probs = new_probs
        else:
            # 无界：求最大不动点
            for iteration in range(1000):
                old_probs = probs.copy()
                for s in dtmc.states:
                    if s not in target_set:
                        p = 0.0
                        for sp, trans_prob in dtmc.trans_probs.get(s, {}).items():
                            p += trans_prob * old_probs[sp]
                        probs[s] = p
                
                # 检查收敛
                if all(abs(probs[s] - old_probs[s]) < 1e-9 for s in dtmc.states):
                    print(f"[概率检查] 收敛于迭代 {iteration}")
                    break
        
        return probs
    
    def check_P_property(
        self,
        pctl_formula: str,
        threshold: float
    ) -> Tuple[bool, Dict[Any, float]]:
        """
        检查概率性质 P_{≥λ}[φ]
        
        Args:
            pctl_formula: PCTL公式，如 "P>=0.9 [F target]"
            threshold: 阈值
        
        Returns:
            (是否满足, 状态→概率映射)
        """
        print(f"[PCTL] 检查: {pctl_formula}")
        
        # 解析公式
        # 简化实现：只处理 F target 形式
        if "F" in pctl_formula:
            parts = pctl_formula.split("F")
            if len(parts) > 1:
                target_prop = parts[1].strip().strip("[]")
            else:
                target_prop = parts[0].split(">=")[-1].strip()
            
            target_set = self.eval_atomic(target_prop)
            probs = self.check_prob_reachability(target_set)
        
        elif "U" in pctl_formula:
            # Until公式
            probs = {}
        
        else:
            probs = {}
        
        # 检查是否满足阈值
        init_state = list(self.model.init_states)[0]
        init_prob = probs.get(init_state, 0.0)
        satisfies = init_prob >= threshold
        
        print(f"[PCTL] 初始概率: {init_prob:.4f}, 阈值: {threshold}")
        print(f"[PCTL] 结果: {'满足' if satisfies else '不满足'}")
        
        return satisfies, probs
    
    # -------------------- CTMC CSL检查 --------------------
    
    def compute_ctmc_steady_state(self) -> Dict[Any, float]:
        """
        计算CTMC稳态分布
        求解线性方程组 πR = 0, Σπ = 1
        """
        print("[CTMC] 计算稳态分布")
        
        if self.model_type != "CTMC":
            raise ValueError("需要CTMC模型")
        
        # 简化：返回均匀分布
        n = len(self.model.states)
        return {s: 1.0/n for s in self.model.states}
    
    def check_s_steady_state(
        self,
        target_set: Set[Any],
        threshold: float
    ) -> bool:
        """
        检查稳态概率 S_{≥λ}[φ]
        """
        print(f"[CSL] 稳态检查: φ ≥ {threshold}")
        
        steady_probs = self.compute_ctmc_steady_state()
        total_prob = sum(steady_probs.get(s, 0.0) for s in target_set)
        
        result = total_prob >= threshold
        print(f"[CSL] 稳态概率: {total_prob:.4f}, 结果: {'满足' if result else '不满足'}")
        
        return result


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("概率模型检查测试")
    print("=" * 50)
    
    # 构建简单DTMC
    states = {"s0", "s1", "s2", "s3"}
    init_states = {"s0"}
    trans_probs = {
        "s0": {"s0": 0.5, "s1": 0.5},
        "s1": {"s1": 0.3, "s2": 0.7},
        "s2": {"s2": 0.9, "s3": 0.1},
        "s3": {"s3": 1.0}
    }
    labels = {
        "s0": {"init"},
        "s2": {"target"},
        "s3": {"bad"}
    }
    
    dtmc = DTMC(states, init_states, trans_probs, labels)
    
    # 创建检查器
    checker = ProbabilisticModelChecker()
    checker.load_dtmc(dtmc)
    
    print(f"\nDTMC模型:")
    print(f"  状态数: {len(states)}")
    print(f"  初始状态: {init_states}")
    
    # 测试可达性概率
    print("\n概率可达性检查:")
    target = {"s2"}
    probs = checker.check_prob_reachability(target)
    for s, p in probs.items():
        print(f"  P(Reach {s2}) = {p:.4f}")
    
    # 测试P性质
    print("\nP性质检查:")
    checker.check_P_property("P>=0.5 [F s2]", 0.5)
    
    # 测试原子命题
    print("\n原子命题求值:")
    print(f"  target: {checker.eval_atomic('target')}")
    
    print("\n✓ 概率模型检查测试完成")
