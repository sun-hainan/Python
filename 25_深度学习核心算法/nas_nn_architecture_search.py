# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / nas_nn_architecture_search

本文件实现 nas_nn_architecture_search 相关的算法功能。
"""

import numpy as np


# ============================
# 搜索空间定义
# ============================

class SearchSpace:
    """
    NAS搜索空间：定义可搜索的操作和节点连接
    
    参数:
        num_nodes: 中间节点数量
        num_operations: 每个节点可选的操作数
    """
    
    def __init__(self, num_nodes=4, num_operations=5):
        self.num_nodes = num_nodes
        self.num_operations = num_operations
        
        # 定义可搜索的操作
        self.operations = [
            'skip_connect',  # 跳跃连接
            'sep_conv_3x3',  # 分离卷积3x3
            'sep_conv_5x5',  # 分离卷积5x5
            'avg_pool_3x3',  # 平均池化
            'max_pool_3x3',  # 最大池化
        ]
    
    def sample_architecture(self):
        """
        随机采样一个架构
        返回:
            edges: 边选择矩阵 (num_nodes+2, num_nodes+2)
            ops: 边上的操作选择
        """
        num_total_nodes = self.num_nodes + 2  # 包含输入输出节点
        edges = np.zeros((num_total_nodes, num_total_nodes))
        ops = {}
        
        # 采样边：每个节点从前面的节点中选择
        for i in range(1, num_total_nodes):
            # 随机选择1-2条入边
            num_edges = np.random.choice([1, 2], p=[0.5, 0.5])
            prev_nodes = np.random.choice(range(i), size=num_edges, replace=False)
            
            for prev in prev_nodes:
                edges[prev, i] = 1
                ops[(prev, i)] = np.random.randint(0, self.num_operations)
        
        return edges, ops
    
    def mutate_architecture(self, edges, ops, mutation_rate=0.1):
        """
        架构变异：随机改变一些边或操作
        
        参数:
            edges: 当前边矩阵
            ops: 当前操作选择
            mutation_rate: 变异概率
        返回:
            new_edges, new_ops: 变异后的架构
        """
        new_edges = edges.copy()
        new_ops = ops.copy()
        
        # 变异边
        for i in range(edges.shape[0]):
            for j in range(i+1, edges.shape[1]):
                if np.random.random() < mutation_rate:
                    new_edges[i, j] = 1 - new_edges[i, j]
                    if new_edges[i, j] == 1:
                        new_ops[(i, j)] = np.random.randint(0, self.num_operations)
        
        return new_edges, new_ops


# ============================
# 随机搜索
# ============================

class RandomSearch:
    """
    随机搜索NAS
    
    参数:
        search_space: 搜索空间
        num_samples: 采样数量
    """
    
    def __init__(self, search_space, num_samples=100):
        self.search_space = search_space
        self.num_samples = num_samples
        self.history = []
    
    def search(self, evaluate_fn):
        """
        执行随机搜索
        
        参数:
            evaluate_fn: 架构评估函数，输入架构，输出性能分数
        返回:
            best_arch: 最佳架构
            best_score: 最佳分数
        """
        best_score = -np.inf
        best_arch = None
        
        for i in range(self.num_samples):
            edges, ops = self.search_space.sample_architecture()
            score = evaluate_fn(edges, ops)
            
            self.history.append({'edges': edges, 'ops': ops, 'score': score})
            
            if score > best_score:
                best_score = score
                best_arch = (edges, ops)
            
            if (i + 1) % 20 == 0:
                print(f"  RandomSearch [{i+1}/{self.num_samples}]: best={best_score:.4f}")
        
        return best_arch, best_score


# ============================
# 强化学习NAS（REINFORCE）
# ============================

class RLNASController:
    """
    基于强化学习的NAS控制器（使用REINFORCE算法）
    
    参数:
        search_space: 搜索空间
        hidden_dim: LSTM隐藏层维度
        lr: 学习率
    """
    
    def __init__(self, search_space, hidden_dim=64, lr=0.001):
        self.search_space = search_space
        self.hidden_dim = hidden_dim
        
        # 控制器LSTM参数（简化版）
        num_total_nodes = search_space.num_nodes + 2
        
        # 每个决策需要两个参数：选择哪个前驱节点 + 选择哪个操作
        self.W_h = np.random.randn(hidden_dim, hidden_dim) * 0.01
        self.W_x = np.random.randn(hidden_dim, hidden_dim) * 0.01
        self.W_pred = np.random.randn(2, hidden_dim) * 0.01
        self.b_h = np.zeros(hidden_dim)
        self.b_pred = np.zeros(2)
        
        # 优化器
        self.lr = lr
        self.baseline = 0.0
        self.entropy_coef = 0.01
    
    def forward(self, edges, ops):
        """
        控制器前向传播，计算架构的对数概率
        
        参数:
            edges: 边矩阵
            ops: 操作选择
        返回:
            log_prob: 架构的对数概率
            entropy: 策略的熵（用于探索）
        """
        h = np.zeros(self.hidden_dim)  # 初始隐藏状态
        
        log_prob = 0.0
        entropy = 0.0
        
        num_total_nodes = self.search_space.num_nodes + 2
        
        # 遍历所有边决策
        for i in range(1, num_total_nodes):
            for j in range(i+1, num_total_nodes):
                if edges[i, j] == 1:  # 这条边存在
                    # 简化的策略网络：基于隐藏状态决定操作
                    # 这里用ops中的值作为简化
                    op_index = ops.get((i, j), 0)
                    if op_index >= 0 and op_index < self.search_space.num_operations:
                        # 计算对数概率（简化）
                        log_prob += np.log(1.0 / self.search_space.num_operations + 1e-8)
                        entropy += np.log(self.search_space.num_operations)
        
        return log_prob, entropy
    
    def update(self, edges, ops, reward):
        """
        REINFORCE更新
        
        参数:
            edges: 架构边
            ops: 架构操作
            reward: 架构奖励
        """
        # 优势 = reward - baseline
        advantage = reward - self.baseline
        
        # 更新baseline（指数移动平均）
        self.baseline = 0.9 * self.baseline + 0.1 * reward
        
        # 这里简化了梯度更新，实际应使用策略梯度
        # 模拟更新
        grad_estimate = advantage * 0.001
        
        # 应用梯度（简化）
        self.W_h += self.lr * grad_estimate
        self.W_x += self.lr * grad_estimate
    
    def search(self, evaluate_fn, num_iterations=50):
        """
        执行强化学习NAS搜索
        
        参数:
            evaluate_fn: 评估函数
            num_iterations: 迭代次数
        返回:
            best_arch: 最佳架构
            best_reward: 最佳奖励
        """
        best_reward = -np.inf
        best_arch = None
        
        for iteration in range(num_iterations):
            # 采样架构
            edges, ops = self.search_space.sample_architecture()
            
            # 评估
            reward = evaluate_fn(edges, ops)
            
            # 更新控制器
            self.update(edges, ops, reward)
            
            if reward > best_reward:
                best_reward = reward
                best_arch = (edges, ops)
            
            if (iteration + 1) % 10 == 0:
                print(f"  RL-NAS [Iter {iteration+1}/{num_iterations}]: reward={reward:.4f}, best={best_reward:.4f}")
        
        return best_arch, best_reward


# ============================
# DARTS可微分架构搜索
# ============================

class DARTS:
    """
    DARTS (Differentiable Architecture Search)
    使用softmax将离散的架构选择松弛为可微分
    
    参数:
        num_nodes: 中间节点数
        num_operations: 每个节点候选操作数
    """
    
    def __init__(self, num_nodes=4, num_operations=5):
        self.num_nodes = num_nodes
        self.num_operations = num_operations
        num_total_nodes = num_nodes + 2
        
        # 边权重（可学习）：表示选择每条边的概率
        # 每个节点对(i,j)之间有权重
        self.edge_weights = {}
        for i in range(num_total_nodes):
            for j in range(i+1, num_total_nodes):
                # 初始化为均匀分布
                self.edge_weights[(i, j)] = np.zeros(num_operations) + 1.0 / num_operations
    
    def get_softmax_action(self, edge_weights):
        """将边权重通过softmax得到概率分布"""
        exp_weights = np.exp(edge_weights - np.max(edge_weights))
        return exp_weights / np.sum(exp_weights)
    
    def forward(self, x, features):
        """
        简化的DARTS前向传播
        
        参数:
            x: 输入特征
            features: 存储中间节点特征的字典
        返回:
            output: 输出
        """
        num_total_nodes = self.num_nodes + 2
        
        # 初始化节点特征
        features[0] = x  # 输入节点
        
        # 计算每个中间节点
        for node in range(1, num_total_nodes - 1):
            node_feature = np.zeros_like(x)
            
            # 聚合所有前驱节点的特征
            for prev in range(node):
                if (prev, node) in self.edge_weights:
                    probs = self.get_softmax_action(self.edge_weights[(prev, node)])
                    # 简化的特征聚合：加权平均
                    node_feature = node_feature + probs[0] * features[prev]
            
            features[node] = node_feature
        
        # 输出节点
        features[num_total_nodes - 1] = sum(
            features[i] for i in range(num_total_nodes - 1)
        ) / (num_total_nodes - 1)
        
        return features[num_total_nodes - 1]
    
    def get_architecture(self):
        """
        获取最终离散的架构
        每个边选择概率最大的操作
        """
        arch = {}
        for edge, weights in self.edge_weights.items():
            best_op = np.argmax(weights)
            arch[edge] = best_op
        return arch


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("神经网络架构搜索（NAS）测试")
    print("=" * 55)
    
    search_space = SearchSpace(num_nodes=4, num_operations=5)
    
    # 模拟评估函数（真实场景中需要训练网络）
    def mock_evaluate(edges, ops):
        """模拟架构评估：基于架构复杂度评分"""
        num_edges = np.sum(edges)
        complexity_penalty = 0.01 * num_edges
        # 模拟性能：介于0.5-0.9之间
        score = 0.7 + 0.2 * np.random.random() - complexity_penalty
        return score
    
    # 测试1：随机搜索
    print("\n--- 随机搜索 ---")
    random_search = RandomSearch(search_space, num_samples=50)
    best_arch, best_score = random_search.search(mock_evaluate)
    print(f"最佳分数: {best_score:.4f}")
    
    # 测试2：强化学习NAS
    print("\n--- 强化学习NAS ---")
    controller = RLNASController(search_space, hidden_dim=32, lr=0.001)
    best_arch_rl, best_reward = controller.search(mock_evaluate, num_iterations=30)
    print(f"最佳奖励: {best_reward:.4f}")
    
    # 测试3：DARTS
    print("\n--- DARTS ---")
    darts = DARTS(num_nodes=3, num_operations=5)
    
    # 模拟训练
    x = np.random.randn(8, 64)  # batch=8, dim=64
    features = {}
    
    for epoch in range(5):
        output = darts.forward(x, features)
        loss = -np.mean(output)  # 简化的损失
        # 模拟更新边权重
        for edge in darts.edge_weights:
            darts.edge_weights[edge] += np.random.randn(5) * 0.01
            darts.edge_weights[edge] = np.clip(darts.edge_weights[edge], -5, 5)
    
    final_arch = darts.get_architecture()
    print(f"学到的架构（部分边）:")
    for edge, op_idx in list(final_arch.items())[:3]:
        op_name = search_space.operations[op_idx]
        print(f"  Edge {edge}: {op_name}")
    
    # 测试4：架构变异
    print("\n--- 架构变异 ---")
    edges, ops = search_space.sample_architecture()
    mutated_edges, mutated_ops = search_space.mutate_architecture(edges, ops, mutation_rate=0.2)
    
    diff_edges = np.sum(edges != mutated_edges)
    diff_ops = sum(1 for k in ops if k in mutated_ops and ops[k] != mutated_ops[k])
    print(f"变异边数: {diff_edges}, 变异操作数: {diff_ops}")
    
    print("\nNAS测试完成！")
