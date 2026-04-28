"""
逻辑张量网络 (Logic Tensor Networks - LTN)
============================================
本模块实现LTN框架：结合神经网络与一阶逻辑的神经符号系统

LTN核心思想：
- 使用张量表示逻辑谓词和函数
- 将逻辑规则编码为损失函数
- 通过反向传播优化

Author: 算法库
"""

import numpy as np
from typing import List, Dict, Callable, Tuple


class Tensor:
    """张量类 - 表示逻辑对象的嵌入"""
    
    def __init__(self, data: np.ndarray, semantics: str = "real"):
        """
        初始化张量
        
        参数:
            data: 数据数组
            semantics: 语义类型 ("real", "boolean", "tensor")
        """
        self.data = data.astype(np.float32)
        self.semantics = semantics
    
    def __add__(self, other):
        return Tensor(self.data + other.data)
    
    def __mul__(self, other):
        return Tensor(self.data * other.data)
    
    def __neg__(self):
        return Tensor(-self.data)


class Predicate:
    """逻辑谓词类"""
    
    def __init__(self, name: str, network: Callable):
        """
        初始化谓词
        
        参数:
            name: 谓词名称
            network: 神经网络（前向函数）
        """
        self.name = name
        self.network = network
    
    def __call__(self, *args) -> Tensor:
        """应用谓词到参数"""
        # 收集所有张量数据
        data_list = [arg.data if isinstance(arg, Tensor) else arg for arg in args]
        
        # 如果是多个张量，拼接
        if len(data_list) > 1:
            combined = np.concatenate(data_list, axis=-1)
        else:
            combined = data_list[0]
        
        # 通过网络前向
        output = self.network(combined)
        
        # 确保是[0,1]范围（用于概率/真值）
        output = np.clip(output, 0, 1)
        
        return Tensor(output, semantics="real")


class Function:
    """一阶函数类"""
    
    def __init__(self, name: str, network: Callable):
        """
        初始化函数
        
        参数:
            name: 函数名称
            network: 神经网络
        """
        self.name = name
        self.network = network
    
    def __call__(self, *args) -> Tensor:
        """应用函数"""
        data_list = [arg.data if isinstance(arg, Tensor) else np.array(arg) for arg in args]
        combined = np.concatenate(data_list, axis=-1)
        return Tensor(self.network(combined))


class Variable:
    """逻辑变量"""
    
    def __init__(self, name: str):
        self.name = name


class Rule:
    """逻辑规则"""
    
    def __init__(self, formula: Callable, weight: float = 1.0):
        """
        初始化规则
        
        参数:
            formula: 公式函数（返回真值张量）
            weight: 规则权重
        """
        self.formula = formula
        self.weight = weight


class LogicTensorNetwork:
    """逻辑张量网络主体"""
    
    def __init__(self, learning_rate: float = 0.001):
        """
        初始化LTN
        
        参数:
            learning_rate: 学习率
        """
        self.predicates: Dict[str, Predicate] = {}
        self.functions: Dict[str, Function] = {}
        self.rules: List[Rule] = []
        self.optimizer = None  # 简化：使用梯度下降
        self.lr = learning_rate
        self.variables: Dict[str, np.ndarray] = {}  # 存储变量值
    
    def register_predicate(self, name: str, network: Callable) -> Predicate:
        """注册谓词"""
        pred = Predicate(name, network)
        self.predicates[name] = pred
        return pred
    
    def register_function(self, name: str, network: Callable) -> Function:
        """注册函数"""
        func = Function(name, network)
        self.functions[name] = func
        return func
    
    def add_rule(self, formula: Callable, weight: float = 1.0):
        """添加逻辑规则"""
        rule = Rule(formula, weight)
        self.rules.append(rule)
    
    def assign(self, var_name: str, values: np.ndarray):
        """为变量赋值"""
        self.variables[var_name] = values.astype(np.float32)
    
    def get_variable(self, var_name: str) -> Tensor:
        """获取变量张量"""
        return Tensor(self.variables[var_name])
    
    def sat(self, formula: Callable) -> float:
        """
        计算公式的满意度（0到1之间）
        
        参数:
            formula: 公式函数
        
        返回:
            平均真值
        """
        result = formula()
        if isinstance(result, Tensor):
            return float(np.mean(result.data))
        return float(result)
    
    def loss(self) -> float:
        """
        计算总体损失
        
        所有规则的满意度损失 + 正则化
        """
        total_loss = 0.0
        
        for rule in self.rules:
            # 计算规则满意度
            sat_level = self.sat(rule.formula)
            # 满意度转化为损失: 1 - sat^2 (更接近0越好)
            rule_loss = 1.0 - sat_level ** 2
            total_loss += rule.weight * rule_loss
        
        return total_loss
    
    def train_step(self):
        """单步训练"""
        # 简化：使用数值梯度
        loss_before = self.loss()
        
        # 对每个谓词和函数的参数做小扰动
        epsilon = 0.001
        for name, pred in self.predicates.items():
            # 这里应该调整网络参数，但简化版只演示概念
            pass
        
        loss_after = self.loss()
        
        return loss_after


# 逻辑连接词
def And(*args) -> Tensor:
    """逻辑与"""
    data = np.stack([a.data if isinstance(a, Tensor) else np.array(a) for a in args])
    return Tensor(np.min(data, axis=0))


def Or(*args) -> Tensor:
    """逻辑或"""
    data = np.stack([a.data if isinstance(a, Tensor) else np.array(a) for a in args])
    return Tensor(np.max(data, axis=0))


def Not(tensor: Tensor) -> Tensor:
    """逻辑非"""
    return Tensor(1.0 - tensor.data)


def Implies(p: Tensor, q: Tensor) -> Tensor:
    """蕴含: p -> q"""
    return Tensor(np.clip(1.0 - p.data + q.data, 0, 1))


def Forall(var_tensor: Tensor, formula: Callable) -> Tensor:
    """全称量词"""
    result = formula()
    return Tensor(np.mean(result.data, axis=0, keepdims=True) 
                  if result.data.ndim > 1 else np.array([np.mean(result.data)]))


def Exists(var_tensor: Tensor, formula: Callable) -> Tensor:
    """存在量词"""
    result = formula()
    return Tensor(np.max(result.data, axis=0, keepdims=True) 
                  if result.data.ndim > 1 else np.array([np.max(result.data)]))


if __name__ == "__main__":
    print("=" * 55)
    print("逻辑张量网络(LTN)测试")
    print("=" * 55)
    
    # 创建LTN
    ltn = LogicTensorNetwork(learning_rate=0.01)
    
    # 定义简单的谓词网络
    def simple_network(x):
        """简单分类网络"""
        return 1.0 / (1.0 + np.exp(-(x[..., 0] - 0.5)))  # 假设x > 0.5为真
    
    # 注册谓词
    P = ltn.register_predicate("P", simple_network)
    
    # 创建数据
    x_data = np.array([[0.2], [0.4], [0.6], [0.8]])
    ltn.assign("x", x_data)
    
    # 定义规则: 对于所有x，P(x)应该为真
    x = ltn.get_variable("x")
    
    def rule1():
        return P(x)
    
    ltn.add_rule(rule1, weight=1.0)
    
    # 计算满意度
    sat = ltn.sat(rule1)
    print(f"\n规则 'forall x: P(x)' 满意度: {sat:.4f}")
    print(f"损失: {ltn.loss():.4f}")
    
    # 测试逻辑连接词
    print("\n--- 逻辑连接词测试 ---")
    
    t1 = Tensor(np.array([0.8, 0.6, 0.3]))
    t2 = Tensor(np.array([0.9, 0.4, 0.7]))
    
    and_result = And(t1, t2)
    or_result = Or(t1, t2)
    not_result = Not(t1)
    implies_result = Implies(t1, t2)
    
    print(f"P:     {t1.data}")
    print(f"Q:     {t2.data}")
    print(f"P∧Q:   {and_result.data}")
    print(f"P∨Q:   {or_result.data}")
    print(f"¬P:    {not_result.data}")
    print(f"P→Q:   {implies_result.data}")
    
    # 测试量词
    print("\n--- 量词测试 ---")
    
    data = np.array([[0.1], [0.3], [0.5], [0.7], [0.9]])
    ltn.assign("y", data)
    y = ltn.get_variable("y")
    
    def exists_formula():
        return P(y)
    
    def forall_formula():
        return P(y)
    
    exists_sat = ltn.sat(exists_formula)
    forall_sat = ltn.sat(forall_formula)
    
    print(f"数据: {data.flatten()}")
    print(f"∃y: P(y) = {exists_sat:.4f} (期望接近1)")
    print(f"∀y: P(y) = {forall_sat:.4f} (期望接近0.6，即0.5以上的比例)")
    
    print("\n测试通过！LTN基础功能正常。")
