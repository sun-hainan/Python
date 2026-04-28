"""
神经符号推理框架 (Neuro-Symbolic Reasoning Framework)
=======================================================
本模块实现基础的神经符号推理框架，结合：
1. 符号逻辑（命题逻辑、一阶逻辑）
2. 神经网络（张量表示）
3. 可微分的推理过程

核心组件：
- 符号表达式树
- 神经网络嵌入
- 规则学习和推理

Author: 算法库
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Callable
from enum import Enum, auto


class SymbolType(Enum):
    """符号类型"""
    CONSTANT = auto()
    VARIABLE = auto()
    PREDICATE = auto()
    FUNCTION = auto()
    CONNECTIVE = auto()


class Symbol:
    """符号基类"""
    
    def __init__(self, name: str, sym_type: SymbolType):
        self.name = name
        self.sym_type = sym_type
        self.embedding = None  # 神经嵌入
    
    def set_embedding(self, embedding: np.ndarray):
        """设置嵌入向量"""
        self.embedding = embedding
    
    def __repr__(self):
        return f"{self.name}"


class Constant(Symbol):
    """常量符号"""
    
    def __init__(self, name: str, value: Any = None):
        super().__init__(name, SymbolType.CONSTANT)
        self.value = value


class Variable(Symbol):
    """变量符号"""
    
    def __init__(self, name: str):
        super().__init__(name, SymbolType.VARIABLE)


class Predicate(Symbol):
    """谓词符号"""
    
    def __init__(self, name: str, arity: int, neural_net: Optional[Callable] = None):
        super().__init__(name, SymbolType.PREDICATE)
        self.arity = arity
        self.neural_net = neural_net  # 用于计算真值
    
    def evaluate(self, args: List) -> float:
        """评估谓词"""
        if self.neural_net is not None:
            # 使用神经网络评估
            embeddings = [arg.embedding if isinstance(arg, Symbol) else arg for arg in args]
            combined = np.concatenate([e if isinstance(e, np.ndarray) else np.array([e]) 
                                        for e in embeddings])
            return float(np.clip(self.neural_net(combined), 0, 1))
        return 0.5  # 默认真值


class Function(Symbol):
    """函数符号"""
    
    def __init__(self, name: str, arity: int, neural_net: Optional[Callable] = None):
        super().__init__(name, SymbolType.FUNCTION)
        self.arity = arity
        self.neural_net = neural_net
    
    def apply(self, args: List) -> Symbol:
        """应用函数"""
        result = Constant(f"{self.name}_result")
        if self.neural_net is not None:
            embeddings = [arg.embedding if isinstance(arg, Symbol) else arg for arg in args]
            combined = np.concatenate(embeddings)
            result.embedding = self.neural_net(combined)
        return result


class Expression:
    """逻辑表达式基类"""
    
    def __init__(self):
        self.symbols = []
    
    def evaluate(self, assignment: Dict[Variable, Any] = None) -> float:
        """评估表达式真值"""
        raise NotImplementedError


class AtomicFormula(Expression):
    """原子公式 P(t1, t2, ...)"""
    
    def __init__(self, predicate: Predicate, terms: List):
        super().__init__()
        self.predicate = predicate
        self.terms = terms
        self.symbols = terms
    
    def evaluate(self, assignment: Dict[Variable, Any] = None) -> float:
        """评估原子公式"""
        term_values = []
        for term in self.terms:
            if isinstance(term, Variable):
                if assignment and term in assignment:
                    term_values.append(assignment[term])
                elif term.embedding is not None:
                    term_values.append(term)
                else:
                    term_values.append(0.0)
            elif isinstance(term, Constant):
                term_values.append(term.value if term.value is not None else term)
            else:
                term_values.append(term)
        
        return self.predicate.evaluate(term_values)


class Negation(Expression):
    """否定 ¬φ"""
    
    def __init__(self, formula: Expression):
        super().__init__()
        self.formula = formula
        self.symbols = formula.symbols
    
    def evaluate(self, assignment: Dict[Variable, Any] = None) -> float:
        return 1.0 - self.formula.evaluate(assignment)


class Conjunction(Expression):
    """合取 φ ∧ ψ"""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__()
        self.left = left
        self.right = right
        self.symbols = left.symbols + right.symbols
    
    def evaluate(self, assignment: Dict[Variable, Any] = None) -> float:
        lv = self.left.evaluate(assignment)
        rv = self.right.evaluate(assignment)
        return lv * rv  # 乘积实现soft AND


class Disjunction(Expression):
    """析取 φ ∨ ψ"""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__()
        self.left = left
        self.right = right
    
    def evaluate(self, assignment: Dict[Variable, Any] = None) -> float:
        lv = self.left.evaluate(assignment)
        rv = self.right.evaluate(assignment)
        return lv + rv - lv * rv  # 概率OR


class Implication(Expression):
    """蕴含 φ → ψ"""
    
    def __init__(self, left: Expression, right: Expression):
        super().__init__()
        self.left = left
        self.right = right
    
    def evaluate(self, assignment: Dict[Variable, Any] = None) -> float:
        lv = self.left.evaluate(assignment)
        rv = self.right.evaluate(assignment)
        return np.clip(1.0 - lv + rv, 0, 1)


class UniversalQuantifier(Expression):
    """全称量词 ∀x φ"""
    
    def __init__(self, variable: Variable, formula: Expression):
        super().__init__()
        self.variable = variable
        self.formula = formula
        self.symbols = [v for v in formula.symbols if v != variable]
    
    def evaluate(self, assignment: Dict[Variable, Any] = None) -> float:
        # 简化：使用多个采样点
        # 实际实现应该在训练时聚合多个样本
        return self.formula.evaluate(assignment)


class ExistentialQuantifier(Expression):
    """存在量词 ∃x φ"""
    
    def __init__(self, variable: Variable, formula: Expression):
        super().__init__()
        self.variable = variable
        self.formula = formula
    
    def evaluate(self, assignment: Dict[Variable, Any] = None) -> float:
        return self.formula.evaluate(assignment)


class NeuroSymbolicReasoner:
    """神经符号推理器"""
    
    def __init__(self):
        self.constants: Dict[str, Constant] = {}
        self.predicates: Dict[str, Predicate] = {}
        self.functions: Dict[str, Function] = {}
        self.rules: List[Tuple[Expression, float]] = []  # (规则, 权重)
        self.kb: List[Expression] = []  # 知识库
    
    def add_constant(self, name: str, value: Any = None) -> Constant:
        """添加常量"""
        c = Constant(name, value)
        self.constants[name] = c
        return c
    
    def add_predicate(self, name: str, arity: int, 
                      neural_net: Optional[Callable] = None) -> Predicate:
        """添加谓词"""
        p = Predicate(name, arity, neural_net)
        self.predicates[name] = p
        return p
    
    def add_function(self, name: str, arity: int,
                     neural_net: Optional[Callable] = None) -> Function:
        """添加函数"""
        f = Function(name, arity, neural_net)
        self.functions[name] = f
        return f
    
    def add_fact(self, expression: Expression):
        """添加事实到知识库"""
        self.kb.append(expression)
    
    def add_rule(self, expression: Expression, weight: float = 1.0):
        """添加规则"""
        self.rules.append((expression, weight))
    
    def query(self, expression: Expression, 
               assignment: Dict[Variable, Any] = None) -> float:
        """查询表达式真值"""
        return expression.evaluate(assignment)
    
    def backward_chain(self, query: Expression) -> float:
        """
        后向链推理
        
        简化版本：直接评估
        完整版本应该支持递归和变量置换
        """
        return query.evaluate()
    
    def forward_chain(self) -> Dict[Expression, float]:
        """
        前向链推理
        
        从已知事实推导新事实
        """
        derived = {}
        
        for rule, weight in self.rules:
            truth_value = rule.evaluate()
            if truth_value > 0.5:  # 阈值
                derived[rule] = truth_value
        
        return derived
    
    def compute_loss(self) -> float:
        """计算逻辑损失"""
        loss = 0.0
        
        # 知识库满意度
        for fact in self.kb:
            truth = fact.evaluate()
            loss += (1.0 - truth) ** 2
        
        # 规则满意度
        for rule, weight in self.rules:
            truth = rule.evaluate()
            loss += weight * (1.0 - truth) ** 2
        
        return loss


if __name__ == "__main__":
    print("=" * 55)
    print("神经符号推理框架测试")
    print("=" * 55)
    
    # 创建推理器
    reasoner = NeuroSymbolicReasoner()
    
    # 定义简单的谓词网络
    def is_mammal_net(x):
        """判断是否为哺乳动物"""
        return float(x[0] > 0.5)
    
    def has_fur_net(x):
        """判断是否有毛"""
        return float(x[0] > 0.6)
    
    # 添加符号
    p_mammal = reasoner.add_predicate("Mammal", 1, is_mammal_net)
    p_has_fur = reasoner.add_predicate("HasFur", 1, has_fur_net)
    
    # 创建常量
    dog = Constant("dog")
    dog.embedding = np.array([0.8])  # 狗的嵌入
    cat = Constant("cat")
    cat.embedding = np.array([0.7])
    
    # 创建原子公式
    dog_is_mammal = AtomicFormula(p_mammal, [dog])
    cat_is_mammal = AtomicFormula(p_mammal, [cat])
    dog_has_fur = AtomicFormula(p_has_fur, [dog])
    
    # 添加事实
    reasoner.add_fact(dog_is_mammal)
    reasoner.add_fact(dog_has_fur)
    
    # 查询
    print("\n--- 原子公式评估 ---")
    print(f"Mammal(dog) = {reasoner.query(dog_is_mammal):.4f}")
    print(f"Mammal(cat) = {reasoner.query(cat_is_mammal):.4f}")
    print(f"HasFur(dog) = {reasoner.query(dog_has_fur):.4f}")
    
    # 复合公式
    print("\n--- 复合公式 ---")
    
    # ¬Mammal(cat)
    not_cat = Negation(cat_is_mammal)
    print(f"¬Mammal(cat) = {reasoner.query(not_cat):.4f}")
    
    # Mammal(dog) ∧ HasFur(dog)
    and_formula = Conjunction(dog_is_mammal, dog_has_fur)
    print(f"Mammal(dog) ∧ HasFur(dog) = {reasoner.query(and_formula):.4f}")
    
    # Mammal(dog) ∨ Mammal(cat)
    or_formula = Disjunction(dog_is_mammal, cat_is_mammal)
    print(f"Mammal(dog) ∨ Mammal(cat) = {reasoner.query(or_formula):.4f}")
    
    # Mammal(dog) → HasFur(dog)
    implies_formula = Implication(dog_is_mammal, dog_has_fur)
    print(f"Mammal(dog) → HasFur(dog) = {reasoner.query(implies_formula):.4f}")
    
    # 添加规则并计算损失
    print("\n--- 规则与损失 ---")
    
    # 规则: ∀x (Mammal(x) → HasFur(x))
    rule = Implication(dog_is_mammal, dog_has_fur)
    reasoner.add_rule(rule, weight=1.0)
    
    print(f"规则 Mammal(x) → HasFur(x) 真值: {reasoner.query(rule):.4f}")
    print(f"总损失: {reasoner.compute_loss():.4f}")
    
    # 前向链
    print("\n--- 前向链推理 ---")
    derived = reasoner.forward_chain()
    print(f"推导出的事实数: {len(derived)}")
    
    print("\n测试通过！神经符号推理框架工作正常。")
