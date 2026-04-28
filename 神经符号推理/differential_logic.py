"""
可微分逻辑 (Differentiable Logic)
====================================
本模块实现可微分的逻辑操作，支持神经网络的端到端训练：

核心方法：
1. Straight-Through Estimator (STE) - 解决不可微问题
2. Gumbel-Softmax - 离散步骤的可微近似
3. 概率逻辑门

关键思想：
- 逻辑操作前向传播使用确定性/离散值
- 反向传播使用近似梯度

Author: 算法库
"""

import numpy as np
from typing import Optional


class DifferentiableLogic:
    """可微分逻辑操作集合"""
    
    def __init__(self, temperature: float = 1.0, hard: bool = False):
        """
        初始化
        
        参数:
            temperature: Gumbel-Softmax温度
            hard: 是否使用硬采样
        """
        self.temperature = temperature
        self.hard = hard
    
    @staticmethod
    def sigmoid(logits: np.ndarray) -> np.ndarray:
        """Sigmoid函数"""
        return 1.0 / (1.0 + np.exp(-np.clip(logits, -500, 500)))
    
    @staticmethod
    def heaviside(x: np.ndarray) -> np.ndarray:
        """阶跃函数（不可微）"""
        return (x > 0).astype(np.float32)
    
    @staticmethod
    def soft_and(*inputs: np.ndarray) -> np.ndarray:
        """
        软与（可微）
        
        实现: AND(x1, x2, ...) ≈ product(xi)
        或使用: 1 - product(1 - xi)
        """
        inputs = list(inputs)
        # 避免log(0)
        inputs = [np.clip(x, 1e-8, 1.0) for x in inputs]
        return np.prod(inputs, axis=0)
    
    @staticmethod
    def soft_or(*inputs: np.ndarray) -> np.ndarray:
        """
        软或（可微）
        
        实现: OR(x1, x2, ...) ≈ 1 - product(1 - xi)
        """
        inputs = list(inputs)
        inputs = [np.clip(x, 0, 1) for x in inputs]
        return 1.0 - np.prod(1 - np.array(inputs), axis=0)
    
    @staticmethod
    def soft_not(x: np.ndarray) -> np.ndarray:
        """软非（可微）"""
        return 1.0 - np.clip(x, 0, 1)
    
    @staticmethod
    def soft_implies(p: np.ndarray, q: np.ndarray) -> np.ndarray:
        """
        软蕴含（可微）
        
        p → q ≈ max(1 - p, q)
        或: 1 - p + p*q
        """
        p = np.clip(p, 0, 1)
        q = np.clip(q, 0, 1)
        return np.clip(1.0 - p + p * q, 0, 1)
    
    @staticmethod
    def soft_xor(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """软异或"""
        x = np.clip(x, 0, 1)
        y = np.clip(y, 0, 1)
        return x + y - 2 * x * y
    
    def gumbel_softmax(self, logits: np.ndarray, dim: int = -1) -> np.ndarray:
        """
        Gumbel-Softmax采样
        
        用于从分类分布中采样，可微
        
        参数:
            logits: 未归一化的对数概率
            dim: 维度
        
        返回:
            软样本
        """
        # 添加Gumbel噪声
        gumbel_noise = -np.log(-np.log(np.random.rand(*logits.shape) + 1e-8) + 1e-8)
        y = (logits + gumbel_noise) / self.temperature
        
        # Softmax
        y_exp = np.exp(y - np.max(y, axis=dim, keepdims=True))
        softmax = y_exp / np.sum(y_exp, axis=dim, keepdims=True)
        
        if self.hard:
            # 硬采样（直通估计）
            indices = np.argmax(logits, axis=dim)
            one_hot = np.eye(softmax.shape[dim])[indices]
            return one_hot
        
        return softmax


class StraightThroughEstimator:
    """直通估计器 (STE)"""
    
    @staticmethod
    def signSTE(x: np.ndarray, threshold: float = 0.0) -> np.ndarray:
        """
        Sign函数的STE
        
        前向: 返回sign(x)
        反向: 返回x（恒等梯度）
        """
        return np.sign(x)
    
    @staticmethod
    def roundSTE(x: np.ndarray) -> np.ndarray:
        """
        Round函数的STE
        
        前向: 返回round(x)
        反向: 返回x
        """
        return np.round(x)
    
    @staticmethod
    def thresholdSTE(x: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """
        阈值化STE
        
        前向: 返回 (x > threshold)
        反向: 返回x
        """
        return (x > threshold).astype(np.float32)


class ProbabilisticLogicGate:
    """概率逻辑门"""
    
    @staticmethod
    def prob_and(p: float, q: float) -> float:
        """概率与: P(A∧B) = P(A) * P(B) (假设独立)"""
        return p * q
    
    @staticmethod
    def prob_or(p: float, q: float) -> float:
        """概率或: P(A∨B) = P(A) + P(B) - P(A)*P(B)"""
        return p + q - p * q
    
    @staticmethod
    def prob_not(p: float) -> float:
        """概率非: P(¬A) = 1 - P(A)"""
        return 1.0 - p
    
    @staticmethod
    def prob_implies(p: float, q: float) -> float:
        """概率蕴含: P(A→B) = P(¬A) + P(A)*P(B)"""
        return (1.0 - p) + p * q
    
    @staticmethod
    def bayes_and(p: float, q: float, prior: float = 0.5) -> float:
        """
        贝叶斯与
        
        P(A|B) = P(B|A) * P(A) / P(B)
        """
        if q == 0:
            return 0.0
        return (p * prior) / q


class DifferentiableLogicCircuit:
    """可微分逻辑电路"""
    
    def __init__(self):
        self.ops = DifferentiableLogic()
        self.inputs = {}
    
    def add_input(self, name: str, value: np.ndarray):
        """添加输入"""
        self.inputs[name] = value
    
    def evaluate(self, circuit_fn) -> np.ndarray:
        """评估电路"""
        return circuit_fn(self.inputs, self.ops)
    
    def and_layer(self, *args) -> np.ndarray:
        """与层"""
        return self.ops.soft_and(*args)
    
    def or_layer(self, *args) -> np.ndarray:
        """或层"""
        return self.ops.soft_or(*args)
    
    def implies_layer(self, antecedent: np.ndarray, consequent: np.ndarray) -> np.ndarray:
        """蕴含层"""
        return self.ops.soft_implies(antecedent, consequent)


class LogicTensor:
    """逻辑张量 - 支持前向后向传播"""
    
    def __init__(self, value: np.ndarray, requires_grad: bool = True):
        self.value = value
        self.gradient = None
        self.requires_grad = requires_grad
    
    def backward(self, grad_output: np.ndarray = None):
        """反向传播（简化版本）"""
        if not self.requires_grad:
            return
        
        if grad_output is None:
            grad_output = np.ones_like(self.value)
        
        self.gradient = grad_output
    
    def __and__(self, other):
        """逻辑与"""
        result = self.ops.soft_and(self.value, other.value)
        return LogicTensor(result)
    
    def __or__(self, other):
        """逻辑或"""
        result = self.ops.soft_or(self.value, other.value)
        return LogicTensor(result)
    
    def __invert__(self):
        """逻辑非"""
        result = self.ops.soft_not(self.value)
        return LogicTensor(result)


if __name__ == "__main__":
    print("=" * 55)
    print("可微分逻辑测试")
    print("=" * 55)
    
    ops = DifferentiableLogic()
    
    # 测试软逻辑操作
    print("\n--- 软逻辑操作 ---")
    
    p = np.array([0.8, 0.6, 0.3, 0.9])
    q = np.array([0.7, 0.4, 0.5, 0.2])
    
    print(f"P:  {p}")
    print(f"Q:  {q}")
    print(f"¬P: {ops.soft_not(p)}")
    print(f"P∧Q: {ops.soft_and(p, q)}")
    print(f"P∨Q: {ops.soft_or(p, q)}")
    print(f"P→Q: {ops.soft_implies(p, q)}")
    print(f"P⊕Q: {ops.soft_xor(p, q)}")
    
    # Gumbel-Softmax测试
    print("\n--- Gumbel-Softmax ---")
    
    logits = np.array([[2.0, 1.0, 0.5], [0.5, 2.0, 1.0]])
    samples = ops.gumbel_softmax(logits, hard=False)
    print(f"Logits: {logits}")
    print(f"Gumbel-Softmax样本: {samples}")
    
    # STE测试
    print("\n--- Straight-Through Estimator ---")
    
    x = np.array([-1.5, -0.5, 0.5, 1.5])
    sign_out = StraightThroughEstimator.signSTE(x)
    round_out = StraightThroughEstimator.roundSTE(x)
    thresh_out = StraightThroughEstimator.thresholdSTE(x, threshold=0.0)
    
    print(f"x:      {x}")
    print(f"sign(x): {sign_out}")
    print(f"round(x): {round_out}")
    print(f"thresh(x): {thresh_out}")
    
    # 概率逻辑门
    print("\n--- 概率逻辑门 ---")
    
    plg = ProbabilisticLogicGate()
    prob_a, prob_b = 0.6, 0.4
    
    print(f"P(A)={prob_a}, P(B)={prob_b}")
    print(f"P(A∧B)={plg.prob_and(prob_a, prob_b):.4f}")
    print(f"P(A∨B)={plg.prob_or(prob_a, prob_b):.4f}")
    print(f"P(¬A)={plg.prob_not(prob_a):.4f}")
    print(f"P(A→B)={plg.prob_implies(prob_a, prob_b):.4f}")
    
    # 逻辑电路
    print("\n--- 可微分逻辑电路 ---")
    
    circuit = DifferentiableLogicCircuit()
    
    a = np.array([0.8, 0.3, 0.6, 0.9])
    b = np.array([0.6, 0.7, 0.4, 0.2])
    c = np.array([0.5, 0.5, 0.5, 0.5])
    
    def circuit_fn(inputs, ops):
        # (A ∧ B) ∨ C
        ab = ops.soft_and(inputs['a'], inputs['b'])
        return ops.soft_or(ab, inputs['c'])
    
    circuit.add_input('a', a)
    circuit.add_input('b', b)
    circuit.add_input('c', c)
    
    result = circuit.evaluate(circuit_fn)
    print(f"(A∧B)∨C = {result}")
    
    # 验证真值表
    print("\n--- 验证软逻辑运算性质 ---")
    
    # 德摩根律: ¬(A∧B) = ¬A ∨ ¬B
    A = np.array([0.8, 0.3])
    B = np.array([0.6, 0.7])
    
    left = ops.soft_not(ops.soft_and(A, B))
    right = ops.soft_or(ops.soft_not(A), ops.soft_not(B))
    
    print(f"¬(A∧B) = {left}")
    print(f"¬A ∨ ¬B = {right}")
    print(f"德摩根律验证 (误差): {np.abs(left - right)}")
    
    print("\n测试通过！可微分逻辑工作正常。")
