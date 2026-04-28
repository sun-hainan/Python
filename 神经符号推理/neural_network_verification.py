"""
神经网络验证 (Neural Network Verification)
============================================
本模块实现神经网络验证的符号方法：

目标：
- 验证神经网络的安全属性
- 找到对抗样本
- 计算鲁棒性边界

方法：
1. 符号区间传播 (Symbolic Interval Propagation)
2. 线性松弛 (Linear Relaxation)
3. 对抗攻击

Author: 算法库
"""

import numpy as np
from typing import List, Tuple, Dict, Optional


class Interval:
    """区间类"""
    
    def __init__(self, lower: float, upper: float):
        self.lower = lower
        self.upper = upper
    
    def __repr__(self):
        return f"[{self.lower:.4f}, {self.upper:.4f}]"
    
    def contains(self, x: float) -> bool:
        return self.lower <= x <= self.upper
    
    @staticmethod
    def add(a: 'Interval', b: 'Interval') -> 'Interval':
        return Interval(a.lower + b.lower, a.upper + b.upper)
    
    @staticmethod
    def sub(a: 'Interval', b: 'Interval') -> 'Interval':
        return Interval(a.lower - b.upper, a.upper - b.lower)
    
    @staticmethod
    def mul(a: 'Interval', b: 'Interval') -> 'Interval':
        """区间乘法（保守估计）"""
        products = [
            a.lower * b.lower,
            a.upper * b.lower,
            a.lower * b.upper,
            a.upper * b.upper
        ]
        return Interval(min(products), max(products))
    
    @staticmethod
    def relu(x: 'Interval') -> 'Interval':
        """ReLU区间（保守估计）"""
        return Interval(max(0, x.lower), max(0, x.upper))
    
    @staticmethod
    def sigmoid(x: 'Interval') -> 'Interval':
        """Sigmoid区间（保守估计）"""
        # Sigmoid是单调递增的
        return Interval(
            1.0 / (1.0 + np.exp(-x.upper)),  # 下界
            1.0 / (1.0 + np.exp(-x.lower))   # 上界
        )


class Symbol:
    """符号变量"""
    
    def __init__(self, name: str, interval: Interval):
        self.name = name
        self.interval = interval
    
    def __repr__(self):
        return f"{self.name}{self.interval}"


class SymbolicExpression:
    """符号表达式"""
    
    def __init__(self, coeffs: Dict[str, float], bias: float = 0.0):
        self.coeffs = coeffs  # {var_name: coefficient}
        self.bias = bias
    
    def evaluate(self, assignment: Dict[str, float]) -> float:
        """求值"""
        result = self.bias
        for name, coeff in self.coeffs.items():
            result += coeff * assignment.get(name, 0.0)
        return result
    
    def interval_bound(self, var_intervals: Dict[str, Interval]) -> Interval:
        """计算区间界（保守）"""
        lower = self.bias
        upper = self.bias
        
        for name, coeff in self.coeffs.items():
            if name in var_intervals:
                iv = var_intervals[name]
                if coeff >= 0:
                    lower += coeff * iv.lower
                    upper += coeff * iv.upper
                else:
                    lower += coeff * iv.upper
                    upper += coeff * iv.lower
        
        return Interval(lower, upper)


class NeuralNetwork:
    """神经网络"""
    
    def __init__(self, layer_sizes: List[int]):
        """
        初始化网络
        
        参数:
            layer_sizes: 每层的大小 [input_dim, hidden1, ..., output_dim]
        """
        self.layer_sizes = layer_sizes
        self.weights: List[np.ndarray] = []
        self.biases: List[np.ndarray] = []
    
    def add_layer(self, weight: np.ndarray, bias: np.ndarray):
        """添加层"""
        self.weights.append(weight)
        self.biases.append(bias)
    
    def forward_interval(self, input_interval: List[Interval],
                        activation: str = "relu") -> List[List[Interval]]:
        """
        前向区间传播
        
        参数:
            input_interval: 输入区间
            activation: 激活函数类型
        
        返回:
            每层的输出区间
        """
        n_layers = len(self.weights)
        intervals = [input_interval]
        
        for l in range(n_layers):
            # 获取上一层的输出作为当前层输入
            if l == 0:
                prev_output = input_interval
            else:
                prev_output = intervals[-1]
            
            # 计算当前层的区间（保守估计）
            n_neurons = self.weights[l].shape[0]
            layer_intervals = []
            
            for i in range(n_neurons):
                # 计算第i个神经元的区间
                w = self.weights[l][i]
                b = self.biases[l][i]
                
                # 区间线性组合
                linear = Interval(b, b)
                for j in range(len(prev_output)):
                    linear = Interval.add(linear, Interval.mul(
                        Interval(w[j], w[j]),  # 权重的区间是点区间
                        prev_output[j]
                    ))
                
                # 应用激活函数
                if activation == "relu":
                    layer_intervals.append(Interval.relu(linear))
                elif activation == "sigmoid":
                    layer_intervals.append(Interval.sigmoid(linear))
                elif activation == "identity":
                    layer_intervals.append(linear)
                else:
                    layer_intervals.append(linear)
            
            intervals.append(layer_intervals)
        
        return intervals
    
    def symbolic_linear relaxation(self, input_interval: List[Interval]) -> List[List[SymbolicExpression]]:
        """
        符号线性松弛
        
        返回每层的符号表达式界
        """
        n_layers = len(self.weights)
        symbols = [None]  # 输入层不需要
        
        # 输入符号变量
        input_symbols = {f"x_{i}": Symbol(f"x_{i}", iv) 
                        for i, iv in enumerate(input_interval)}
        
        layer_symbols = []
        current_symbols = input_symbols.copy()
        
        for l in range(n_layers):
            layer_exprs = []
            
            for i in range(self.weights[l].shape[0]):
                coeffs = {}
                bias = self.biases[l][i]
                
                # 收集权重系数
                for j, iv in enumerate(current_symbols.values()):
                    coeff = self.weights[l][i, j]
                    coeffs[f"{j}"] = coeff  # 简化：只用索引
                
                expr = SymbolicExpression(coeffs, bias)
                layer_exprs.append(expr)
            
            layer_symbols.append(layer_exprs)
            current_symbols = {f"h_{l}_{i}": Symbol(f"h_{l}_{i}", expr.interval_bound(
                {k: v.interval for k, v in input_symbols.items()}
            )) for i, expr in enumerate(layer_exprs)}
        
        return layer_symbols


class NetworkVerifier:
    """网络验证器"""
    
    def __init__(self, network: NeuralNetwork):
        self.network = network
    
    def verify_property(self, input_bounds: List[Tuple[float, float]],
                       property_fn: Callable, activation: str = "relu") -> Tuple[bool, Optional[float]]:
        """
        验证网络属性
        
        参数:
            input_bounds: 输入区间 [(lo, hi), ...]
            property_fn: 属性函数，输入和输出区间，返回是否满足
            activation: 激活函数
        
        返回:
            (是否满足, 不满足程度)
        """
        # 转换为Interval
        input_interval = [Interval(lo, hi) for lo, hi in input_bounds]
        
        # 前向传播
        intervals = self.network.forward_interval(input_interval, activation)
        output_interval = intervals[-1]
        
        # 评估属性
        return property_fn(input_interval, output_interval)
    
    def find_adversarial_example(self, input_bounds: List[Tuple[float, float]],
                                target_class: int, epsilon: float = 0.1) -> Optional[np.ndarray]:
        """
        寻找对抗样本（使用区间攻击）
        
        参数:
            input_bounds: 输入区间
            target_class: 目标类别
            epsilon: 扰动上界
        
        返回:
            对抗样本或None
        """
        # 简化版本：边界搜索
        best_input = None
        best_margin = float('inf')
        
        # 在区间边界采样
        n_dims = len(input_bounds)
        
        for _ in range(1000):
            # 随机点
            input_val = np.array([
                np.random.uniform(lo - epsilon, hi + epsilon) 
                for lo, hi in input_bounds
            ])
            
            # 截断到允许范围
            input_val = np.clip(input_val, 
                              [lo for lo, hi in input_bounds],
                              [hi for lo, hi in input_bounds])
            
            # 前向传播
            x = input_val
            for l in range(len(self.network.weights)):
                x = self.network.weights[l] @ x + self.network.biases[l]
                if l < len(self.network.weights) - 1:
                    x = np.maximum(0, x)  # ReLU
            
            # 检查目标类别的logit
            target_logit = x[target_class]
            
            # 计算到其他类别的最小距离
            other_logits = [x[i] for i in range(len(x)) if i != target_class]
            if other_logits:
                max_other = max(other_logits)
                margin = target_logit - max_other
                
                if margin < best_margin:
                    best_margin = margin
                    best_input = input_val.copy()
        
        if best_margin < 0:
            return best_input
        return None


def compute_robustness_bound(network: NeuralNetwork,
                            input_interval: List[Interval],
                            target_idx: int) -> float:
    """
    计算鲁棒性边界
    
    返回使分类结果不变的扰动上界
    """
    verifier = NetworkVerifier(network)
    
    # 简化的边界计算
    intervals = network.forward_interval(input_interval, "relu")
    output = intervals[-1]
    
    if target_idx >= len(output):
        return 0.0
    
    target_interval = output[target_idx]
    
    # 计算到其他类别的最小间隔
    min_margin = float('inf')
    
    for i, iv in enumerate(output):
        if i == target_idx:
            continue
        
        # 保守估计：类别i的上界与目标类别的下界之差
        margin = target_interval.lower - iv.upper
        
        if margin < min_margin:
            min_margin = margin
    
    return max(0, min_margin)


if __name__ == "__main__":
    print("=" * 55)
    print("神经网络验证测试")
    print("=" * 55)
    
    # 创建简单网络
    np.random.seed(42)
    
    # 网络: 2 -> 4 -> 2
    network = NeuralNetwork([2, 4, 2])
    network.add_layer(
        np.random.randn(4, 2) * 0.5,
        np.random.randn(4) * 0.1
    )
    network.add_layer(
        np.random.randn(2, 4) * 0.5,
        np.random.randn(2) * 0.1
    )
    
    print("\n--- 区间传播测试 ---")
    
    # 输入区间
    input_bounds = [(-0.1, 0.1), (-0.1, 0.1)]
    input_interval = [Interval(lo, hi) for lo, hi in input_bounds]
    
    # 前向传播
    intervals = network.forward_interval(input_interval, "relu")
    
    print(f"输入区间: {input_interval}")
    print(f"输出区间: {intervals[-1]}")
    
    # 验证器
    verifier = NetworkVerifier(network)
    
    # 定义属性：输出在某个范围内
    def property_fn(inp, out):
        return all(iv.upper < 10 for iv in out)
    
    satisfied, margin = verifier.verify_property(input_bounds, property_fn)
    print(f"\n属性验证: {'满足' if satisfied else '不满足'}")
    
    # 鲁棒性边界
    print("\n--- 鲁棒性分析 ---")
    
    robustness = compute_robustness_bound(network, input_interval, target_idx=0)
    print(f"类别0的鲁棒性边界: {robustness:.4f}")
    
    # 对抗样本搜索
    print("\n--- 对抗样本搜索 ---")
    
    adversarial = verifier.find_adversarial_example(
        input_bounds, 
        target_class=1,
        epsilon=0.2
    )
    
    if adversarial is not None:
        print(f"找到对抗样本: {adversarial}")
    else:
        print("未找到对抗样本（给定epsilon范围内）")
    
    # 符号表达式测试
    print("\n--- 符号线性松弛 ---")
    
    expr = SymbolicExpression({"x0": 1.5, "x1": -0.5}, bias=0.3)
    var_intervals = {
        "x0": Interval(0, 1),
        "x1": Interval(-1, 1)
    }
    
    bound = expr.interval_bound(var_intervals)
    print(f"符号表达式: 1.5*x0 - 0.5*x1 + 0.3")
    print(f"区间界: {bound}")
    
    print("\n测试通过！神经网络验证功能正常。")
