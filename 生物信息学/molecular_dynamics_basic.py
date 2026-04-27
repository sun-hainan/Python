# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / molecular_dynamics_basic



本文件实现 molecular_dynamics_basic 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple

import math





def lennard_jones_potential(r: float, epsilon: float = 1.0, sigma: float = 1.0) -> float:

    """

    Lennard-Jones势能



    U(r) = 4ε[(σ/r)^12 - (σ/r)^6]



    参数:

        r: 原子间距

        epsilon: 势阱深度

        sigma: 平衡距离



    返回:

        势能

    """

    if r < 0.01:

        return 1e10

    sr = sigma / r

    return 4 * epsilon * (sr**12 - sr**6)





def lennard_jones_force(r_vec: np.ndarray, epsilon: float = 1.0, sigma: float = 1.0) -> np.ndarray:

    """

    Lennard-Jones力



    F = -dU/dr = 24ε/r * [2(σ/r)^12 - (σ/r)^6]



    参数:

        r_vec: 原子间距离向量



    返回:

        力向量

    """

    r = np.linalg.norm(r_vec)

    if r < 0.01:

        return np.zeros(3)



    sr = sigma / r

    force_mag = 24 * epsilon / r * (2 * sr**12 - sr**6)

    force_vec = force_mag * (r_vec / r)

    return force_vec





def bond_energy(r: float, r_eq: float, k: float) -> float:

    """

    键伸缩能（简谐势）



    U = (1/2)k(r - r_eq)^2



    参数:

        r: 当前键长

        r_eq: 平衡键长

        k: 力常数



    返回:

        能量

    """

    return 0.5 * k * (r - r_eq)**2





def angle_energy(theta: float, theta_eq: float, k: float) -> float:

    """

    角度弯曲能



    U = (1/2)k(θ - θ_eq)^2

    """

    return 0.5 * k * (theta - theta_eq)**2





def verlet_integration(

    positions: np.ndarray,

    velocities: np.ndarray,

    forces: np.ndarray,

    masses: np.ndarray,

    dt: float

) -> Tuple[np.ndarray, np.ndarray]:

    """

    Velocity Verlet积分算法



    参数:

        positions: 位置 (n_atoms, 3)

        velocities: 速度 (n_atoms, 3)

        forces: 力 (n_atoms, 3)

        masses: 质量 (n_atoms,)

        dt: 时间步长



    返回:

        (new_positions, new_velocities)

    """

    # 更新位置

    new_positions = positions + velocities * dt + 0.5 * forces / masses[:, None] * dt**2



    # 估算速度（需要新力，这里简化处理）

    new_velocities = velocities + 0.5 * forces / masses[:, None] * dt



    return new_positions, new_velocities





def compute_forces(

    positions: np.ndarray,

    epsilon: float = 1.0,

    sigma: float = 1.0

) -> np.ndarray:

    """

    计算所有原子间的Lennard-Jones力



    参数:

        positions: 原子坐标

        epsilon, sigma: LJ参数



    返回:

        力矩阵 (n_atoms, n_atoms, 3)

    """

    n = len(positions)

    forces = np.zeros((n, n, 3))



    for i in range(n):

        for j in range(i + 1, n):

            r_vec = positions[j] - positions[i]

            f = lennard_jones_force(r_vec, epsilon, sigma)

            forces[i, j] = f

            forces[j, i] = -f



    return forces





def energy_minimization_steepest_descent(

    positions: np.ndarray,

    epsilon: float = 1.0,

    sigma: float = 1.0,

    n_steps: int = 100,

    step_size: float = 0.1

) -> np.ndarray:

    """

    最速下降法能量最小化



    参数:

        positions: 初始坐标

        epsilon, sigma: LJ参数

        n_steps: 最大步数

        step_size: 步长



    返回:

        最小化后的坐标

    """

    coords = positions.copy()



    for step in range(n_steps):

        # 计算力

        total_force = np.zeros_like(coords)

        for i in range(len(coords)):

            for j in range(len(coords)):

                if i != j:

                    r_vec = coords[j] - coords[i]

                    r = np.linalg.norm(r_vec)

                    if r < 0.01:

                        continue

                    sr = sigma / r

                    f_mag = 24 * epsilon / r * (2 * sr**12 - sr**6)

                    total_force[i] += f_mag * (r_vec / r)



        # 更新坐标

        coords = coords - step_size * total_force



        if np.linalg.norm(total_force) < 0.01:

            print(f'  收敛于步 {step}')

            break



    return coords





def compute_temperature(velocities: np.ndarray, masses: np.ndarray) -> float:

    """

    计算系统温度



    (3/2)NkT = (1/2)Σm_i*v_i^2



    参数:

        velocities: 速度

        masses: 质量



    返回:

        温度

    """

    n_atoms = len(velocities)

    kinetic_energy = 0.5 * np.sum(masses * np.sum(velocities**2, axis=1))

    T = 2 * kinetic_energy / (3 * n_atoms)

    return T





def berendsen_thermostat(

    velocities: np.ndarray,

    masses: np.ndarray,

    target_T: float,

    tau: float = 0.1,

    dt: float = 0.001

) -> np.ndarray:

    """

    Berendsen热浴（温度耦合）



    参数:

        velocities: 速度

        masses: 质量

        target_T: 目标温度

        tau: 耦合时间

        dt: 时间步长



    返回:

        调整后的速度

    """

    current_T = compute_temperature(velocities, masses)

    if current_T < 1e-10:

        return velocities



    scale = np.sqrt(1 + dt / tau * (target_T / current_T - 1))

    return velocities * scale





if __name__ == '__main__':

    print('=== 分子动力学模拟基础测试 ===')



    # 测试1: Lennard-Jones势

    print('\n--- 测试1: Lennard-Jones势 ---')

    r_range = np.linspace(0.8, 3.0, 50)

    for r in [0.9, 1.0, 1.2, 1.5, 2.0]:

        U = lennard_jones_potential(r, epsilon=1.0, sigma=1.0)

        print(f'  r={r:.2f}: U={U:.4f}')



    # 测试2: 能量最小化

    print('\n--- 测试2: 能量最小化 ---')

    np.random.seed(42)

    n_atoms = 10

    initial_coords = np.random.rand(n_atoms, 3) * 5



    minimized = energy_minimization_steepest_descent(

        initial_coords, epsilon=0.5, sigma=2.0, n_steps=50, step_size=0.2

    )



    print(f'  初始RMSD: {np.std(initial_coords):.3f}')

    print(f'  最小化后: {np.std(minimized):.3f}')



    # 测试3: Verlet积分

    print('\n--- 测试3: Verlet积分 ---')

    n_atoms = 2

    positions = np.array([[0.0, 0.0, 0.0], [1.5, 0.0, 0.0]])

    velocities = np.zeros((n_atoms, 3))

    masses = np.array([1.0, 1.0])



    print(f'  初始位置: {positions[1] - positions[0]}')



    for step in range(100):

        forces = compute_forces(positions, epsilon=1.0, sigma=1.0)

        total_force = np.sum(forces, axis=1)

        positions, velocities = verlet_integration(positions, velocities, total_force, masses, 0.01)



        if step % 20 == 0:

            dist = np.linalg.norm(positions[1] - positions[0])

            print(f'  步{step}: 距离={dist:.4f}')



    # 测试4: 温度计算

    print('\n--- 测试4: 温度计算 ---')

    velocities = np.random.randn(10, 3)

    masses = np.ones(10)

    T = compute_temperature(velocities, masses)

    print(f'  随机速度的温度: {T:.4f}')



    # 测试5: 热浴

    print('\n--- 测试5: Berendsen热浴 ---')

    velocities = np.random.randn(10, 3)

    masses = np.ones(10)

    T_before = compute_temperature(velocities, masses)

    velocities_adjusted = berendsen_thermostat(velocities, masses, target_T=1.0)

    T_after = compute_temperature(velocities_adjusted, masses)

    print(f'  调整前温度: {T_before:.4f}')

    print(f'  目标温度: 1.0')

    print(f'  调整后温度: {T_after:.4f}')

