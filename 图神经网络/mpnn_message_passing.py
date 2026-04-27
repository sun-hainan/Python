# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / mpnn_message_passing

本文件实现 mpnn_message_passing 相关的算法功能。
"""

import numpy as np


# ============================
# 消息函数
# ============================

def message_mlp(source_features, edge_features, target_features, W_m, b_m):
    """
    基于MLP的消息函数
    
    参数:
        source_features: 源节点特征 (num_edges, dim)
        edge_features: 边特征 (num_edges, edge_dim)
        target_features: 目标节点特征 (num_edges, dim)
        W_m: 消息权重
        b_m: 消息偏置
    返回:
        messages: 消息 (num_edges, dim)
    """
    # 拼接特征
    combined = np.concatenate([source_features, edge_features, target_features], axis=1)
    
    # MLP
    messages = np.maximum(0, combined @ W_m + b_m)
    
    return messages


def message_dot_product(source_features, edge_features, target_features, W_s, W_t):
    """
    点积注意力消息函数
    
    参数:
        source_features: 源节点特征
        target_features: 目标节点特征
        W_s, W_t: 变换权重
    返回:
        messages: 加权消息
        attention: 注意力权重
    """
    # 变换特征
    src_transformed = source_features @ W_s
    tgt_transformed = target_features @ W_t
    
    # 计算注意力
    attention = np.sum(src_transformed * tgt_transformed, axis=1, keepdims=True)
    attention = np.exp(np.clip(attention, -50, 50))
    
    # 加权消息
    messages = attention * src_transformed
    
    return messages, attention


def message_constant(source_features, edge_features, target_features):
    """
    常数消息（简化版本，不学习消息）
    """
    return source_features


# ============================
# 聚合函数
# ============================

def aggregate_sum(messages, receivers):
    """
    求和聚合
    
    参数:
        messages: 每条边的消息 (num_edges, dim)
        receivers: 每条消息对应的接收节点 (num_edges,)
    返回:
        aggregated: 每个节点的聚合消息 (num_nodes, dim)
    """
    num_nodes = int(np.max(receivers)) + 1
    dim = messages.shape[1]
    
    aggregated = np.zeros((num_nodes, dim))
    np.add.at(aggregated, receivers, messages)
    
    return aggregated


def aggregate_mean(messages, receivers, num_nodes):
    """均值聚合"""
    aggregated = aggregate_sum(messages, receivers)
    
    # 计算每个节点的邻居数
    neighbor_counts = np.bincount(receivers, minlength=num_nodes)
    neighbor_counts = np.maximum(neighbor_counts, 1)  # 避免除零
    
    return aggregated / neighbor_counts.reshape(-1, 1)


def aggregate_max(messages, receivers, num_nodes):
    """最大值聚合"""
    dim = messages.shape[1]
    aggregated = np.full((num_nodes, dim), -np.inf)
    
    # 使用at函数实现max聚合
    for i, receiver in enumerate(receivers):
        aggregated[receiver] = np.maximum(aggregated[receiver], messages[i])
    
    return aggregated


# ============================
# 状态更新函数
# ============================

def update_gru(current_state, incoming_messages, W_u, b_u, W_r, b_r, W_z, b_z):
    """
    GRU状态更新
    
    参数:
        current_state: 当前状态 (num_nodes, state_dim)
        incoming_messages: 聚合后的消息 (num_nodes, msg_dim)
        W_u, W_r, W_z, b_u, b_r, b_z: GRU参数
    """
    num_nodes = current_state.shape[0]
    state_dim = current_state.shape[1]
    
    # 重置门
    r = sigmoid(incoming_messages @ W_r + b_r)
    r_state = r * current_state
    
    # 候选状态
    h_tilde = np.tanh(r_state @ W_u + incoming_messages @ W_u[:state_dim] + b_u)
    
    # 更新门
    z = sigmoid(incoming_messages @ W_z + b_z)
    
    # 新状态
    new_state = (1 - z) * current_state + z * h_tilde
    
    return new_state


def update_simple(current_state, incoming_messages, W, b):
    """
    简单线性更新
    
    参数:
        current_state: 当前状态
        incoming_messages: 聚合消息
        W, b: 更新参数
    """
    return np.maximum(0, current_state + incoming_messages @ W + b)


# ============================
# MPNN框架
# ============================

class MPNNLayer:
    """
    MPNN层
    
    参数:
        node_dim: 节点特征维度
        edge_dim: 边特征维度
        message_dim: 消息维度
        state_dim: 状态维度
        message_type: 消息函数类型 ('mlp', 'dot', 'constant')
        aggregate_type: 聚合类型 ('sum', 'mean', 'max')
        update_type: 更新类型 ('gru', 'simple')
    """
    
    def __init__(self, node_dim, edge_dim, message_dim=32, state_dim=32,
                 message_type='mlp', aggregate_type='sum', update_type='simple'):
        self.node_dim = node_dim
        self.edge_dim = edge_dim
        self.message_dim = message_dim
        self.state_dim = state_dim
        self.message_type = message_type
        self.aggregate_type = aggregate_type
        self.update_type = update_type
        
        input_dim = node_dim * 2 + edge_dim
        
        # 消息函数参数
        if message_type == 'mlp':
            self.W_m = np.random.randn(input_dim, message_dim) * np.sqrt(2.0 / input_dim)
            self.b_m = np.zeros(message_dim)
        
        # 更新函数参数
        if update_type == 'gru':
            self.state_dim = state_dim
            self.W_u = np.random.randn(state_dim + message_dim, state_dim) * 0.01
            self.b_u = np.zeros(state_dim)
            self.W_r = np.random.randn(state_dim + message_dim, state_dim) * 0.01
            self.b_r = np.zeros(state_dim)
            self.W_z = np.random.randn(state_dim + message_dim, state_dim) * 0.01
            self.b_z = np.zeros(state_dim)
        elif update_type == 'simple':
            self.update_W = np.random.randn(message_dim, state_dim) * np.sqrt(2.0 / message_dim)
            self.update_b = np.zeros(state_dim)
    
    def forward(self, node_features, edge_index, edge_features=None, node_states=None):
        """
        MPNN前馈传播
        
        参数:
            node_features: 节点特征 (num_nodes, node_dim)
            edge_index: 边索引 (2, num_edges)，第一行为源节点，第二行为目标节点
            edge_features: 边特征 (num_edges, edge_dim)，可选
            node_states: 节点状态（用于多层MPNN），可选
        返回:
            new_states: 更新后的节点状态
            messages: 边消息（可选）
        """
        num_nodes = node_features.shape[0]
        num_edges = edge_index.shape[1]
        
        # 如果没有边特征，创建全1的默认特征
        if edge_features is None:
            edge_features = np.ones((num_edges, 1))
        
        # 如果没有初始状态，使用节点特征
        if node_states is None:
            node_states = node_features
        
        # 1. 消息传递：为每条边计算消息
        messages = []
        
        for i in range(num_edges):
            src = edge_index[0, i]
            dst = edge_index[1, i]
            
            src_feat = node_states[src]
            dst_feat = node_states[dst]
            edge_feat = edge_features[i] if i < len(edge_features) else np.array([0.0])
            
            if self.message_type == 'mlp':
                msg = message_mlp(
                    src_feat.reshape(1, -1),
                    edge_feat.reshape(1, -1),
                    dst_feat.reshape(1, -1),
                    self.W_m, self.b_m
                )
            elif self.message_type == 'dot':
                msg, _ = message_dot_product(
                    src_feat.reshape(1, -1),
                    edge_feat.reshape(1, -1),
                    dst_feat.reshape(1, -1),
                    np.eye(self.node_dim),
                    np.eye(self.node_dim)
                )
            else:
                msg = message_constant(
                    src_feat.reshape(1, -1),
                    edge_feat.reshape(1, -1),
                    dst_feat.reshape(1, -1)
                )
            
            messages.append(msg.flatten())
        
        messages = np.array(messages)
        
        # 2. 消息聚合：为每个节点聚合来自邻居的消息
        receivers = edge_index[1, :]  # 目标节点
        
        if self.aggregate_type == 'sum':
            aggregated = aggregate_sum(messages, receivers)
        elif self.aggregate_type == 'mean':
            aggregated = aggregate_mean(messages, receivers, num_nodes)
        elif self.aggregate_type == 'max':
            aggregated = aggregate_max(messages, receivers, num_nodes)
        else:
            aggregated = aggregate_sum(messages, receivers)
        
        # 3. 状态更新
        if self.update_type == 'gru':
            new_states = update_gru(
                node_states, aggregated,
                self.W_u, self.b_u, self.W_r, self.b_r, self.W_z, self.b_z
            )
        else:
            new_states = update_simple(node_states, aggregated, self.update_W, self.update_b)
        
        return new_states, messages


def sigmoid(x):
    """Sigmoid函数"""
    x = np.clip(x, -500, 500)
    return 1 / (1 + np.exp(-x))


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("消息传递神经网络（MPNN）测试")
    print("=" * 55)
    
    # 创建测试图
    num_nodes = 6
    num_edges = 10
    
    # 边索引
    edge_index = np.array([
        [0, 0, 1, 1, 2, 2, 3, 3, 4, 5],
        [1, 2, 0, 3, 0, 4, 1, 5, 2, 3]
    ])
    
    # 节点特征
    node_features = np.random.randn(num_nodes, 8)
    
    # 边特征
    edge_features = np.random.randn(num_edges, 2)
    
    print(f"节点数: {num_nodes}")
    print(f"边数: {num_edges}")
    
    # 测试1：MPNN层前馈
    print("\n--- MPNN层前馈测试 ---")
    mpnn = MPNNLayer(
        node_dim=8,
        edge_dim=2,
        message_dim=16,
        state_dim=16,
        message_type='mlp',
        aggregate_type='sum',
        update_type='simple'
    )
    
    new_states, messages = mpnn.forward(node_features, edge_index, edge_features)
    
    print(f"输入节点特征形状: {node_features.shape}")
    print(f"输出状态形状: {new_states.shape}")
    print(f"消息数量: {len(messages)}")
    print(f"消息形状: {messages[0].shape}")
    
    # 测试2：不同消息函数
    print("\n--- 不同消息函数对比 ---")
    for msg_type in ['mlp', 'dot', 'constant']:
        mpnn_msg = MPNNLayer(
            node_dim=8, edge_dim=2, message_dim=16, state_dim=16,
            message_type=msg_type
        )
        states, _ = mpnn_msg.forward(node_features, edge_index, edge_features)
        print(f"  {msg_type:10s}: 输出均值={states.mean():.4f}, 标准差={states.std():.4f}")
    
    # 测试3：不同聚合函数
    print("\n--- 不同聚合函数对比 ---")
    for agg_type in ['sum', 'mean', 'max']:
        mpnn_agg = MPNNLayer(
            node_dim=8, edge_dim=2, message_dim=16, state_dim=16,
            aggregate_type=agg_type
        )
        states, _ = mpnn_agg.forward(node_features, edge_index, edge_features)
        print(f"  {agg_type:6s}: 输出均值={states.mean():.4f}, 标准差={states.std():.4f}")
    
    # 测试4：多层MPNN
    print("\n--- 多层MPNN测试 ---")
    mpnn_layers = [
        MPNNLayer(node_dim=8, edge_dim=2, message_dim=16, state_dim=16),
        MPNNLayer(node_dim=16, edge_dim=2, message_dim=16, state_dim=16),
        MPNNLayer(node_dim=16, edge_dim=2, message_dim=8, state_dim=8),
    ]
    
    current_states = node_features
    for i, layer in enumerate(mpnn_layers):
        current_states, _ = layer.forward(current_states, edge_index, edge_features)
        print(f"  Layer {i+1}: 状态形状 {current_states.shape}")
    
    # 测试5：MPNN与GCN对比
    print("\n--- MPNN vs 简化GCN ---")
    # MPNN
    mpnn_simple = MPNNLayer(node_dim=8, edge_dim=0, message_dim=16, state_dim=8)
    states_mpnn, _ = mpnn_simple.forward(node_features, edge_index)
    
    # 简化GCN
    adj = np.zeros((num_nodes, num_nodes))
    for i in range(num_edges):
        adj[edge_index[0, i], edge_index[1, i]] = 1
    adj = adj + np.eye(num_nodes)
    d_inv = 1.0 / (np.sum(adj, axis=1) + 1e-8)
    adj_norm = adj * d_inv.reshape(-1, 1) * d_inv.reshape(1, -1)
    
    W_gcn = np.random.randn(8, 8) * 0.01
    states_gcn = adj_norm @ node_features @ W_gcn
    states_gcn = np.maximum(0, states_gcn)
    
    print(f"MPNN输出均值: {states_mpnn.mean():.4f}")
    print(f"GCN输出均值: {states_gcn.mean():.4f}")
    print(f"输出相关性: {np.corrcoef(states_mpnn.flatten(), states_gcn.flatten())[0,1]:.4f}")
    
    # 测试6：消息分析
    print("\n--- 边消息分析 ---")
    mpnn_debug = MPNNLayer(node_dim=8, edge_dim=2, message_dim=8, state_dim=8)
    _, messages = mpnn_debug.forward(node_features, edge_index, edge_features)
    
    print(f"消息形状: {messages.shape}")
    print(f"消息均值范围: [{messages.min():.4f}, {messages.max():.4f}]")
    
    # 节点0的消息
    node_0_outgoing = np.where(edge_index[0] == 0)[0]
    print(f"节点0发出的消息数: {len(node_0_outgoing)}")
    print(f"节点0发出的消息均值: {messages[node_0_outgoing].mean(axis=0).round(3)}")
    
    print("\nMPNN测试完成！")
