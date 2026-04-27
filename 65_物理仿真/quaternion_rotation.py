# -*- coding: utf-8 -*-

"""

算法实现：物理仿真 / quaternion_rotation



本文件实现 quaternion_rotation 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D





class Quaternion:

    """

    四元数类

    

    四元数 q = w + xi + yj + zk

    其中 w 是标量部分，(x,y,z) 是矢量部分

    对于单位四元数：w² + x² + y² + z² = 1

    """

    

    def __init__(self, w=1.0, x=0.0, y=0.0, z=0.0):

        """

        初始化四元数

        

        参数:

            w: 标量部分（实部）

            x, y, z: 矢量部分（虚部）

        """

        self.w = w

        self.x = x

        self.y = y

        self.z = z

    

    @classmethod

    def from_axis_angle(cls, axis, angle):

        """

        从旋转轴和角度创建四元数

        

        参数:

            axis: 旋转轴（单位向量）, numpy array [3]

            angle: 旋转角度（弧度）, float

        

        返回:

            Quaternion: 单位四元数

        """

        # 确保轴是单位向量

        axis = np.array(axis, dtype=float)

        axis = axis / np.linalg.norm(axis)

        

        # 半角公式：q = cos(θ/2) + sin(θ/2) * (xi + yj + zk)

        half_angle = angle / 2.0

        w = np.cos(half_angle)

        sin_half = np.sin(half_angle)

        x, y, z = axis * sin_half

        

        return cls(w=w, x=x, y=y, z=z)

    

    @classmethod

    def identity(cls):

        """

        创建单位四元数（对应无旋转）

        """

        return cls(w=1.0, x=0.0, y=0.0, z=0.0)

    

    def __mul__(self, other):

        """

        四元数乘法（用于组合旋转）

        

        q1 * q2 表示：先应用q2旋转，再应用q1旋转

        

        参数:

            other: 另一个四元数

        

        返回:

            乘积四元数

        """

        # 提取分量

        w1, x1, y1, z1 = self.w, self.x, self.y, self.z

        w2, x2, y2, z2 = other.w, other.x, other.y, other.z

        

        # 四元数乘法公式

        w = w1*w2 - x1*x2 - y1*y2 - z1*z2

        x = w1*x2 + x1*w2 + y1*z2 - z1*y2

        y = w1*y2 - x1*z2 + y1*w2 + z1*x2

        z = w1*z2 + x1*y2 - y1*x2 + z1*w2

        

        return Quaternion(w=w, x=x, y=y, z=z)

    

    def conjugate(self):

        """

        四元数共轭：q* = w - xi - yj - zk

        

        返回:

            共轭四元数

        """

        return Quaternion(w=self.w, x=-self.x, y=-self.y, z=-self.z)

    

    def norm(self):

        """

        四元数的模（范数）

        

        返回:

            float: sqrt(w² + x² + y² + z²)

        """

        return np.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)

    

    def normalize(self):

        """

        归一化四元数

        """

        n = self.norm()

        if n > 1e-10:  # 避免除零

            self.w /= n

            self.x /= n

            self.y /= n

            self.z /= n

        return self

    

    def to_rotation_matrix(self):

        """

        将四元数转换为3x3旋转矩阵

        

        返回:

            rotation_matrix: 3x3 numpy array

        """

        # 归一化确保是单位四元数

        q = Quaternion(w=self.w, x=self.x, y=self.y, z=self.z)

        q.normalize()

        

        w, x, y, z = q.w, q.x, q.y, q.z

        

        # 旋转矩阵公式

        r00 = 1 - 2*(y*y + z*z)

        r01 = 2*(x*y - w*z)

        r02 = 2*(x*z + w*y)

        

        r10 = 2*(x*y + w*z)

        r11 = 1 - 2*(x*x + z*z)

        r12 = 2*(y*z - w*x)

        

        r20 = 2*(x*z - w*y)

        r21 = 2*(y*z + w*x)

        r22 = 1 - 2*(x*x + y*y)

        

        return np.array([

            [r00, r01, r02],

            [r10, r11, r12],

            [r20, r21, r22]

        ])

    

    def rotate_vector(self, v):

        """

        使用四元数旋转三维向量

        

        参数:

            v: 三维向量, numpy array [3]

        

        返回:

            旋转后的向量

        """

        # 将向量扩展为纯四元数 (0, vx, vy, vz)

        v_quat = Quaternion(w=0.0, x=v[0], y=v[1], z=v[2])

        

        # 旋转公式：v' = q * v * q^(-1)

        # 由于q是单位四元数，q^(-1) = q*

        rotated = self * v_quat * self.conjugate()

        

        # 返回向量部分

        return np.array([rotated.x, rotated.y, rotated.z])

    

    def slerp(self, other, t):

        """

        四元数球面线性插值（Spherical Linear Interpolation）

        

        用于在两个旋转之间平滑过渡

        

        参数:

            other: 目标四元数

            t: 插值参数 [0, 1]，0返回自身，1返回other

        

        返回:

            插值四元数

        """

        # 确保两个四元数都是单位四元数

        q1 = Quaternion(w=self.w, x=self.x, y=self.y, z=self.z)

        q1.normalize()

        q2 = Quaternion(w=other.w, x=other.x, y=other.y, z=other.z)

        q2.normalize()

        

        # 计算点积（余弦值）

        cos_half_theta = q1.w*q2.w + q1.x*q2.x + q1.y*q2.y + q1.z*q2.z

        

        # 如果dot为负，取反以确保走短弧

        if cos_half_theta < 0:

            q2.w = -q2.w

            q2.x = -q2.x

            q2.y = -q2.y

            q2.z = -q2.z

            cos_half_theta = -cos_half_theta

        

        # 如果非常接近，使用线性插值

        if cos_half_theta > 0.9995:

            result_w = q1.w + t*(q2.w - q1.w)

            result_x = q1.x + t*(q2.x - q1.x)

            result_y = q1.y + t*(q2.y - q1.y)

            result_z = q1.z + t*(q2.z - q1.z)

            return Quaternion(w=result_w, x=result_x, y=result_y, z=result_z)

        

        # 计算半角和sin值

        half_theta = np.arccos(cos_half_theta)

        sin_half_theta = np.sqrt(1.0 - cos_half_theta**2)

        

        # 球面插值公式

        a = np.sin((1-t)*half_theta) / sin_half_theta

        b = np.sin(t*half_theta) / sin_half_theta

        

        return Quaternion(

            w=a*q1.w + b*q2.w,

            x=a*q1.x + b*q2.x,

            y=a*q1.y + b*q2.y,

            z=a*q1.z + b*q2.z

        )

    

    def __repr__(self):

        return f"Quaternion(w={self.w:.4f}, x={self.x:.4f}, y={self.y:.4f}, z={self.z:.4f})"





def plot_rotation_comparison():

    """

    可视化对比四元数旋转和欧拉角旋转

    """

    # 定义测试向量

    original_vectors = [

        np.array([1.0, 0.0, 0.0]),  # X轴

        np.array([0.0, 1.0, 0.0]),  # Y轴

        np.array([0.0, 0.0, 1.0]),  # Z轴

        np.array([1.0, 1.0, 1.0]),  # 对角线

    ]

    original_vectors = [v / np.linalg.norm(v) for v in original_vectors]  # 归一化

    

    # 创建两个旋转四元数

    # 绕Z轴旋转90度

    q_z = Quaternion.from_axis_angle(np.array([0, 0, 1]), np.pi/2)

    

    # 绕Y轴旋转90度

    q_y = Quaternion.from_axis_angle(np.array([0, 1, 0]), np.pi/2)

    

    # 组合旋转：先Z后Y

    q_combined = q_z * q_y

    

    # 绘制3D对比图

    fig = plt.figure(figsize=(14, 5))

    

    # 原始向量

    ax1 = fig.add_subplot(131, projection='3d')

    for i, v in enumerate(original_vectors):

        color = ['r', 'g', 'b', 'm'][i]

        ax1.quiver(0, 0, 0, v[0], v[1], v[2], color=color, arrow_length_ratio=0.15)

    ax1.set_xlim([-1.5, 1.5])

    ax1.set_ylim([-1.5, 1.5])

    ax1.set_zlim([-1.5, 1.5])

    ax1.set_xlabel('X')

    ax1.set_ylabel('Y')

    ax1.set_zlabel('Z')

    ax1.set_title('原始向量')

    ax1.set_box_aspect([1,1,1])

    

    # 单独旋转（Z轴90度）

    ax2 = fig.add_subplot(132, projection='3d')

    for i, v in enumerate(original_vectors):

        color = ['r', 'g', 'b', 'm'][i]

        rotated = q_z.rotate_vector(v)

        ax2.quiver(0, 0, 0, rotated[0], rotated[1], rotated[2], color=color, arrow_length_ratio=0.15)

    ax2.set_xlim([-1.5, 1.5])

    ax2.set_ylim([-1.5, 1.5])

    ax2.set_zlim([-1.5, 1.5])

    ax2.set_xlabel('X')

    ax2.set_ylabel('Y')

    ax2.set_zlabel('Z')

    ax2.set_title('绕Z轴旋转90°')

    ax2.set_box_aspect([1,1,1])

    

    # 组合旋转

    ax3 = fig.add_subplot(133, projection='3d')

    for i, v in enumerate(original_vectors):

        color = ['r', 'g', 'b', 'm'][i]

        rotated = q_combined.rotate_vector(v)

        ax3.quiver(0, 0, 0, rotated[0], rotated[1], rotated[2], color=color, arrow_length_ratio=0.15)

    ax3.set_xlim([-1.5, 1.5])

    ax3.set_ylim([-1.5, 1.5])

    ax3.set_zlim([-1.5, 1.5])

    ax3.set_xlabel('X')

    ax3.set_ylabel('Y')

    ax3.set_zlabel('Z')

    ax3.set_title('先Z后Y各90°')

    ax3.set_box_aspect([1,1,1])

    

    plt.tight_layout()

    plt.savefig('quaternion_rotation_result.png', dpi=150)

    plt.show()

    print("图像已保存至 quaternion_rotation_result.png")





def plot_slerp_interpolation():

    """

    可视化四元数SLERP插值

    """

    # 从朝X+到朝Y+的旋转

    q_start = Quaternion.from_axis_angle(np.array([0, 0, 1]), 0)  # 初始朝向X+

    q_end = Quaternion.from_axis_angle(np.array([0, 0, 1]), np.pi/2)  # 旋转到Y+

    

    # 采样多个时间点

    t_values = np.linspace(0, 1, 11)

    positions = []

    

    # 原始向量（X轴方向）

    test_vector = np.array([1.0, 0.0, 0.0])

    

    for t in t_values:

        # SLERP插值

        q_interp = q_start.slerp(q_end, t)

        # 旋转后的X轴方向

        rotated = q_interp.rotate_vector(test_vector)

        positions.append(rotated)

    

    positions = np.array(positions)

    

    # 绘图

    fig = plt.figure(figsize=(10, 5))

    

    # 3D轨迹

    ax1 = fig.add_subplot(121, projection='3d')

    ax1.plot(positions[:, 0], positions[:, 1], positions[:, 2], 'b-o', markersize=8)

    ax1.quiver(0, 0, 0, 1, 0, 0, color='r', arrow_length_ratio=0.1, label='X+ (初始)')

    ax1.quiver(0, 0, 0, 0, 1, 0, color='g', arrow_length_ratio=0.1, label='Y+ (目标)')

    ax1.set_xlabel('X')

    ax1.set_ylabel('Y')

    ax1.set_zlabel('Z')

    ax1.set_title('SLERP轨迹（球面大圆）')

    ax1.legend()

    ax1.set_box_aspect([1,1,1])

    

    # XY平面投影

    ax2 = fig.add_subplot(122)

    ax2.plot(positions[:, 0], positions[:, 1], 'b-o', markersize=8)

    circle = plt.Circle((0, 0), 1, fill=False, color='gray', linestyle='--')

    ax2.add_patch(circle)

    ax2.axhline(y=0, color='k', alpha=0.3)

    ax2.axvline(x=0, color='k', alpha=0.3)

    ax2.set_xlim([-1.5, 1.5])

    ax2.set_ylim([-1.5, 1.5])

    ax2.set_xlabel('X')

    ax2.set_ylabel('Y')

    ax2.set_title('XY平面投影（沿Z轴看）')

    ax2.set_aspect('equal')

    ax2.grid(True, alpha=0.3)

    

    plt.tight_layout()

    plt.savefig('quaternion_slerp_result.png', dpi=150)

    plt.show()

    print("图像已保存至 quaternion_slerp_result.png")





if __name__ == "__main__":

    print("=" * 55)

    print("四元数（Quaternion）旋转测试")

    print("=" * 55)

    

    # 基本操作测试

    print("\n1. 基本四元数操作:")

    q = Quaternion(w=0.707, x=0, y=0.707, z=0)

    print(f"   测试四元数: {q}")

    print(f"   模: {q.norm():.4f}")

    

    # 从轴角创建

    print("\n2. 从轴角创建四元数:")

    axis = np.array([0, 0, 1])  # Z轴

    angle = np.pi / 4  # 45度

    q = Quaternion.from_axis_angle(axis, angle)

    print(f"   绕Z轴旋转45°: {q}")

    print(f"   归一化模: {q.norm():.4f}")

    

    # 旋转向量

    print("\n3. 向量旋转:")

    test_vector = np.array([1.0, 0.0, 0.0])

    rotated = q.rotate_vector(test_vector)

    print(f"   原始向量: {test_vector}")

    print(f"   旋转后:  {rotated}")

    print(f"   理论值:  [0.707, 0.707, 0.0]")

    

    # 四元数乘法（组合旋转）

    print("\n4. 旋转组合 (q1 * q2):")

    q1 = Quaternion.from_axis_angle(np.array([0, 0, 1]), np.pi/2)  # 绕Z 90°

    q2 = Quaternion.from_axis_angle(np.array([0, 1, 0]), np.pi/2)  # 绕Y 90°

    q_combined = q1 * q2

    print(f"   q1 (绕Z 90°): {q1}")

    print(f"   q2 (绕Y 90°): {q2}")

    print(f"   组合: {q_combined}")

    

    # 验证矩阵转换

    print("\n5. 转换为旋转矩阵:")

    rot_matrix = q_combined.to_rotation_matrix()

    print(f"   旋转矩阵:\n{rot_matrix}")

    

    # 验证矩阵与四元数旋转一致性

    test = np.array([1.0, 0.0, 0.0])

    mat_rotated = rot_matrix @ test

    quat_rotated = q_combined.rotate_vector(test)

    print(f"   矩阵旋转X+: {mat_rotated}")

    print(f"   四元旋转X+: {quat_rotated}")

    print(f"   一致性: {np.allclose(mat_rotated, quat_rotated)}")

    

    # SLERP插值

    print("\n6. SLERP球面线性插值:")

    q_start = Quaternion.identity()

    q_end = Quaternion.from_axis_angle(np.array([0, 0, 1]), np.pi/2)

    print(f"   起点: {q_start}")

    print(f"   终点: {q_end}")

    q_mid = q_start.slerp(q_end, 0.5)

    print(f"   t=0.5: {q_mid}")

    

    # 绘制对比图

    print("\n7. 生成可视化图像...")

    plot_rotation_comparison()

    plot_slerp_interpolation()

    

    print("\n测试完成！四元数是3D旋转的最佳表示方法。")

