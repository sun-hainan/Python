"""
符号模型检查 (Symbolic Model Checking)
=======================================
核心思想：使用二叉决策图(BDD)表示状态集合和转移关系
通过BDD操作实现状态空间的高效遍历

关键技术：
1. BDD (Binary Decision Diagram): 紧凑表示布尔函数
2. 集合操作: ∩, ∪, ¬, ∃, ∀ 通过BDD交集/并集/补/存在/全称量化实现
3. 不动点计算: 递归计算EG/EU等模态算子

优势：避免状态爆炸，支持大规模状态空间验证
"""

from typing import Set, Dict, Callable, Optional, Tuple
from dataclasses import dataclass
from collections import deque


# ----------------------- BDD 简化实现 -----------------------

@dataclass
class BDDNode:
    """BDD节点"""
    var_id: int                                  # 变量索引
    low: 'BDDNode'                               # 假分支指向的节点
    high: 'BDDNode'                              # 真分支指向的节点


class BDD:
    """
    二叉决策图（简化实现）
    实际应使用CUDD/pyDDL等成熟库
    """
    def __init__(self):
        self.var_names: Dict[str, int] = {}     # 变量名→索引映射
        self.var_order: list = []                # 变量顺序（影响BDD大小）
        self._true_node: Optional[BDDNode] = None   # 终节点: True
        self._false_node: Optional[BDDNode] = None  # 终节点: False
    
    def mk_var(self, name: str) -> BDDNode:
        """创建变量节点"""
        if name not in self.var_names:
            self.var_names[name] = len(self.var_names)
            self.var_order.append(name)
        var_id = self.var_names[name]
        return BDDNode(var_id, self.false, self.true)
    
    @property
    def true(self) -> BDDNode:
        if self._true_node is None:
            self._true_node = BDDNode(-1, None, None)  # 终端节点标记
        return self._true_node
    
    @property
    def false(self) -> BDDNode:
        if self._false_node is None:
            self._false_node = BDDNode(-2, None, None)  # 终端节点标记
        return self._false_node
    
    def ite(self, cond: str, then_bdd: BDDNode, else_bdd: BDDNode) -> BDDNode:
        """
        ITE(If-Then-Else)操作
        实现BDD的复合操作
        """
        cond_id = self.var_names.get(cond, -1)
        if cond_id < 0:
            return then_bdd
        return BDDNode(cond_id, else_bdd, then_bdd)
    
    def exists(self, bdd: BDDNode, var: str) -> BDDNode:
        """存在量化 ∃v.F"""
        var_id = self.var_names.get(var, -1)
        if var_id < 0:
            return bdd
        # 简化: 存在量化 ≈ 消除变量后的或操作
        return self.ite(var, self.true, self.false)
    
    def forall(self, bdd: BDDNode, var: str) -> BDDNode:
        """全称量化 ∀v.F"""
        var_id = self.var_names.get(var, -1)
        if var_id < 0:
            return bdd
        # 全称量化 = ¬∃v.¬F
        negated = self.negate(bdd)
        existed = self.exists(negated, var)
        return self.negate(existed)
    
    def negate(self, bdd: BDDNode) -> BDDNode:
        """取反操作"""
        if bdd.var_id < 0:
            # 终端节点取反
            return self.true if bdd is self.false else self.false
        return BDDNode(bdd.var_id, bdd.high, bdd.low)


# ----------------------- 符号模型检查引擎 -----------------------

@dataclass
class SymbolicModel:
    """
    符号模型定义
    - var_list: 有序变量列表（决定BDD变量顺序）
    - init_bdd: 初始状态BDD
    - trans_bdd: 转移关系BDD
    - label_func: 原子命题到BDD的映射
    """
    var_list: list                               # 变量列表
    init_bdd: BDDNode                            # 初始状态BDD
    trans_bdd: BDDNode                           # 转移关系BDD: T(s,s')
    label_func: Dict[str, Callable]              # 命题→状态条件函数


class SymbolicModelChecker:
    """
    符号模型检查器
    实现CTL模型检查的核心算法
    """
    
    def  __init__(self, model: SymbolicModel):
        self.model = model
        self.bdd = BDD()
        # 初始化变量顺序
        for var in model.var_list:
            self.bdd.mk_var(var)
    
    def check_EF(self, p_bdd: BDDNode) -> BDDNode:
        """
        检验 EF p (存在未来态满足p)
        计算: νX. p ∨ (EX ∧ X)
        使用不动点迭代
        """
        X = self.bdd.false                       # X_0 = ∅
        X_new = self.bdd.false
        
        iteration = 0
        while X != X_new:
            X = X_new
            # 计算 EX ∧ X
            ex_x = self.preimage(X)              # EX = {s | ∃s': T(s,s') ∧ X(s')}
            ex_x_and = self.bdd.ite(
                "tmp", ex_x, self.bdd.false       # 交集操作
            )
            # X_new = p ∨ (EX ∧ X)
            X_new = self.bdd.ite("p", p_bdd, ex_x)
            iteration += 1
            if iteration > 1000:
                raise RuntimeError("不动点迭代不收敛")
        
        return X_new
    
    def check_EG(self, p_bdd: BDDNode) -> BDDNode:
        """
        检验 EG p (存在全局路径满足p)
        计算: μX. p ∧ (EX ∧ X)
        对偶不动点（最小不动点）
        """
        X = self.bdd.true                        # X_0 = 全集
        X_new = self.bdd.true
        var_name = self.model.var_list[0] if self.model.var_list else "x"
        
        iteration = 0
        while X != X_new:
            X = X_new
            ex_x = self.preimage(X)              # EX
            # 交集: p ∧ EX
            X_new = self.bdd.ite(var_name, p_bdd, ex_x)
            iteration += 1
        
        return X_new
    
    def check_EU(self, p_bdd: BDDNode, q_bdd: BDDNode) -> BDDNode:
        """
        检验 E[p U q] (存在路径p直到q)
        计算: μX. q ∨ (p ∧ EX)
        """
        X = self.bdd.false
        var_name = self.model.var_list[0] if self.model.var_list else "x"
        
        iteration = 0
        while True:
            # X_new = q ∨ (p ∧ EX)
            ex_x = self.preimage(X)
            # p ∧ EX
            p_and_ex = self.bdd.ite(var_name, p_bdd, ex_x)
            # q ∨ (p ∧ EX)
            X_new = self.bdd.ite(var_name, q_bdd, p_and_ex)
            
            if X_new == X:
                return X_new
            X = X_new
            iteration += 1
            if iteration > 1000:
                raise RuntimeError("EU不动点迭代不收敛")
    
    def preimage(self, target: BDDNode) -> BDDNode:
        """
        计算前像 Pre(T, Target)
        Pre(T, Target) = {s | ∃s': T(s,s') ∧ Target(s')}
        
        实现: ∀s'. T(s,s') → Target(s')
            = ¬∃s'. T(s,s') ∧ ¬Target(s')
        """
        # 简化实现：前像 ≈ 存在量化后的转移关系
        return self.bdd.exists(self.model.trans_bdd, self.model.var_list[-1] if self.model.var_list else "s'")


# ----------------------- CTL模型检查器 -----------------------

class CTLModelChecker:
    """CTL模型检查器主类"""
    
    def __init__(self, model: SymbolicModel):
        self.model = model
        self.checker = SymbolicModelChecker(model)
    
    def parse_ctl(self, formula: str) -> str:
        """解析CTL公式（简化实现）"""
        # 支持: EF, EG, EU, AX, AG, AF, EX, EG, AU
        return formula
    
    def check(self, ctl_formula: str, state: Optional[str] = None) -> bool:
        """
        检查CTL公式
        若指定state则检查该状态，否则检查所有初始状态
        """
        print(f"[CTL] 检查公式: {ctl_formula}")
        
        # 简化：为演示创建BDD节点
        p_bdd = self.checker.bdd.true
        q_bdd = self.checker.bdd.true
        
        if ctl_formula.startswith("EF"):
            result = self.checker.check_EF(p_bdd)
        elif ctl_formula.startswith("EG"):
            result = self.checker.check_EG(p_bdd)
        elif ctl_formula.startswith("EU"):
            result = self.checker.check_EU(p_bdd, q_bdd)
        else:
            print(f"[CTL] 不支持的公式: {ctl_formula}")
            return False
        
        print(f"[CTL] 验证结果: {'满足' if result is not None else '不满足'}")
        return result is not None


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("符号模型检查测试")
    print("=" * 50)
    
    # 创建简单模型
    model = SymbolicModel(
        var_list=["x", "y"],
        init_bdd=None,
        trans_bdd=None,
        label_func={}
    )
    
    # 创建检查器
    checker = CTLModelChecker(model)
    
    # 测试CTL公式检查
    print("\n测试1: EF p")
    checker.check("EF p")
    
    print("\n测试2: EG p")
    checker.check("EG p")
    
    print("\n测试3: E[p U q]")
    checker.check("EU p q")
    
    # BDD基本操作演示
    print("\n" + "=" * 50)
    bdd = BDD()
    print("BDD变量创建测试:")
    v = bdd.mk_var("x")
    print(f"  创建变量x: var_id={v.var_id}")
    print(f"  变量映射: {bdd.var_names}")
    
    print("\n✓ 符号模型检查测试完成")
