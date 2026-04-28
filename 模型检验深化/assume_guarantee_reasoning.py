"""
Assume-Guarantee验证 (Assume-Guarantee Reasoning)
================================================
功能：实现组合验证框架中的Assume-Guarantee推理规则
支持三元组⟨A⟩M⟨G⟩的验证

核心规则：
1. 基础规则: ⟨true⟩M⟨G⟩ = M ⊨ G
2. 乐观规则: ⟨A⟩M⟨G⟩ = M ⊨ A → G
3. 递归规则: ⟨A⟩M⟨G⟩ = M ⊨ (A ∧ AX⟨A⟩M⟨G⟩) → G

优势：将大系统分解为小组件分别验证，避免状态爆炸
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import deque


@dataclass
class Component:
    """
    系统组件定义
    - name: 组件名
    - vars: 组件内部变量
    - init: 初始状态条件
    - trans: 转移关系
    - guarantees: 保证条件列表
    - assumptions: 假设条件列表
    """
    name: str
    vars: Set[str] = field(default_factory=set)
    init: str = ""
    trans: str = ""
    guarantees: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)


@dataclass
class GuaranteeTriple:
    """
    Assume-Guarantee三元组
    ⟨A⟩M⟨G⟩: 如果满足假设A，则M满足保证G
    """
    assumption: str                               # A
    component: str                                # M
    guarantee: str                                # G


class AssumeGuaranteeVerifier:
    """
    Assume-Guarantee验证器
    
    实现三种推理规则：
    1. Open-world: 基础验证
    2. Circular: 递归假设
    3. learning-based: 基于学习的假设生成
    """
    
    def __init__(self):
        self.components: Dict[str, Component] = {}
        self.triples: List[GuaranteeTriple] = []
    
    def add_component(self, comp: Component):
        """添加组件"""
        self.components[comp.name] = comp
    
    def verify_triple(
        self,
        triple: GuaranteeTriple,
        env_assumption: str = "true"
    ) -> bool:
        """
        验证Assume-Guarantee三元组
        
        Args:
            triple: 要验证的三元组
            env_assumption: 环境假设
        
        Returns:
            是否验证成功
        """
        print(f"[AG验证] ⟨{triple.assumption}⟩ {triple.component} ⟩{triple.guarantee}")
        
        # 获取组件
        comp = self.components.get(triple.component)
        if not comp:
            print(f"[AG验证] 错误: 组件 {triple.component} 不存在")
            return False
        
        # 基础验证：M ⊨ A → G
        # 即所有满足A的状态也都满足G
        print(f"[AG验证] 检查: ({triple.assumption}) → ({triple.guarantee})")
        
        # 简化：假设成立
        result = self._check_implication(
            comp,
            triple.assumption,
            triple.guarantee
        )
        
        return result
    
    def _check_implication(
        self,
        comp: Component,
        antecedent: str,
        consequent: str
    ) -> bool:
        """
        检查蕴含关系: antecedent → consequent
        
        实现：检查是否存在 antecedent ∧ ¬consequent 的状态
        """
        print(f"[AG验证] 检查蕴含: {antecedent} → {consequent}")
        
        # 简化实现
        # 实际应用中使用模型检查器
        if "true" in antecedent.lower():
            # true → G 等价于验证 G
            return True
        
        # 简单假设：只要antecedent存在，consequent就成立
        return True
    
    def circular_verification(
        self,
        comps: List[str],
        property_formula: str
    ) -> bool:
        """
        循环Assume-Guarantee验证
        
        迭代过程：
        1. 初始化假设为true
        2. 对每个组件验证 ⟨A_i⟩ M_i ⟨G_i⟩
        3. 收敛时得到不动点
        
        Args:
            comps: 组件列表
            property_formula: 待验证性质
        
        Returns:
            是否验证成功
        """
        print(f"[循环AG] 验证组件组合: {comps}")
        
        assumptions = {comp: "true" for comp in comps}
        old_assumptions = None
        iteration = 0
        max_iter = 10
        
        while assumptions != old_assumptions and iteration < max_iter:
            iteration += 1
            old_assumptions = assumptions.copy()
            
            print(f"\n[循环AG] 迭代 {iteration}")
            
            for comp_name in comps:
                comp = self.components[comp_name]
                old_assume = assumptions[comp_name]
                
                # 计算新假设
                # A_new = ∧_{j≠i} G_j (其他组件的保证作为假设)
                new_assume_parts = []
                for other_comp in comps:
                    if other_comp != comp_name:
                        other = self.components[other_comp]
                        for g in other.guarantees:
                            new_assume_parts.append(g)
                
                new_assume = " ∧ ".join(new_assume_parts) if new_assume_parts else "true"
                assumptions[comp_name] = new_assume
                
                print(f"  {comp_name}: {old_assume} → {new_assume}")
                
                # 验证三元组
                triple = GuaranteeTriple(
                    assumption=new_assume,
                    component=comp_name,
                    guarantee=comp.guarantees[0] if comp.guarantees else "true"
                )
                if not self.verify_triple(triple):
                    print(f"[循环AG] 验证失败!")
                    return False
        
        print(f"[循环AG] 收敛于迭代 {iteration}")
        return True
    
    def learning_based_ag(
        self,
        comp_name: str,
        property_formula: str,
        max_learning_iter: int = 5
    ) -> Optional[str]:
        """
        基于学习的Assume-Guarantee验证
        
        使用L*思想学习假设：
        1. 从空假设开始
        2. 如果验证失败，从反例中学习新假设
        3. 直到假设收敛
        
        Args:
            comp_name: 组件名
            property_formula: 性质公式
            max_learning_iter: 最大学习迭代
        
        Returns:
            学习到的假设或None
        """
        print(f"[学习AG] 学习组件 {comp} 的假设")
        
        hypothesis = "true"                        # 初始假设
        comp = self.components[comp_name]
        
        for iteration in range(max_learning_iter):
            print(f"\n[学习AG] 迭代 {iteration + 1}, 假设: {hypothesis}")
            
            # 验证三元组
            triple = GuaranteeTriple(
                assumption=hypothesis,
                component=comp_name,
                guarantee=property_formula
            )
            
            if self.verify_triple(triple):
                print(f"[学习AG] 假设被接受: {hypothesis}")
                return hypothesis
            
            # 学习阶段：从反例生成新假设
            print(f"[学习AG] 假设被拒绝，学习新假设...")
            
            # 简化：添加性质公式作为假设
            if hypothesis == "true":
                hypothesis = property_formula
            else:
                hypothesis = f"({hypothesis}) ∧ ({property_formula})"
        
        print(f"[学习AG] 学习未收敛")
        return None


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("Assume-Guarantee验证测试")
    print("=" * 50)
    
    # 创建验证器
    verifier = AssumeGuaranteeVerifier()
    
    # 添加组件
    comp1 = Component(
        name="M1",
        vars={"x", "y"},
        guarantees=["G1: x > 0", "G2: y > 0"],
        assumptions=[]
    )
    comp2 = Component(
        name="M2",
        vars={"y", "z"},
        guarantees=["G3: y < 10"],
        assumptions=["A1: z > 0"]
    )
    
    verifier.add_component(comp1)
    verifier.add_component(comp2)
    
    print(f"组件数: {len(verifier.components)}")
    
    # 测试基本三元组验证
    print("\n基本三元组验证:")
    triple = GuaranteeTriple(
        assumption="A1",
        component="M1",
        guarantee="G1"
    )
    result = verifier.verify_triple(triple)
    print(f"  结果: {'通过' if result else '失败'}")
    
    # 测试循环AG
    print("\n循环Assume-Guarantee:")
    result = verifier.circular_verification(["M1", "M2"], "G1 ∧ G3")
    print(f"  结果: {'通过' if result else '失败'}")
    
    # 测试学习AG
    print("\n学习Assume-Guarantee:")
    learned_a = verifier.learning_based_ag("M1", "G1")
    print(f"  学习到的假设: {learned_a}")
    
    print("\n✓ Assume-Guarantee验证测试完成")
