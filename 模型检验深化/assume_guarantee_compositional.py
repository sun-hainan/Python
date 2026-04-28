"""
组合Assume-Guarantee (Compositional Assume-Guarantee Reasoning)
==============================================================
功能：实现组合验证框架，支持多组件系统的增量验证
基于假设-保证推理规则的组合扩展

核心思想：
1. 将大系统分解为小组件
2. 对每个组件独立验证
3. 使用假设-保证三元组组合验证结果
4. 支持递归验证和不动点计算

规则：
- 基础规则: M ⊨ G  ⟺  ⟨true⟩M⟨G⟩
- 乐观规则: M ⊨ A → G  ⟺  ⟨A⟩M⟨G⟩
- 组合规则: ⟨A⟩M⟨G⟩ ∧ ⟨B⟩N⟨H⟩ ⇒ ⟨A⟩M‖N⟨G ∧ H⟩
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import deque


@dataclass
class ComponentDef:
    """
    组件定义
    - name: 组件名
    - local_vars: 本地变量
    - interface_vars: 接口变量
    - init: 初始条件
    - trans: 转移关系
    - guarantee: 保证条件
    """
    name: str
    local_vars: Set[str] = field(default_factory=set)
    interface_vars: Set[str] = field(default_factory=set)
    init: str = "true"
    trans: str = "true"
    guarantee: str = "true"


@dataclass
class AGTriple:
    """
    Assume-Guarantee三元组
    """
    assumption: str                               # 环境假设
    component: str                               # 组件名
    guarantee: str                                # 保证条件
    context: Set[str] = field(default_factory=set)  # 组件集合


@dataclass
class CompositionResult:
    """组合结果"""
    composed_component: str
    composed_guarantee: str
    new_assumptions: List[str] = field(default_factory=list)


class CompositionalAGVerifier:
    """
    组合Assume-Guarantee验证器
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentDef] = {}
        self.triples: List[AGTriple] = []
        self.composition_graph: Dict[str, Set[str]] = {}
    
    def add_component(self, comp: ComponentDef):
        """添加组件"""
        self.components[comp.name] = comp
        self.composition_graph[comp.name] = set()
        print(f"[组合AG] 添加组件: {comp.name}")
    
    def set_interface(self, comp1: str, comp2: str):
        """设置组件接口连接"""
        if comp1 in self.composition_graph and comp2 in self.components:
            self.composition_graph[comp1].add(comp2)
            self.composition_graph[comp2].add(comp1)
    
    def verify_triple(self, triple: AGTriple) -> bool:
        """
        验证Assume-Guarantee三元组
        
        验证 ⟨A⟩M⟨G⟩ 即：
        在假设A成立时，组件M满足保证G
        """
        print(f"\n[组合AG] 验证: ⟨{triple.assumption}⟩ {triple.component} ⟨{triple.guarantee}⟩")
        
        comp = self.components.get(triple.component)
        if not comp:
            print(f"[组合AG] 错误: 组件 {triple.component} 不存在")
            return False
        
        # 简化验证：检查蕴含关系
        # 实际应用中调用模型检查器
        result = self._check_entailment(comp, triple.assumption, triple.guarantee)
        
        if result:
            print(f"[组合AG] ✓ 验证通过")
        else:
            print(f"[组合AG] ✗ 验证失败")
        
        return result
    
    def _check_entailment(
        self,
        comp: ComponentDef,
        assumption: str,
        guarantee: str
    ) -> bool:
        """
        检查蕴含: A ∧ trans → G
        
        简化实现：假设验证通过
        """
        print(f"[组合AG] 检查蕴含: ({assumption} ∧ {comp.trans}) → {guarantee}")
        
        # 简化：只要 guarantee 不是 false 就通过
        if guarantee == "false":
            return False
        
        return True
    
    def generate_assumption(
        self,
        target_comp: str,
        other_components: Set[str]
    ) -> str:
        """
        生成对目标组件的假设
        
        基于其他组件的保证生成假设
        
        Args:
            target_comp: 目标组件名
            other_components: 其他组件集合
        
        Returns:
            生成的假设
        """
        print(f"[组合AG] 为 {target_comp} 生成假设")
        
        assumption_parts = []
        
        for other in other_components:
            if other == target_comp:
                continue
            
            comp = self.components.get(other)
            if comp and comp.guarantee != "true":
                assumption_parts.append(comp.guarantee)
        
        if assumption_parts:
            assumption = " ∧ ".join(assumption_parts)
        else:
            assumption = "true"
        
        print(f"[组合AG] 生成假设: {assumption}")
        return assumption
    
    def compose_components(
        self,
        comp1: str,
        comp2: str
    ) -> CompositionResult:
        """
        组合两个组件
        
        组合规则：
        ⟨A⟩M⟨G⟩ ∧ ⟨B⟩N⟨H⟩  ⇒  ⟨A⟩M‖N⟨G ∧ H⟩
        
        Args:
            comp1: 组件1
            comp2: 组件2
        
        Returns:
            组合结果
        """
        print(f"\n[组合AG] 组合 {comp1} || {comp2}")
        
        c1 = self.components[comp1]
        c2 = self.components[comp2]
        
        # 组合变量
        combined_vars = c1.local_vars | c2.local_vars | c1.interface_vars | c2.interface_vars
        
        # 组合保证
        guarantees = []
        if c1.guarantee != "true":
            guarantees.append(c1.guarantee)
        if c2.guarantee != "true":
            guarantees.append(c2.guarantee)
        
        composed_guarantee = " ∧ ".join(guarantees) if guarantees else "true"
        
        # 生成新组件名
        new_name = f"{comp1}_AND_{comp2}"
        
        # 创建新组件
        new_comp = ComponentDef(
            name=new_name,
            local_vars=combined_vars,
            guarantee=composed_guarantee
        )
        self.components[new_name] = new_comp
        
        # 新组件的假设：来自两个子组件的假设
        new_assumptions = []
        for triple in self.triples:
            if triple.component == comp1 or triple.component == comp2:
                new_assumptions.append(triple.assumption)
        
        return CompositionResult(
            composed_component=new_name,
            composed_guarantee=composed_guarantee,
            new_assumptions=new_assumptions
        )
    
    def circular_verification(
        self,
        target_components: List[str],
        global_property: str
    ) -> bool:
        """
        循环组合验证
        
        迭代过程：
        1. 初始化所有假设为true
        2. 对每个组件验证三元组
        3. 使用其他组件的保证更新假设
        4. 重复直到收敛
        
        Args:
            target_components: 目标组件列表
            global_property: 全局性质
        
        Returns:
            是否验证成功
        """
        print(f"\n{'='*50}")
        print(f"[循环组合AG] 验证: {global_property}")
        print(f"{'='*50}")
        
        # 初始化假设
        assumptions: Dict[str, str] = {comp: "true" for comp in target_components}
        
        for iteration in range(20):
            print(f"\n[循环组合AG] 迭代 {iteration + 1}")
            
            changed = False
            
            for comp in target_components:
                old_assume = assumptions[comp]
                
                # 使用其他组件的保证生成新假设
                other_comps = set(target_components) - {comp}
                new_assume = self.generate_assumption(comp, other_comps)
                assumptions[comp] = new_assume
                
                if old_assume != new_assume:
                    changed = True
                
                # 验证三元组
                triple = AGTriple(
                    assumption=new_assume,
                    component=comp,
                    guarantee=self.components[comp].guarantee,
                    context=set(target_components)
                )
                self.triples.append(triple)
                
                if not self.verify_triple(triple):
                    print(f"[循环组合AG] ✗ 验证失败!")
                    return False
            
            if not changed:
                print(f"[循环组合AG] ✓ 假设收敛，验证成功")
                return True
        
        print(f"[循环组合AG] ✗ 迭代不收敛")
        return False
    
    def incremental_verification(
        self,
        components_to_add: List[str],
        global_property: str
    ) -> bool:
        """
        增量验证
        
        当系统扩展时，渐进地验证新组件
        
        Args:
            components_to_add: 要添加的组件列表
            global_property: 全局性质
        
        Returns:
            验证是否成功
        """
        print(f"\n[增量验证] 添加 {len(components_to_add)} 个组件")
        
        verified = set()
        
        for comp in components_to_add:
            print(f"\n[增量验证] 添加组件: {comp}")
            
            # 生成假设（基于已验证组件）
            if verified:
                assumption = self.generate_assumption(comp, verified)
            else:
                assumption = "true"
            
            # 验证新组件
            triple = AGTriple(
                assumption=assumption,
                component=comp,
                guarantee=self.components[comp].guarantee
            )
            self.triples.append(triple)
            
            if not self.verify_triple(triple):
                return False
            
            verified.add(comp)
            
            # 尝试组合验证
            if len(verified) > 1:
                comp_list = list(verified)
                if not self.circular_verification(comp_list, global_property):
                    return False
        
        return True


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("组合Assume-Guarantee验证测试")
    print("=" * 50)
    
    # 创建验证器
    verifier = CompositionalAGVerifier()
    
    # 定义组件
    comp_a = ComponentDef(
        name="A",
        local_vars={"x"},
        guarantee="x >= 0"
    )
    
    comp_b = ComponentDef(
        name="B",
        local_vars={"y"},
        guarantee="y >= 0"
    )
    
    comp_c = ComponentDef(
        name="C",
        local_vars={"z"},
        guarantee="z >= 0"
    )
    
    verifier.add_component(comp_a)
    verifier.add_component(comp_b)
    verifier.add_component(comp_c)
    
    # 设置接口
    verifier.set_interface("A", "B")
    verifier.set_interface("B", "C")
    
    # 测试1: 验证三元组
    print("\n--- 测试1: 三元组验证 ---")
    triple = AGTriple(
        assumption="true",
        component="A",
        guarantee="x >= 0"
    )
    verifier.verify_triple(triple)
    
    # 测试2: 循环验证
    print("\n--- 测试2: 循环组合验证 ---")
    result = verifier.circular_verification(
        ["A", "B", "C"],
        "x >= 0 ∧ y >= 0 ∧ z >= 0"
    )
    print(f"循环验证结果: {'成功' if result else '失败'}")
    
    # 测试3: 增量验证
    print("\n--- 测试3: 增量验证 ---")
    verifier2 = CompositionalAGVerifier()
    verifier2.add_component(comp_a)
    verifier2.add_component(comp_b)
    verifier2.add_component(comp_c)
    
    result = verifier2.incremental_verification(
        ["A", "B", "C"],
        "x >= 0 ∧ y >= 0"
    )
    print(f"增量验证结果: {'成功' if result else '失败'}")
    
    print("\n✓ 组合Assume-Guarantee验证测试完成")
