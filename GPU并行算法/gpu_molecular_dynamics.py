# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_molecular_dynamics

本文件实现 gpu_molecular_dynamics 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba
import math


def cpu_nbody(data, masses, n, dt):
    """
    CPU N-Body模拟（基准）
    
    参数:
        data: 位置数据 [x, y, z, vx, vy, vz] 每粒子6个值
        masses: 质量数组
        n: 粒子数
        dt: 时间步长
    
    返回:
        更新后的位置和速度
    """
    result = data.copy()
    
    for i in range(n):
        # 粒子i的位置和速度
        xi = data[i * 6 + 0]
        yi = data[i * 6 + 1]
        zi = data[i * 6 + 2]
        vxi = data[i * 6 + 3]
        vyi = data[i * 6 + 4]
        vzi = data[i * 6 + 5]
        
        # 计算作用于粒子i的力
        ax = 0.0
        ay = 0.0
        az = 0.0
        
        for j in range(n):
            if i != j:
                # 粒子j的位置
                xj = data[j * 6 + 0]
                yj = data[j * 6 + 1]
                zj = data[j * 6 + 2]
                
                # 距离计算
                dx = xj - xi
                dy = yj - yi
                dz = zj - zi
                r = math.sqrt(dx*dx + dy*dy + dz*dz) + 1e-10
                
                # 万有引力 (F = G*m1*m2/r^2)
                G = 6.674e-11
                mj = masses[j]
                force = G * mj / (r * r)
                
                # 加速度累加
                ax += force * dx / r
                ay += force * dy / r
                az += force * dz / r
        
        # 更新速度
        result[i * 6 + 3] = vxi + ax * dt
        result[i * 6 + 4] = vyi + ay * dt
        result[i * 6 + 5] = vzi + az * dt
        
        # 更新位置
        result[i * 6 + 0] = xi + result[i * 6 + 3] * dt
        result[i * 6 + 1] = yi + result[i * 6 + 4] * dt
        result[i * 6 + 2] = zi + result[i * 6 + 5] * dt
    
    return result


@cuda.jit
def gpu_nbody_kernel(data, masses, n, dt, G):
    """
    GPU N-Body模拟内核
    
    算法：每个线程计算一个粒子的受力
    注意：这是O(n²)复杂度的朴素算法
    
    参数:
        data: 位置和速度数组
        masses: 质量数组
        n: 粒子数
        dt: 时间步长
        G: 引力常数
    """
    i = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if i < n:
        # 获取粒子i的位置
        xi = data[i * 6 + 0]
        yi = data[i * 6 + 1]
        zi = data[i * 6 + 2]
        
        # 初始化加速度
        ax = 0.0
        ay = 0.0
        az = 0.0
        
        # 计算所有其他粒子对粒子i的引力
        for j in range(n):
            if i != j:
                xj = data[j * 6 + 0]
                yj = data[j * 6 + 1]
                zj = data[j * 6 + 2]
                
                dx = xj - xi
                dy = yj - yi
                dz = zj - zi
                r = math.sqrt(dx*dx + dy*dy + dz*dz) + 1e-10
                
                mj = masses[j]
                force = G * mj / (r * r)
                
                ax += force * dx / r
                ay += force * dy / r
                az += force * dz / r
        
        # 获取当前速度
        vxi = data[i * 6 + 3]
        vyi = data[i * 6 + 4]
        vzi = data[i * 6 + 5]
        
        # 更新速度和位置
        new_vx = vxi + ax * dt
        new_vy = vyi + ay * dt
        new_vz = vzi + az * dt
        
        new_x = xi + new_vx * dt
        new_y = yi + new_vy * dt
        new_z = zi + new_vz * dt
        
        # 写回（使用共享内存优化版本）
        data[i * 6 + 0] = new_x
        data[i * 6 + 1] = new_y
        data[i * 6 + 2] = new_z
        data[i * 6 + 3] = new_vx
        data[i * 6 + 4] = new_vy
        data[i * 6 + 5] = new_vz


@cuda.jit
def gpu_nbody_shared_kernel(data, masses, velocities, n, dt, G):
    """
    GPU N-Body优化内核（使用共享内存）
    
    优化策略：
    1. 将数据分块加载到共享内存
    2. 减少全局内存访问
    3. 利用共享内存的低延迟
    
    参数:
        data: 位置数据
        masses: 质量
        velocities: 速度（输出）
        n: 粒子数
        dt: 时间步长
        G: 引力常数
    """
    i = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    # 共享内存：存储位置数据块
    shared_pos = cuda.shared.array(256 * 3, dtype=numba.float32)  # x,y,z for 256 particles
    
    if i < n:
        xi = data[i * 6 + 0]
        yi = data[i * 6 + 1]
        zi = data[i * 6 + 2]
        
        ax = 0.0
        ay = 0.0
        az = 0.0
        
        # 分块处理
        block_size = cuda.blockDim.x
        num_blocks = (n + block_size - 1) // block_size
        
        for block in range(num_blocks):
            # 加载一个数据块到共享内存
            j_base = block * block_size
            tid = cuda.threadIdx.x
            
            if j_base + tid < n:
                shared_pos[tid * 3 + 0] = data[(j_base + tid) * 6 + 0]
                shared_pos[tid * 3 + 1] = data[(j_base + tid) * 6 + 1]
                shared_pos[tid * 3 + 2] = data[(j_base + tid) * 6 + 2]
            
            cuda.syncthreads()
            
            # 计算与该数据块的相互作用
            for j_idx in range(block_size):
                j = j_base + j_idx
                if j < n and j != i:
                    xj = shared_pos[j_idx * 3 + 0]
                    yj = shared_pos[j_idx * 3 + 1]
                    zj = shared_pos[j_idx * 3 + 2]
                    
                    dx = xj - xi
                    dy = yj - yi
                    dz = zj - zi
                    r = math.sqrt(dx*dx + dy*dy + dz*dz) + 1e-10
                    
                    mj = masses[j]
                    force = G * mj / (r * r)
                    
                    ax += force * dx / r
                    ay += force * dy / r
                    az += force * dz / r
            
            cuda.syncthreads()
        
        # 更新速度
        vxi = data[i * 6 + 3]
        vyi = data[i * 6 + 4]
        vzi = data[i * 6 + 5]
        
        velocities[i * 6 + 0] = vxi + ax * dt
        velocities[i * 6 + 1] = vyi + ay * dt
        velocities[i * 6 + 2] = vzi + az * dt


@cuda.jit
def gpu_update_positions_kernel(data, velocities, n, dt):
    """
    GPU位置更新内核
    
    参数:
        data: 位置数据
        velocities: 速度数据
        n: 粒子数
        dt: 时间步长
    """
    i = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if i < n:
        # 更新位置
        data[i * 6 + 0] += velocities[i * 6 + 0] * dt
        data[i * 6 + 1] += velocities[i * 6 + 1] * dt
        data[i * 6 + 2] += velocities[i * 6 + 2] * dt


def gpu_nbody(data, masses, n, dt, G=6.674e-11, use_shared=True):
    """
    GPU N-Body封装函数
    
    参数:
        data: 位置和速度数组
        masses: 质量数组
        n: 粒子数
        dt: 时间步长
        G: 引力常数
        use_shared: 是否使用共享内存优化
    
    返回:
        更新后的数据
    """
    data = data.astype(np.float32)
    masses = masses.astype(np.float32)
    
    d_data = cuda.to_device(data.copy())
    d_masses = cuda.to_device(masses)
    
    threads = 256
    blocks = (n + threads - 1) // threads
    
    if use_shared:
        # 优化版本：分离速度和位置更新
        velocities = np.zeros(n * 6, dtype=np.float32)
        d_velocities = cuda.to_device(velocities)
        
        # 计算新速度
        gpu_nbody_shared_kernel[blocks, threads](
            d_data, d_masses, d_velocities, n, dt, np.float32(G)
        )
        
        # 更新位置
        gpu_update_positions_kernel[blocks, threads](
            d_data, d_velocities, n, dt
        )
    else:
        # 朴素版本
        gpu_nbody_kernel[blocks, threads](
            d_data, d_masses, n, dt, np.float32(G)
        )
    
    return d_data.copy_to_host()


def compute_kinetic_energy(data, masses, n):
    """
    计算系统总动能
    
    参数:
        data: 位置和速度数据
        masses: 质量数组
        n: 粒子数
    
    返回:
        总动能
    """
    total_energy = 0.0
    
    for i in range(n):
        vx = data[i * 6 + 3]
        vy = data[i * 6 + 4]
        vz = data[i * 6 + 5]
        m = masses[i]
        
        v_sq = vx*vx + vy*vy + vz*vz
        total_energy += 0.5 * m * v_sq
    
    return total_energy


def run_demo():
    """运行N-Body模拟演示"""
    print("=" * 60)
    print("GPU并行算法示例：分子动力学N-Body模拟")
    print("=" * 60)
    
    n = 50  # 粒子数量
    dt = 0.01  # 时间步长
    
    # 初始化数据：位置和速度
    np.random.seed(42)
    positions = np.random.rand(n * 3) * 1000  # 位置 (米)
    velocities = np.random.rand(n * 3) * 100  # 速度 (米/秒)
    data = np.concatenate([positions, velocities])
    
    # 质量 (千克)
    masses = np.random.rand(n) * 1e30 + 1e28
    
    print(f"\n模拟参数: {n}个粒子, dt={dt}秒")
    
    # CPU计算（少量迭代）
    print("\n[计算验证]")
    cpu_data = data.copy()
    cpu_data = cpu_nbody(cpu_data, masses, n, dt)
    cpu_energy = compute_kinetic_energy(cpu_data, masses, n)
    print(f"  CPU动能: {cpu_energy:.4e}")
    
    # GPU计算（朴素版本）
    gpu_data_simple = gpu_nbody(data.copy(), masses, n, dt, use_shared=False)
    gpu_energy_simple = compute_kinetic_energy(gpu_data_simple, masses, n)
    print(f"  GPU朴素版动能: {gpu_energy_simple:.4e}")
    print(f"  与CPU误差: {abs(cpu_energy - gpu_energy_simple)/cpu_energy*100:.2f}%")
    
    # GPU计算（共享内存版本）
    gpu_data_shared = gpu_nbody(data.copy(), masses, n, dt, use_shared=True)
    gpu_energy_shared = compute_kinetic_energy(gpu_data_shared, masses, n)
    print(f"  GPU共享版动能: {gpu_energy_shared:.4e}")
    print(f"  与CPU误差: {abs(cpu_energy - gpu_energy_shared)/cpu_energy*100:.2f}%")
    
    # 性能测试
    print("\n[性能测试]")
    import time
    
    iterations = 100
    
    start = time.time()
    for _ in range(iterations):
        data_copy = data.copy()
        cpu_nbody(data_copy, masses, n, dt)
    cpu_time = time.time() - start
    print(f"  CPU ({iterations}次): {cpu_time:.4f}秒, 平均{ cpu_time/iterations*1000:.2f}ms/次")
    
    start = time.time()
    for _ in range(iterations):
        gpu_nbody(data.copy(), masses, n, dt, use_shared=False)
    gpu_simple_time = time.time() - start
    print(f"  GPU朴素版 ({iterations}次): {gpu_simple_time:.4f}秒, 平均{gpu_simple_time/iterations*1000:.2f}ms/次")
    
    start = time.time()
    for _ in range(iterations):
        gpu_nbody(data.copy(), masses, n, dt, use_shared=True)
    gpu_shared_time = time.time() - start
    print(f"  GPU共享版 ({iterations}次): {gpu_shared_time:.4f}秒, 平均{gpu_shared_time/iterations*1000:.2f}ms/次")
    
    print("\n" + "=" * 60)
    print("N-Body模拟核心概念:")
    print("  1. O(n²)复杂度：每个粒子与所有其他粒子交互")
    print("  2. 朴素版本：直接全局内存访问")
    print("  3. 共享内存优化：分块加载减少内存延迟")
    print("  4. 科学计算：天体物理、分子动力学等")
    print("  5. 进一步优化：Barnes-Hut树算法将复杂度降至O(n log n)")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
