"""
交互式定理证明框架 (Interactive Theorem Prover Framework)
=====================================================
功能：提供交互式定理证明的基础框架
支持策略(Tactics)、证明脚本、证明状态管理

核心组件：
1. ProofState: 证明状态
   - goals: 待证目标栈
   - context: 当前上下文
   - assumptions: 假设
2. Tactic: 证明策略
   - intro: 引入变量/假设
   - apply: 应用定理/引理
   - split: 拆分复合目标
   - solve: 求解目标
3. Theorem: 已证明的定理
4. ProofScript: 证明脚本

策略模式：
- primitive tactics: 基本策略
- derived tactics: 组合策略
- automation: 自动证明策略
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import re


@dataclass
class Term:
    """项"""
    kind: str                                     # var, const, app, abs, let
    name: str = ""
    args: List['Term'] = field(default_factory=list)
    body: Optional['Term'] = None
    
    def __str__(self):
        if self.kind == "var":
            return self.name
        elif self.kind == "const":
            return self.name
        elif self.kind == "app":
            args_str = " ".join(str(a) for a in self.args)
            return f"({self.name} {args_str})"
        elif self.kind == "abs":
            return f"(λ{self.name}. {self.body})"
        return "?"


@dataclass
class Formula:
    """公式"""
    kind: str                                     # atom, and, or, implies, not, forall, exists
    name: str = ""                                # 原子名
    left: Optional['Formula'] = None
    right: Optional['Formula'] = None
    child: Optional['Formula'] = None
    var: str = ""                                 # 量词变量
    term: Optional[Term] = None
    
    def __str__(self):
        if self.kind == "atom":
            return self.name
        elif self.kind == "and":
            return f"({self.left} ∧ {self.right})"
        elif self.kind == "or":
            return f"({self.left} ∨ {self.right})"
        elif self.kind == "implies":
            return f"({self.left} → {self.right})"
        elif self.kind == "not":
            return f"¬{self.child}"
        elif self.kind == "forall":
            return f"∀{self.var}.{self.child}"
        elif self.kind == "exists":
            return f"∃{self.var}.{self.child}"
        return "?"


@dataclass
class Goal:
    """
    证明目标
    
    - conclusion: 待证结论
    - hypotheses: 假设列表
    - context: 上下文（变量绑定等）
    """
    conclusion: Formula
    hypotheses: List[Formula] = field(default_factory=list)
    context: Dict[str, Term] = field(default_factory=dict)
    
    def __str__(self):
        hyps = ",\n  ".join(str(h) for h in self.hypotheses) if self.hypotheses else "无"
        return f"目标:\n  假设: {hyps}\n  结论: {self.conclusion}"


@dataclass
class ProofState:
    """
    证明状态
    
    - goals: 目标栈
    - theorems: 已证明的定理库
    - proof_term: 当前证明项
    """
    goals: List[Goal] = field(default_factory=list)
    theorems: Dict[str, Formula] = field(default_factory=dict)
    proof_term: Optional[Term] = None
    
    def current_goal(self) -> Optional[Goal]:
        """获取当前目标"""
        return self.goals[-1] if self.goals else None
    
    def is_complete(self) -> bool:
        """检查证明是否完成"""
        return len(self.goals) == 0


@dataclass
class TacticResult:
    """策略结果"""
    success: bool
    new_state: Optional[ProofState] = None
    message: str = ""
    proof_term: Optional[Term] = None


class Tactic:
    """
    证明策略基类
    
    策略将证明状态映射到新的证明状态
    """
    
    def __init__(self, name: str):
        self.name = name
    
    def apply(self, state: ProofState) -> TacticResult:
        """应用策略"""
        raise NotImplementedError
    
    def __str__(self):
        return self.name


class IntroTactic(Tactic):
    """引入策略 - 引入假设或变量"""
    
    def __init__(self, name: str = None):
        super().__init__(name or "intro")
    
    def apply(self, state: ProofState) -> TacticResult:
        """引入变量"""
        goal = state.current_goal()
        if not goal:
            return TacticResult(False, message="没有当前目标")
        
        conclusion = goal.conclusion
        
        if conclusion.kind == "implies":
            # 引入蕴含前件作为新假设
            new_hyp = conclusion.left
            new_conc = conclusion.right
            
            # 创建新目标
            new_goal = Goal(
                conclusion=new_conc,
                hypotheses=goal.hypotheses + [new_hyp],
                context=goal.context.copy()
            )
            
            new_state = ProofState(
                goals=state.goals[:-1] + [new_goal],
                theorems=state.theorems.copy()
            )
            
            return TacticResult(True, new_state, f"引入假设 {new_hyp}")
        
        elif conclusion.kind == "forall":
            # 引入全称量词变量
            new_conc = conclusion.child
            
            new_goal = Goal(
                conclusion=new_conc,
                hypotheses=goal.hypotheses.copy(),
                context=goal.context.copy()
            )
            
            new_state = ProofState(
                goals=state.goals[:-1] + [new_goal],
                theorems=state.theorems.copy()
            )
            
            return TacticResult(True, new_state, f"引入变量 {conclusion.var}")
        
        elif conclusion.kind == "not":
            # ¬A → 引入A作为假设
            new_hyp = conclusion.child
            
            new_goal = Goal(
                conclusion=Formula(kind="atom", name="⊥"),  # 假
                hypotheses=goal.hypotheses + [new_hyp],
                context=goal.context.copy()
            )
            
            new_state = ProofState(
                goals=state.goals[:-1] + [new_goal],
                theorems=state.theorems.copy()
            )
            
            return TacticResult(True, new_state, f"引入假设 {new_hyp}")
        
        return TacticResult(False, message="无法引入")


class ApplyTactic(Tactic):
    """应用策略 - 应用定理或假设"""
    
    def __init__(self, theorem_name: str):
        super().__init__(f"apply {theorem_name}")
        self.theorem_name = theorem_name
    
    def apply(self, state: ProofState) -> TacticResult:
        """应用定理"""
        goal = state.current_goal()
        if not goal:
            return TacticResult(False, message="没有当前目标")
        
        if self.theorem_name not in state.theorems:
            return TacticResult(False, message=f"定理 {self.theorem_name} 未找到")
        
        theorem = state.theorems[self.theorem_name]
        
        # 简化：直接使用定理作为结论
        new_goal = Goal(
            conclusion=theorem,
            hypotheses=goal.hypotheses.copy(),
            context=goal.context.copy()
        )
        
        new_state = ProofState(
            goals=state.goals[:-1] + [new_goal],
            theorems=state.theorems.copy()
        )
        
        return TacticResult(True, new_state, f"应用定理 {self.theorem_name}")


class SplitTactic(Tactic):
    """拆分策略 - 拆分合取目标"""
    
    def __init__(self):
        super().__init__("split")
    
    def apply(self, state: ProofState) -> TacticResult:
        """拆分合取目标"""
        goal = state.current_goal()
        if not goal:
            return TacticResult(False, message="没有当前目标")
        
        conclusion = goal.conclusion
        
        if conclusion.kind == "and":
            # 拆分为两个子目标
            left_goal = Goal(
                conclusion=conclusion.left,
                hypotheses=goal.hypotheses.copy(),
                context=goal.context.copy()
            )
            right_goal = Goal(
                conclusion=conclusion.right,
                hypotheses=goal.hypotheses.copy(),
                context=goal.context.copy()
            )
            
            new_state = ProofState(
                goals=state.goals[:-1] + [left_goal, right_goal],
                theorems=state.theorems.copy()
            )
            
            return TacticResult(True, new_state, "拆分为两个子目标")
        
        return TacticResult(False, message="目标不是合取")


class AssumeTactic(Tactic):
    """假设策略 - 使用假设证明"""
    
    def __init__(self, hyp_name: str):
        super().__init__(f"assume {hyp_name}")
        self.hyp_name = hyp_name
    
    def apply(self, state: ProofState) -> TacticResult:
        """使用假设"""
        goal = state.current_goal()
        if not goal:
            return TacticResult(False, message="没有当前目标")
        
        # 检查假设是否存在
        for hyp in goal.hypotheses:
            if hyp.name == self.hyp_name or str(hyp) == self.hyp_name:
                # 检查假设是否与结论匹配
                if hyp == goal.conclusion:
                    # 证明完成
                    new_state = ProofState(
                        goals=state.goals[:-1],
                        theorems=state.theorems.copy()
                    )
                    return TacticResult(True, new_state, f"使用假设 {self.hyp_name}")
        
        return TacticResult(False, message=f"假设 {self.hyp_name} 不存在或不匹配")


class AutoTactic(Tactic):
    """自动证明策略"""
    
    def __init__(self):
        super().__init__("auto")
    
    def apply(self, state: ProofState) -> TacticResult:
        """自动求解"""
        goal = state.current_goal()
        if not goal:
            return TacticResult(False, message="没有当前目标")
        
        # 简化：检查是否可以直接使用假设
        conclusion = goal.conclusion
        
        for hyp in goal.hypotheses:
            if hyp == conclusion:
                new_state = ProofState(
                    goals=state.goals[:-1],
                    theorems=state.theorems.copy()
                )
                return TacticResult(True, new_state, "auto: 使用假设")
        
        return TacticResult(False, message="auto: 无法自动求解")


class ProofScript:
    """
    证明脚本
    
    包含策略序列
    """
    
    def __init__(self, name: str):
        self.name = name
        self.tactics: List[Tactic] = []
    
    def add(self, tactic: Tactic):
        """添加策略"""
        self.tactics.append(tactic)
    
    def execute(self, state: ProofState) -> TacticResult:
        """执行证明脚本"""
        current_state = state
        
        for tactic in self.tactics:
            result = tactic.apply(current_state)
            
            if not result.success:
                return TacticResult(
                    False, 
                    current_state,
                    f"策略 {tactic.name} 失败: {result.message}"
                )
            
            current_state = result.new_state
            
            if current_state.is_complete():
                return TacticResult(True, current_state, "证明完成")
        
        return TacticResult(True, current_state, "脚本执行完成")


class InteractiveProver:
    """
    交互式定理证明器
    """
    
    def __init__(self):
        self.state: Optional[ProofState] = None
        self.proof_scripts: Dict[str, ProofScript] = {}
    
    def start_proof(self, goal: Goal):
        """开始证明"""
        self.state = ProofState(goals=[goal])
        print(f"\n[证明器] 开始证明")
        print(self.state.current_goal())
    
    def run_tactic(self, tactic: Tactic) -> bool:
        """运行策略"""
        if not self.state:
            print("[证明器] 没有活动证明")
            return False
        
        result = tactic.apply(self.state)
        
        if result.success:
            self.state = result.new_state
            print(f"[证明器] ✓ {result.message}")
            
            if self.state.is_complete():
                print("[证明器] ✓ 证明完成!")
                return True
            else:
                print(self.state.current_goal())
        else:
            print(f"[证明器] ✗ {result.message}")
        
        return result.success
    
    def add_theorem(self, name: str, formula: Formula):
        """添加定理"""
        if self.state and self.state.is_complete():
            self.state.theorems[name] = formula
            print(f"[证明器] 注册定理: {name} : {formula}")
    
    def prove(self, name: str, formula: Formula, script: ProofScript) -> bool:
        """
        证明定理
        
        Args:
            name: 定理名
            formula: 定理公式
            script: 证明脚本
        """
        print(f"\n{'='*50}")
        print(f"证明定理: {name}")
        print(f"公式: {formula}")
        print(f"{'='*50}")
        
        # 创建目标
        goal = Goal(conclusion=formula)
        
        # 开始证明
        self.start_proof(goal)
        
        # 执行脚本
        result = script.execute(self.state)
        
        if result.success and self.state.is_complete():
            self.add_theorem(name, formula)
            print(f"\n✓ 定理 {name} 证明成功")
            return True
        else:
            print(f"\n✗ 证明失败: {result.message}")
            return False


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("交互式定理证明器测试")
    print("=" * 50)
    
    prover = InteractiveProver()
    
    # 创建定理: A → A
    theorem1 = Formula(kind="implies", 
                       left=Formula(kind="atom", name="A"),
                       right=Formula(kind="atom", name="A"))
    
    # 创建证明脚本
    script = ProofScript("trivial")
    script.add(IntroTactic())                     # 引入假设A
    script.add(AssumeTactic("A"))                # 使用假设A
    
    # 证明
    prover.prove("trivial", theorem1, script)
    
    # 测试: A ∧ B → A
    print("\n" + "=" * 50)
    theorem2 = Formula(
        kind="implies",
        left=Formula(kind="and",
                    left=Formula(kind="atom", name="A"),
                    right=Formula(kind="atom", name="B")),
        right=Formula(kind="atom", name="A")
    )
    
    script2 = ProofScript("conj_left")
    script2.add(IntroTactic())                   # 引入A∧B作为假设
    script2.add(AssumeTactic("A ∧ B"))           # 使用假设A∧B
    
    prover.prove("conj_left", theorem2, script2)
    
    print("\n✓ 交互式定理证明器测试完成")
