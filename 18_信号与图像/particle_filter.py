# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / particle_filter

本文件实现 particle_filter 相关的算法功能。
"""

import numpy as np


class Particle:
    """粒子"""

    def __init__(self, state, weight=1.0):
        self.state = np.array(state, dtype=float)
        self.weight = weight
        self.weight_normalized = 0.0


class ParticleFilter:
    """
    粒子滤波器

    实现 SIR (Sampling Importance Resampling) 滤波器。
    """

    def __init__(self, state_dim, n_particles=100,
                 dynamics_fn=None, obs_fn=None,
                 prior_fn=None):
        """
        初始化粒子滤波器

        参数:
            state_dim: 状态维度
            n_particles: 粒子数量
            dynamics_fn: 动力学函数 f(x, u) -> x'
            obs_fn: 观测似然函数 L(z|x)
            prior_fn: 先验采样函数
        """
        self.state_dim = state_dim
        self.n_particles = n_particles
        self.dynamics_fn = dynamics_fn
        self.obs_fn = obs_fn
        self.prior_fn = prior_fn

        self.particles = []
        self.weights = np.zeros(n_particles)
        self.estimate = np.zeros(state_dim)

    def initialize(self, prior_fn=None):
        """
        初始化粒子

        参数:
            prior_fn: 先验采样函数
        """
        if prior_fn is None and self.prior_fn is not None:
            prior_fn = self.prior_fn

        self.particles = []
        for _ in range(self.n_particles):
            if prior_fn:
                state = prior_fn()
            else:
                state = np.zeros(self.state_dim)
            self.particles.append(Particle(state))

        self.weights[:] = 1.0 / self.n_particles

    def predict(self, u=None):
        """
        预测步骤：使用动力学模型传播粒子

        参数:
            u: 控制输入
        """
        for p in self.particles:
            if self.dynamics_fn:
                p.state = self.dynamics_fn(p.state, u)
            else:
                # 无模型：添加随机游走
                p.state += np.random.randn(self.state_dim) * 0.1

    def update(self, z, R=None):
        """
        更新步骤：根据观测更新权重

        参数:
            z: 观测值
            R: 观测噪声协方差
        """
        for i, p in enumerate(self.particles):
            if self.obs_fn:
                # 计算似然
                likelihood = self.obs_fn(z, p.state)
                p.weight *= likelihood
            else:
                # 简化：假设高斯观测噪声
                if R is not None:
                    diff = z - p.state[:len(z)]
                    likelihood = np.exp(-0.5 * diff @ np.linalg.inv(R) @ diff)
                    p.weight *= likelihood

        # 归一化权重
        total = sum(p.weight for p in self.particles)
        if total > 0:
            for p in self.particles:
                p.weight /= total
        else:
            for p in self.particles:
                p.weight = 1.0 / self.n_particles

    def resample(self):
        """
        重采样：使用系统采样（Systematic Resampling）

        去除低权重粒子，复制高权重粒子。
        """
        weights = np.array([p.weight for p in self.particles])

        # 系统采样
        cumsum = np.cumsum(weights)
        u0 = np.random.uniform(0, 1.0 / self.n_particles)

        new_particles = []
        for i in range(self.n_particles):
            u = u0 + (i - 1) / self.n_particles
            idx = np.searchsorted(cumsum, u)
            new_particles.append(Particle(self.particles[idx].state.copy()))

        self.particles = new_particles
        for p in self.particles:
            p.weight = 1.0 / self.n_particles

    def estimate_state(self):
        """
        估计状态（加权平均）

        返回:
            x_hat: 估计状态
        """
        weights = np.array([p.weight for p in self.particles])
        states = np.array([p.state for p in self.particles])
        self.estimate = np.average(states, weights=weights, axis=0)
        return self.estimate

    def get_ess(self):
        """
        计算有效样本数（ESS）

        返回:
            ess: 有效样本数
        """
        weights = np.array([p.weight for p in self.particles])
        return 1.0 / np.sum(weights ** 2)

    def step(self, z, u=None, R=None, resample_threshold=0.5):
        """
        一步完整滤波

        参数:
            z: 观测
            u: 控制输入
            R: 观测噪声
            resample_threshold: 重采样阈值（相对于 n_particles）
        """
        self.predict(u)
        self.update(z, R)
        ess = self.get_ess()

        if ess < resample_threshold * self.n_particles:
            self.resample()

        return self.estimate_state()


def systematic_resample(weights):
    """
    系统重采样

    参数:
        weights: 粒子权重
    返回:
        indices: 新粒子索引
    """
    n = len(weights)
    cumsum = np.cumsum(weights)
    u0 = np.random.uniform(0, 1.0 / n)

    indices = []
    u = u0
    for i in range(n):
        u += 1.0 / n
        idx = np.searchsorted(cumsum, u)
        indices.append(min(idx, n - 1))

    return indices


def multinomial_resample(weights):
    """多项式重采样"""
    n = len(weights)
    cumsum = np.cumsum(weights)
    u = np.random.uniform(0, 1)
    indices = []
    for _ in range(n):
        idx = np.searchsorted(cumsum, u)
        indices.append(idx)
        u += 1.0 / n
    return indices


class SIRParticleFilter(ParticleFilter):
    """
    SIR 粒子滤波器（完整实现）
    """

    def __init__(self, state_dim, n_particles, transition_fn, observation_fn):
        super().__init__(state_dim, n_particles)
        self.transition_fn = transition_fn
        self.observation_fn = observation_fn

    def predict(self, u=None):
        """预测：采样新的粒子"""
        for p in self.particles:
            p.state = self.transition_fn(p.state, u) + \
                     np.random.randn(self.state_dim) * 0.1

    def update(self, z):
        """更新：计算重要性权重"""
        for p in self.particles:
            likelihood = self.observation_fn(z, p.state)
            p.weight *= likelihood

        # 归一化
        total = sum(p.weight for p in self.particles)
        for p in self.particles:
            p.weight /= total


def robot_localization_demo():
    """机器人定位演示"""
    print("=== 粒子滤波器定位演示 ===")

    np.random.seed(42)

    # 状态: [x, y, theta]
    state_dim = 3
    n_particles = 100

    def transition(state, u=None):
        """运动模型"""
        if u is None:
            u = np.array([0.1, 0.05])
        v, w = u
        theta = state[2]
        return np.array([
            state[0] + v * np.cos(theta),
            state[1] + v * np.sin(theta),
            state[2] + w
        ])

    def observe(state):
        """观测模型（返回似然）"""
        return 1.0

    pf = SIRParticleFilter(state_dim, n_particles, transition, observe)

    # 初始化粒子（撒在地图范围内）
    for i, p in enumerate(pf.particles):
        p.state = np.array([np.random.uniform(-5, 5),
                           np.random.uniform(-5, 5),
                           np.random.uniform(-np.pi, np.pi)])

    # 模拟轨迹
    true_state = np.array([0, 0, 0])
    observations = []

    print(f"初始粒子数: {n_particles}")
    print(f"初始估计: {pf.estimate_state().round(2)}")

    for step in range(10):
        # 真实移动
        u = np.array([0.5, 0.1])
        true_state = transition(true_state, u) + np.random.randn(3) * 0.05

        # 观测（带噪声）
        obs = true_state[:2] + np.random.randn(2) * 0.3

        # 滤波
        pf.predict(u)
        pf.update(obs)
        ess_before = pf.get_ess()
        pf.resample()
        estimate = pf.estimate_state()
        ess_after = pf.get_ess()

        print(f"Step {step+1}: 估计 ({estimate[0]:.2f}, {estimate[1]:.2f}) "
              f"真实 ({true_state[0]:.2f}, {true_state[1]:.2f}) "
              f"ESS: {ess_before:.1f} -> {ess_after:.1f}")

    print(f"\n最终估计: {pf.estimate_state().round(2)}")
    print(f"最终 ESS: {pf.get_ess():.1f}")


if __name__ == "__main__":
    robot_localization_demo()

    print("\n=== 跟踪演示 ===")

    # 1D 跟踪
    np.random.seed(123)

    pf = ParticleFilter(state_dim=1, n_particles=200)

    # 先验
    def prior():
        return np.array([np.random.uniform(-10, 10)])
    pf.initialize(prior)

    true_x = 0.0
    estimates = []

    for t in range(50):
        # 真实动态
        true_x = true_x + 0.5 + np.random.randn() * 0.2

        # 观测
        z = true_x + np.random.randn() * 0.5

        # 滤波
        pf.predict()
        pf.update(np.array([z]), R=np.array([[0.5]]))
        pf.resample()
        est = pf.estimate_state()[0]
        estimates.append(est)

    import matplotlib
    matplotlib.use('Agg')

    print(f"跟踪完成，最后估计: {estimates[-1]:.2f}")
    print(f"真实位置: {true_x:.2f}")
    print(f"跟踪误差: {abs(estimates[-1] - true_x):.2f}")

    print("\n粒子滤波器测试完成!")
