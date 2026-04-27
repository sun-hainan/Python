# -*- coding: utf-8 -*-

"""

算法实现：25_深度学习核心算法 / optimizer_adam



本文件实现 optimizer_adam 相关的算法功能。

"""



import numpy as np





class Adam:

    """

    Adam优化器

    

    参数:

        params: 待优化参数列表

        lr: 初始学习率（默认0.001）

        beta1: 梯度一阶矩的指数衰减率（默认0.9）

        beta2: 梯度二阶矩的指数衰减率（默认0.999）

        epsilon: 防止除零的小常数（默认1e-8）

        weight_decay: L2正则化系数（默认为0）

    """

    

    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999,

                 epsilon=1e-8, weight_decay=0.0):

        self.params = params

        self.lr = lr

        self.beta1 = beta1

        self.beta2 = beta2

        self.eps = epsilon

        self.weight_decay = weight_decay

        

        # 一阶矩估计：梯度的指数移动平均（类似动量）

        self.m = [np.zeros_like(p.data if hasattr(p, 'data') else p) for p in params]

        # 二阶矩估计：梯度平方的指数移动平均

        self.v = [np.zeros_like(p.data if hasattr(p, 'data') else p) for p in params]

        # 迭代计数器（用于偏置校正）

        self.t = 0

    

    def step(self):

        """执行一次参数更新"""

        self.t += 1

        

        for i, param in enumerate(self.params):

            data = param.data if hasattr(param, 'data') else param

            grad = param.grad if hasattr(param, 'grad') else param['grad']

            

            # 梯度裁剪：防止梯度爆炸（可选）

            grad = np.clip(grad, -5.0, 5.0)

            

            # 更新一阶矩估计（梯度均值）

            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad

            # 更新二阶矩估计（梯度方差）

            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)

            

            # 偏置校正（因为m和v初始为0，会向0偏移）

            # 训练早期，m和v会被低估，需要校正

            m_hat = self.m[i] / (1 - self.beta1 ** self.t)

            v_hat = self.v[i] / (1 - self.beta2 ** self.t)

            

            # 参数更新：结合动量和自适应学习率

            if self.weight_decay > 0:

                # AdamW：直接对参数做L2正则（更正确的权重衰减方式）

                data = data - self.lr * (m_hat / (np.sqrt(v_hat) + self.eps) 

                                         + self.weight_decay * data)

            else:

                data = data - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

            

            # 写回参数

            if hasattr(param, 'data'):

                param.data = data

            else:

                param['data'] = data

    

    def zero_grad(self):

        """清零所有参数的梯度"""

        for param in self.params:

            if hasattr(param, 'grad'):

                param.grad = np.zeros_like(param.grad)





class AdamW:

    """

    AdamW（Adam with Weight Decay）优化器

    将权重衰减与自适应学习率解耦，是Adam的改进版本

    """

    

    def __init__(self, params, lr=0.001, betas=(0.9, 0.999),

                 eps=1e-8, weight_decay=0.01):

        self.params = params

        self.lr = lr

        self.beta1, self.beta2 = betas

        self.eps = eps

        self.weight_decay = weight_decay

        

        self.m = [np.zeros_like(p.data if hasattr(p, 'data') else p) for p in params]

        self.v = [np.zeros_like(p.data if hasattr(p, 'data') else p) for p in params]

        self.t = 0

    

    def step(self):

        """执行一次参数更新"""

        self.t += 1

        

        for i, param in enumerate(self.params):

            data = param.data if hasattr(param, 'data') else param

            grad = param.grad if hasattr(param, 'grad') else param['grad']

            

            # 更新一阶和二阶矩

            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad

            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)

            

            # 偏置校正

            m_hat = self.m[i] / (1 - self.beta1 ** self.t)

            v_hat = self.v[i] / (1 - self.beta2 ** self.t)

            

            # AdamW的核心：权重衰减是独立的，不参与梯度计算

            # 这与L2正则化不同，L2正则化的梯度会被Adam的自适应学习率缩放

            data = data - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

            data = data - self.lr * self.weight_decay * data

            

            if hasattr(param, 'data'):

                param.data = data

            else:

                param['data'] = data

    

    def zero_grad(self):

        for param in self.params:

            if hasattr(param, 'grad'):

                param.grad = np.zeros_like(param.grad)





# ============================

# 测试代码

# ============================



if __name__ == "__main__":

    np.random.seed(42)

    

    class SimpleParam:

        """模拟参数容器"""

        def __init__(self, data):

            self.data = data

            self.grad = np.zeros_like(data)

    

    print("=" * 55)

    print("Adam优化器测试：最小化 Rosenbrock函数")

    print("=" * 55)

    

    # Rosenbrock函数：f(x,y) = (1-x)^2 + 100(y-x^2)^2

    # 全局最小值在(x,y)=(1,1)

    

    # 测试Adam

    x = SimpleParam(np.array([0.0, 0.0], dtype=np.float64))

    optimizer = Adam([x], lr=0.001, weight_decay=0.0)

    

    print("\n--- Adam优化 ---")

    for epoch in range(1, 5001):

        # 计算Rosenbrock函数梯度

        x.grad = np.array([

            -2 * (1 - x.data[0]) - 400 * x.data[0] * (x.data[1] - x.data[0]**2),

            200 * (x.data[1] - x.data[0]**2)

        ])

        

        optimizer.step()

        optimizer.zero_grad()

        

        if epoch % 1000 == 0:

            loss = (1 - x.data[0])**2 + 100 * (x.data[1] - x.data[0]**2)**2

            print(f"Epoch {epoch:5d}: ({x.data[0]:.4f}, {x.data[1]:.4f}), loss={loss:.2f}")

    

    print(f"\n最终: ({x.data[0]:.6f}, {x.data[1]:.6f})")

    

    # 测试AdamW

    x2 = SimpleParam(np.array([0.0, 0.0], dtype=np.float64))

    optimizer_w = AdamW([x2], lr=0.001, weight_decay=0.01)

    

    print("\n--- AdamW优化 (weight_decay=0.01) ---")

    for epoch in range(1, 5001):

        x2.grad = np.array([

            -2 * (1 - x2.data[0]) - 400 * x2.data[0] * (x2.data[1] - x2.data[0]**2),

            200 * (x2.data[1] - x2.data[0]**2)

        ])

        optimizer_w.step()

        optimizer_w.zero_grad()

    

    print(f"AdamW最终: ({x2.data[0]:.6f}, {x2.data[1]:.6f})")

    print("\nAdam优化器测试完成！")

