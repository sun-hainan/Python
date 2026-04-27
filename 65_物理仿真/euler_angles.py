# -*- coding: utf-8 -*-

"""

算法实现：物理仿真 / euler_angles



本文件实现 euler_angles 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D





class EulerAngles:

    """

    欧拉角类

    

    支持Z-X-Z内旋序（Intrinsic）约定

    """

    

    def __init__(self, alpha=0.0, beta=0.0, gamma=0.0):

        """

        初始化欧拉角

        

        参数:

            alpha: 第一次旋转角度（绕Z轴），弧度

            beta: 第二次旋转角度（绕X轴），弧度

            gamma: 第三次旋转角度（绕Z轴），弧度

        """

        self.alpha = alpha

        self.beta = beta

        self.gamma = gamma

    

    def to_rotation_matrix(self):

        """

        将欧拉角转换为3x3旋转矩阵

        

        使用Z-X-Z内旋序（绕固定轴的顺序是Z->X->Z）

        内旋等价于外旋的X->Y->Z顺序

        

        返回:

            rotation_matrix: 3x3 numpy array

        """

        ca, cb, cg = np.cos(self.alpha), np.cos(self.beta), np.cos(self.gamma)

        sa, sb, sg = np.sin(self.alpha), np.sin(self.beta), np.sin(self.gamma)

        

        # Z-X-Z欧拉角旋转矩阵

        # R = Rz(α) * Rx(β) * Rz(γ)

        r00 = ca*cg - sa*cb*sg

        r01 = -ca*sg - sa*cb*cg

        r02 = sa*sb

        

        r10 = sa*cg + ca*cb*sg

        r11 = -sa*sg + ca*cb*cg

        r12 = -ca*sb

        

        r20 = sb*sg

        r21 = sb*cg

        r22 = cb

        

        return np.array([

            [r00, r01, r02],

            [r10, r11, r12],

            [r20, r21, r22]

        ])

    

    def rotate_vector(self, v):

        """

        使用欧拉角旋转向量

        

        参数:

            v: 三维向量, numpy array [3]

        

        返回:

            旋转后的向量

        """

        rot_matrix = self.to_rotation_matrix()

        return rot_matrix @ np.array(v)

    

    @classmethod

    def from_rotation_matrix(cls, R):

        """

        从旋转矩阵提取欧拉角（Z-X-Z序）

        

        参数:

            R: 3x3旋转矩阵

        

        返回:

            EulerAngles对象

        """

        # 检查输入是否有效

        if R.shape != (3, 3):

            raise ValueError("旋转矩阵必须是3x3")

        

        # 检查正交性（允许小误差）

        if not (np.allclose(R @ R.T, np.eye(3), atol=1e-6) and np.isclose(np.linalg.det(R), 1.0, atol=1e-6)):

            raise ValueError("无效的旋转矩阵")

        

        # 从矩阵提取欧拉角

        # r22 = cos(beta)

        cb = R[2, 2]

        

        if np.abs(cb) < 1e-10:

            # 万向锁情况：beta = ±90°

            # 此时只有关于alpha和gamma的和有意义

            alpha = np.arctan2(R[0, 1], R[0, 0])

            beta = np.pi/2 if cb > 0 else -np.pi/2

            gamma = 0.0

        else:

            # 正常情况

            sb = np.sqrt(1 - cb**2)

            alpha = np.arctan2(R[1, 2], -R[0, 2])

            beta = np.arctan2(sb, cb)

            gamma = np.arctan2(R[2, 1], R[2, 0])

        

        return cls(alpha=alpha, beta=beta, gamma=gamma)

    

    @classmethod

    def from_quaternion_components(cls, w, x, y, z):

        """

        从四元数分量创建欧拉角

        

        参数:

            w, x, y, z: 四元数分量

        

        返回:

            EulerAngles对象

        """

        # 归一化

        norm = np.sqrt(w**2 + x**2 + y**2 + z**2)

        w, x, y, z = w/norm, x/norm, y/norm, z/norm

        

        # 四元数转旋转矩阵元素

        r00 = 1 - 2*(y*y + z*z)

        r01 = 2*(x*y - w*z)

        r02 = 2*(x*z + w*y)

        r10 = 2*(x*y + w*z)

        r11 = 1 - 2*(x*x + z*z)

        r12 = 2*(y*z - w*x)

        r20 = 2*(x*z - w*y)

        r21 = 2*(y*z + w*x)

        r22 = 1 - 2*(x*x + y*y)

        

        R = np.array([

            [r00, r01, r02],

            [r10, r11, r12],

            [r20, r21, r22]

        ])

        

        return cls.from_rotation_matrix(R)

    

    def to_degrees(self):

        """

        转换为角度制

        

        返回:

            (alpha_deg, beta_deg, gamma_deg)

        """

        return (

            np.degrees(self.alpha),

            np.degrees(self.beta),

            np.degrees(self.gamma)

        )

    

    @classmethod

    def from_degrees(cls, alpha_deg, beta_deg, gamma_deg):

        """

        从角度制创建欧拉角

        

        参数:

            alpha_deg, beta_deg, gamma_deg: 角度值（度）

        

        返回:

            EulerAngles对象

        """

        return cls(

            alpha=np.radians(alpha_deg),

            beta=np.radians(beta_deg),

            gamma=np.radians(gamma_deg)

        )

    

    def interpolate_linear(self, other, t):

        """

        线性插值（注意：不是最优的插值方式）

        

        直接对角度线性插值，可能走"弯路"

        

        参数:

            other: 目标欧拉角

            t: 插值参数 [0, 1]

        

        返回:

            插值欧拉角

        """

        # 注意：直接线性插值在角度跨越±180°时可能不优

        alpha = self.alpha + t * (other.alpha - self.alpha)

        beta = self.beta + t * (other.beta - self.beta)

        gamma = self.gamma + t * (other.gamma - self.gamma)

        return EulerAngles(alpha=alpha, beta=beta, gamma=gamma)

    

    def __repr__(self):

        a, b, g = self.to_degrees()

        return f"EulerAngles(α={a:.1f}°, β={b:.1f}°, γ={g:.1f}°)"





def demonstrate_gimbal_lock():

    """

    演示万向锁问题

    

    当beta=±90°时，alpha和gamma的旋转效果相同

    丢失了一个自由度

    """

    print("=" * 55)

    print("万向锁（Gimbal Lock）演示")

    print("=" * 55)

    

    # 测试向量

    test_vector = np.array([1.0, 0.0, 0.0])

    

    # 情况1：正常旋转

    print("\n情况1：正常旋转 (α=30°, β=45°, γ=60°)")

    euler_normal = EulerAngles.from_degrees(30, 45, 60)

    rotated_normal = euler_normal.rotate_vector(test_vector)

    print(f"  欧拉角: {euler_normal}")

    print(f"  X+轴旋转后: [{rotated_normal[0]:.4f}, {rotated_normal[1]:.4f}, {rotated_normal[2]:.4f}]")

    

    # 情况2：接近万向锁（β=89°）

    print("\n情况2：接近万向锁 (α=30°, β=89°, γ=60°)")

    euler_near = EulerAngles.from_degrees(30, 89, 60)

    rotated_near = euler_near.rotate_vector(test_vector)

    print(f"  欧拉角: {euler_near}")

    print(f"  X+轴旋转后: [{rotated_near[0]:.4f}, {rotated_near[1]:.4f}, {rotated_near[2]:.4f}]")

    

    # 情况3：万向锁状态（β=90°）

    print("\n情况3：万向锁状态 (α=30°, β=90°, γ=60°)")

    euler_lock = EulerAngles.from_degrees(30, 90, 60)

    rotated_lock = euler_lock.rotate_vector(test_vector)

    print(f"  欧拉角: {euler_lock}")

    print(f"  X+轴旋转后: [{rotated_lock[0]:.4f}, {rotated_lock[1]:.4f}, {rotated_lock[2]:.4f}]")

    

    # 情况4：万向锁，但α和γ交换（应该与情况3不同，但这里会相同）

    print("\n情况4：万向锁交换 (α=60°, β=90°, γ=30°)")

    euler_lock2 = EulerAngles.from_degrees(60, 90, 30)

    rotated_lock2 = euler_lock2.rotate_vector(test_vector)

    print(f"  欧拉角: {euler_lock2}")

    print(f"  X+轴旋转后: [{rotated_lock2[0]:.4f}, {rotated_lock2[1]:.4f}, {rotated_lock2[2]:.4f}]")

    

    print(f"\n结论：情况3和4旋转结果相同（都是[{rotated_lock[0]:.4f}, {rotated_lock[1]:.4f}, {rotated_lock[2]:.4f}]）")

    print("这说明在万向锁状态下，α和γ的旋转效果无法区分！")





def plot_euler_rotation_comparison():

    """

    可视化欧拉角旋转效果

    """

    # 定义测试向量

    test_vectors = [

        np.array([1.0, 0.0, 0.0]),

        np.array([0.0, 1.0, 0.0]),

        np.array([0.0, 0.0, 1.0]),

    ]

    colors = ['r', 'g', 'b']

    

    # 不同旋转角度

    angles_list = [

        EulerAngles.from_degrees(0, 0, 0),      # 无旋转

        EulerAngles.from_degrees(45, 30, 60),   # 一般旋转

        EulerAngles.from_degrees(90, 45, 30),   # 较大旋转

        EulerAngles.from_degrees(0, 89, 0),     # 接近万向锁

    ]

    titles = ['原始', '一般旋转(45°,30°,60°)', '大旋转(90°,45°,30°)', '接近万向锁(0°,89°,0°)']

    

    fig = plt.figure(figsize=(16, 4))

    

    for i, (euler, title) in enumerate(zip(angles_list, titles)):

        ax = fig.add_subplot(1, 4, i+1, projection='3d')

        

        for vec, color in zip(test_vectors, colors):

            rotated = euler.rotate_vector(vec)

            ax.quiver(0, 0, 0, rotated[0], rotated[1], rotated[2], 

                     color=color, arrow_length_ratio=0.15, linewidth=2)

        

        # 绘制坐标轴

        for axis, color in zip([np.eye(3)], [['gray']]):

            for j, c in enumerate(['r', 'g', 'b']):

                ax.quiver(0, 0, 0, axis[0, j], axis[1, j], axis[2, j],

                         color=c, alpha=0.3, arrow_length_ratio=0.1)

        

        ax.set_xlim([-1.5, 1.5])

        ax.set_ylim([-1.5, 1.5])

        ax.set_zlim([-1.5, 1.5])

        ax.set_xlabel('X')

        ax.set_ylabel('Y')

        ax.set_zlabel('Z')

        ax.set_title(title)

        ax.set_box_aspect([1,1,1])

    

    plt.tight_layout()

    plt.savefig('euler_angles_result.png', dpi=150)

    plt.show()

    print("图像已保存至 euler_angles_result.png")





def compare_euler_quaternion():

    """

    对比欧拉角和四元数

    """

    print("\n" + "=" * 55)

    print("欧拉角 vs 四元数 对比")

    print("=" * 55)

    

    # 相同旋转

    print("\n测试：绕Z轴旋转90°")

    

    # 欧拉角

    euler = EulerAngles.from_degrees(90, 0, 0)

    print(f"  欧拉角: {euler}")

    

    # 四元数（等效）

    # 绕Z轴90° = 四元数 (cos45°, 0, 0, sin45°)

    w, x, y, z = np.cos(np.pi/4), 0, 0, np.sin(np.pi/4)

    print(f"  四元数: w={w:.4f}, x={x:.4f}, y={y:.4f}, z={z:.4f}")

    

    # 测试向量

    test = np.array([1.0, 0.0, 0.0])

    

    euler_rotated = euler.rotate_vector(test)

    print(f"\n  欧拉角旋转X+: [{euler_rotated[0]:.4f}, {euler_rotated[1]:.4f}, {euler_rotated[2]:.4f}]")

    print(f"  理论值:       [0.0000, 1.0000, 0.0000]")





if __name__ == "__main__":

    # 演示万向锁

    demonstrate_gimbal_lock()

    

    # 对比欧拉角和四元数

    compare_euler_quaternion()

    

    # 可视化

    print("\n生成可视化图像...")

    plot_euler_rotation_comparison()

    

    print("\n测试完成！欧拉角直观但有万向锁，建议使用四元数进行计算。")

