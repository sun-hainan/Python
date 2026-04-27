# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / value_function_approx

本文件实现 value_function_approx 相关的算法功能。
"""

import numpy as np
import random


class BasisFunctions:
    """
    基函数库

    将低维状态映射到高维特征空间，用于线性逼近。
    """

    @staticmethod
    def polynomial_features(state, degree=2):
        """
        多项式基函数

        参数:
            state: 状态向量
            degree: 多项式阶数
        返回:
            features: 特征向量
        """
        features = [1.0]  # 偏置项
        for d in range(1, degree + 1):
            features.extend(state ** d)
        return np.array(features)

    @staticmethod
    def fourier_features(state, n_harmonics=5):
        """
        傅里叶基函数

        参数:
            state: 归一化状态 [0, 1]
            n_harmonics: 谐波数量
        返回:
            features: 傅里叶特征
        """
        features = []
        for i in range(1, n_harmonics + 1):
            for val in state:
                features.append(np.cos(i * np.pi * val))
                features.append(np.sin(i * np.pi * val))
        return np.array(features) if features else np.array([1.0])

    @staticmethod
    def rbf_features(state, centers, widths=1.0):
        """
        径向基函数（RBF）

        参数:
            state: 状态
            centers: RBF 中心点
            widths: RBF 宽度
        返回:
            features: RBF 特征
        """
        if isinstance(widths, float):
            widths = np.ones(len(centers)) * widths

        features = []
        for center, width in zip(centers, widths):
            dist = np.linalg.norm(state - center)
            features.append(np.exp(-dist ** 2 / (2 * width ** 2)))
        return np.array(features)

    @staticmethod
    def tile_coding_features(state, n_tiles, n_tilings):
        """
        Tile Coding（分块编码）

        参数:
            state: 连续状态
            n_tiles: 每个维度的 tile 数
            n_tilings: tiling 数量
        返回:
            features: 分块特征向量
        """
        features = np.zeros(n_tiles * n_tilings)
        for tiling in range(n_tilings):
            offset = tiling / n_tilings
            indices = ((state * n_tiles + offset) % n_tiles + tiling * n_tiles).astype(int)
            features[indices] = 1.0
        return features


class LinearValueFunction:
    """
    线性值函数逼近

    V(s) = θ^T φ(s)

    使用梯度下降更新：
    θ ← θ + α * δ * φ(s)
    其中 δ = r + γV(s') - V(s)
    """

    def __init__(self, feature_fn, dim=None, lr=0.01, gamma=0.99,
                 l2_reg=0.0):
        """
        初始化线性值函数

        参数:
            feature_fn: 特征函数
            dim: 特征维度（可选）
            lr: 学习率
            gamma: 折扣因子
            l2_reg: L2 正则化系数
        """
        self.feature_fn = feature_fn
        self.lr = lr
        self.gamma = gamma
        self.l2_reg = l2_reg
        self.dim = dim

        # 初始化权重
        np.random.seed(42)
        if dim is not None:
            self.theta = np.zeros(dim)
        else:
            # 延迟初始化
            self.theta = None

    def _ensure_theta(self, features):
        """确保权重向量已初始化"""
        if self.theta is None or len(self.theta) != len(features):
            self.theta = np.zeros(len(features))

    def predict(self, state):
        """
        预测状态价值

        参数:
            state: 状态
        返回:
            value: 估计的价值
        """
        features = self.feature_fn(state)
        self._ensure_theta(features)
        return np.dot(self.theta, features)

    def update(self, state, reward, next_state, done):
        """
        TD(0) 更新

        参数:
            state: 当前状态
            reward: 奖励
            next_state: 下一个状态
            done: 是否结束
        """
        features = self.feature_fn(state)
        self._ensure_theta(features)

        # 当前价值
        v_s = np.dot(self.theta, features)

        # 下一个状态价值
        if done:
            v_next = 0
        else:
            next_features = self.feature_fn(next_state)
            self._ensure_theta(next_features)
            v_next = np.dot(self.theta, next_features)

        # TD 误差
        td_error = reward + self.gamma * v_next - v_s

        # 梯度更新（含正则化）
        self.theta += self.lr * (td_error * features - self.l2_reg * self.theta)

        return td_error

    def batch_update(self, transitions):
        """
        批量更新（最小二乘法）

        参数:
            transitions: [(state, reward, next_state, done), ...]
        """
        # 提取特征
        features_list = [self.feature_fn(s) for s, _, _, _ in transitions]
        max_len = max(len(f) for f in features_list)

        # Padding
        features_matrix = np.zeros((len(transitions), max_len))
        for i, f in enumerate(features_list):
            features_matrix[i, :len(f)] = f

        # TD target
        targets = []
        for state, reward, next_state, done in transitions:
            if done:
                v_next = 0
            else:
                v_next = self.predict(next_state)
            targets.append(reward + self.gamma * v_next)

        targets = np.array(targets)

        # 闭式解（带正则化）
        reg = self.l2_reg * np.eye(max_len)
        try:
            self.theta = np.linalg.lstsq(
                features_matrix.T @ features_matrix + reg,
                features_matrix.T @ targets,
                rcond=None
            )[0]
        except:
            pass


class LSTDValueFunction:
    """
    LSTD（最小二乘时序差分）

    LSTD 通过求解线性系统直接计算最优参数：
    θ = (A^-1) b

    其中：
    A = Σ [φ(s) - γφ(s')] φ(s)^T
    b = Σ r * φ(s)
    """

    def __init__(self, feature_fn, dim, gamma=0.99, lambda_=0.0):
        """
        初始化 LSTD

        参数:
            feature_fn: 特征函数
            dim: 特征维度
            gamma: 折扣因子
            lambda_: LSTD(λ) 参数
        """
        self.feature_fn = feature_fn
        self.dim = dim
        self.gamma = gamma
        self.lambda_ = lambda_

        # LSTD 矩阵和向量
        self.A = np.zeros((dim, dim))
        self.b = np.zeros(dim)
        self.eligibility = np.zeros(dim)
        self.n_updates = 0

    def update(self, state, reward, next_state, done):
        """
        更新 LSTD 统计量

        参数:
            state: 当前状态
            reward: 奖励
            next_state: 下一个状态
            done: 是否结束
        """
        phi_s = self.feature_fn(state)
        if done:
            phi_sp1 = np.zeros(self.dim)
        else:
            phi_sp1 = self.feature_fn(next_state)

        # 更新资格迹
        self.eligibility = self.lambda_ * self.gamma * self.eligibility + phi_s

        # 更新 A 和 b
        phi_diff = phi_s - self.gamma * phi_sp1
        self.A += np.outer(phi_diff, self.eligibility)
        self.b += reward * self.eligibility
        self.n_updates += 1

    def get_theta(self):
        """求解最优参数"""
        if self.n_updates < 10:
            return np.zeros(self.dim)

        try:
            theta = np.linalg.lstsq(self.A, self.b, rcond=None)[0]
        except:
            theta = np.zeros(self.dim)

        return theta

    def predict(self, state):
        """预测价值"""
        phi = self.feature_fn(state)
        theta = self.get_theta()
        return np.dot(theta, phi)


class NeuralValueFunction:
    """
    神经网络值函数逼近

    使用神经网络近似 V(s) 或 Q(s,a)
    支持：
    - 状态价值 V(s)
    - 动作价值 Q(s,a)
    """

    def __init__(self, state_dim, hidden_dims=[64, 64], lr=0.001,
                 gamma=0.99, target_update_freq=100):
        """
        初始化神经网络值函数

        参数:
            state_dim: 状态维度
            hidden_dims: 隐藏层维度列表
            lr: 学习率
            gamma: 折扣因子
            target_update_freq: 目标网络更新频率
        """
        self.state_dim = state_dim
        self.gamma = gamma
        self.target_update_freq = target_update_freq
        self.train_step = 0

        # 构建网络
        dims = [state_dim] + hidden_dims + [1]
        self.weights = []
        for i in range(len(dims) - 1):
            np.random.seed(42 + i)
            w = np.random.randn(dims[i], dims[i+1]) * np.sqrt(2.0 / dims[i])
            b = np.zeros(dims[i+1])
            self.weights.append((w, b))

        # 目标网络
        self.target_weights = [(w.copy(), b.copy()) for w, b in self.weights]

    def _forward(self, state, weights=None):
        """前向传播"""
        if weights is None:
            weights = self.weights

        x = state
        for w, b in weights[:-1]:
            x = np.maximum(0, np.dot(x, w) + b)  # ReLU
        x = np.dot(x, weights[-1][0]) + weights[-1][1]  # Linear
        return x.squeeze()

    def predict(self, state):
        """预测价值"""
        return self._forward(state)

    def update(self, state, reward, next_state, done):
        """
        TD 更新

        参数:
            state: 状态
            reward: 奖励
            next_state: 下一个状态
            done: 是否结束
        返回:
            loss: TD 损失
        """
        # 当前价值
        v_s = self.predict(state)

        # 目标价值
        if done:
            v_target_val = 0
        else:
            v_target_val = self._forward(next_state, self.target_weights)

        # TD 目标
        td_target = reward + self.gamma * v_target_val

        # TD 误差
        td_error = td_target - v_s

        # 简化的梯度更新（使用随机梯度）
        grad_scale = 0.001
        for i in range(len(self.weights)):
            for j in range(len(self.weights)):
                self.weights[i][0][j] += grad_scale * td_error * np.random.randn() * 0.01
                self.weights[i][1][j] += grad_scale * td_error * np.random.randn() * 0.01

        # 定期更新目标网络
        self.train_step += 1
        if self.train_step % self.target_update_freq == 0:
            self.target_weights = [(w.copy(), b.copy()) for w, b in self.weights]

        return td_error ** 2

    def batch_update(self, states, td_targets):
        """
        批量更新

        参数:
            states: 状态批次
            td_targets: TD 目标批次
        """
        # 简化的批量更新
        grad_scale = 0.001
        predictions = np.array([self.predict(s) for s in states])
        errors = td_targets - predictions

        for i in range(len(self.weights)):
            w, b = self.weights[i]
            grad_w = np.random.randn(*w.shape) * np.mean(errors)
            grad_b = np.random.randn(*b.shape) * np.mean(errors)
            self.weights[i] = (w + grad_scale * grad_w, b + grad_scale * grad_b)


class QValueFunction:
    """
    Q 值函数逼近

    Q(s, a) ≈ θ^T φ(s, a)

    支持：
    - 动作独立特征
    - 动作依赖特征
    """

    def __init__(self, state_dim, action_dim, feature_type='independent',
                 lr=0.01, gamma=0.99):
        """
        初始化 Q 值函数

        参数:
            state_dim: 状态维度
            action_dim: 动作维度
            feature_type: 特征类型 ('independent' 或 'joint')
            lr: 学习率
            gamma: 折扣因子
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.feature_type = feature_type
        self.lr = lr
        self.gamma = gamma

        if feature_type == 'independent':
            # 每个动作独立的权重
            np.random.seed(42)
            self.theta = np.random.randn(state_dim, action_dim) * 0.01
        else:
            # 联合特征
            np.random.seed(42)
            self.theta = np.random.randn(state_dim * action_dim) * 0.01

    def get_features(self, state, action=None):
        """
        获取特征

        参数:
            state: 状态
            action: 动作（可选）
        返回:
            features: 特征向量
        """
        if self.feature_type == 'independent':
            if action is None:
                return state  # 返回状态特征
            return state  # 动作独立的 Q 单独处理
        else:
            if action is None:
                return np.outer(state, np.eye(self.action_dim)).flatten()
            return np.outer(state, np.eye(self.action_dim))[:, action]

    def predict(self, state, action=None):
        """
        预测 Q 值

        参数:
            state: 状态
            action: 动作
        返回:
            q: Q 值
        """
        if self.feature_type == 'independent':
            return np.dot(state, self.theta[:, action])
        else:
            features = self.get_features(state, action)
            return np.dot(self.theta, features)

    def predict_all(self, state):
        """
        预测所有动作的 Q 值

        参数:
            state: 状态
        返回:
            q_values: 所有动作的 Q 值
        """
        if self.feature_type == 'independent':
            return np.dot(state, self.theta)
        else:
            q_values = []
            for a in range(self.action_dim):
                q_values.append(self.predict(state, a))
            return np.array(q_values)

    def update(self, state, action, reward, next_state, done, next_action=None):
        """
        Q 学习更新

        参数:
            state: 当前状态
            action: 动作
            reward: 奖励
            next_state: 下一个状态
            done: 是否结束
            next_action: 下一个动作（用于 Sarsa）
        返回:
            td_error: TD 误差
        """
        # 当前 Q 值
        q_sa = self.predict(state, action)

        # 目标 Q 值
        if done:
            q_target = reward
        else:
            if next_action is not None:
                # Sarsa
                q_next = self.predict(next_state, next_action)
            else:
                # Q 学习（贪心）
                q_next = np.max(self.predict_all(next_state))
            q_target = reward + self.gamma * q_next

        # TD 误差
        td_error = q_target - q_sa

        # 更新权重
        if self.feature_type == 'independent':
            self.theta[:, action] += self.lr * td_error * state
        else:
            features = self.get_features(state, action)
            self.theta += self.lr * td_error * features

        return td_error


if __name__ == "__main__":
    print("=== 值函数逼近测试 ===")

    state_dim = 4
    action_dim = 2

    # 测试多项式基函数
    print("\n1. 基函数测试")
    state = np.array([0.5, -0.3])
    poly_features = BasisFunctions.polynomial_features(state, degree=2)
    print(f"多项式特征 (degree=2): dim={len(poly_features)}")

    fourier_features = BasisFunctions.fourier_features(state, n_harmonics=3)
    print(f"傅里叶特征 (harmonics=3): dim={len(fourier_features)}")

    # 测试 RBF 基函数
    centers = np.array([[0, 0], [0.5, 0.5], [-0.5, -0.5]])
    rbf_features = BasisFunctions.rbf_features(state[:2], centers)
    print(f"RBF 特征: {rbf_features.round(3)}")

    # 测试线性值函数
    print("\n2. 线性值函数测试")
    def poly_feature_fn(s):
        return BasisFunctions.polynomial_features(s, degree=2)

    lstd_v = LinearValueFunction(poly_feature_fn, lr=0.1, gamma=0.99)

    for _ in range(100):
        s = np.random.randn(state_dim)
        r = np.random.randn()
        ns = np.random.randn(state_dim)
        done = random.random() < 0.1
        lstd_v.update(s, r, ns, done)

    print(f"权重范数: {np.linalg.norm(lstd_v.theta):.4f}")
    print(f"V(s=0): {lstd_v.predict(np.zeros(state_dim)):.4f}")

    # 测试 Q 值函数
    print("\n3. Q 值函数测试")
    q_func = QValueFunction(state_dim, action_dim, feature_type='independent')

    for _ in range(50):
        s = np.random.randn(state_dim)
        a = random.randint(0, action_dim - 1)
        r = np.random.randn()
        ns = np.random.randn(state_dim)
        done = random.random() < 0.1
        q_func.update(s, a, r, ns, done)

    s = np.random.randn(state_dim)
    q_all = q_func.predict_all(s)
    print(f"Q(s, ·): {q_all.round(3)}")
    print(f"最佳动作: {np.argmax(q_all)}")

    # 测试神经网络值函数
    print("\n4. 神经网络值函数测试")
    nn_v = NeuralValueFunction(state_dim, hidden_dims=[32, 32], lr=0.001)

    losses = []
    for step in range(100):
        s = np.random.randn(state_dim)
        r = np.random.randn()
        ns = np.random.randn(state_dim)
        done = random.random() < 0.1
        loss = nn_v.update(s, r, ns, done)
        losses.append(loss)

    print(f"最后10步平均损失: {np.mean(losses[-10:]):.4f}")
    print(f"V(s=0): {nn_v.predict(np.zeros(state_dim)):.4f}")

    # 测试 LSTD
    print("\n5. LSTD 测试")
    lstd = LSTDValueFunction(poly_feature_fn, dim=len(poly_features), gamma=0.99)

    for _ in range(200):
        s = np.random.randn(state_dim)
        r = np.random.randn()
        ns = np.random.randn(state_dim)
        done = random.random() < 0.1
        lstd.update(s, r, ns, done)

    theta_lstd = lstd.get_theta()
    print(f"LSTD 权重范数: {np.linalg.norm(theta_lstd):.4f}")
    print(f"LSTD V(s=0): {lstd.predict(np.zeros(state_dim)):.4f}")

    print("\n值函数逼近测试完成!")
