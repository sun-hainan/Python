# -*- coding: utf-8 -*-

"""

算法实现：25_深度学习核心算法 / optimizer_sgd



本文件实现 optimizer_sgd 相关的算法功能。

"""



import numpy as np





class SGD:

    """

    随机梯度下降优化器

    

    参数:

        params: 待优化参数列表（如网络权重列表）

        lr: 学习率（learning rate）

        momentum: 动量系数（默认为0表示不使用动量）

        nesterov: 是否使用Nesterov动量

    """

    

    def __init__(self, params, lr=0.01, momentum=0.0, nesterov=False):

        self.params = params  # 网络中所有需要优化的参数

        self.lr = lr

        self.momentum = momentum

        self.nesterov = nesterov

        # velocity：动量项，存储历史梯度的指数加权移动

        self.velocity = [np.zeros_like(p) for p in params]

    

    def step(self):

        """

        执行一次参数更新

        标准SGD: w = w - lr * grad

        动量SGD: v = m*v + grad, w = w - lr*v

        Nesterov: 先用动量预测位置，再计算梯度

        """

        for i, param in enumerate(self.params):

            grad = param.grad if hasattr(param, 'grad') else param['grad']

            

            if self.nesterov:

                # Nesterov动量：先利用动量向前一步，再计算梯度

                v = self.momentum * self.velocity[i] + grad

                # 参数更新使用"向前看"的梯度

                self.velocity[i] = v

                param.data -= self.lr * v

            elif self.momentum > 0:

                # 标准动量：累积历史梯度方向

                self.velocity[i] = self.momentum * self.velocity[i] + grad

                param.data -= self.lr * self.velocity[i]

            else:

                # 纯SGD：无动量

                param.data -= self.lr * grad

    

    def zero_grad(self):

        """清零所有参数的梯度"""

        for param in self.params:

            if hasattr(param, 'grad'):

                param.grad = np.zeros_like(param.grad)

            elif isinstance(param, dict):

                param['grad'] = np.zeros_like(param['data'])





# ============================

# 辅助类：带梯度的参数容器

# ============================



class Param:

    """

    参数包装器：包含data和grad，兼容优化器接口

    

    参数:

        data: 参数值（numpy数组）

        grad: 参数梯度

    """

    def __init__(self, data):

        self.data = data

        self.grad = np.zeros_like(data)





# ============================

# 测试代码

# ============================



if __name__ == "__main__":

    np.random.seed(42)

    

    # 模拟一个简单优化问题：min f(x) = (x-3)^2，最优解x=3

    # 梯度：df/dx = 2(x-3)

    

    x = Param(np.array([0.0]))  # 初始值x=0

    optimizer = SGD([x], lr=0.1, momentum=0.9, nesterov=False)

    

    print("=" * 50)

    print("SGD优化器测试：最小化 f(x) = (x-3)^2")

    print("=" * 50)

    

    history = []

    for epoch in range(1, 51):

        # 计算梯度：df/dx = 2(x-3)

        x.grad = 2 * (x.data - 3)

        

        # 更新参数

        optimizer.step()

        optimizer.zero_grad()

        

        loss = (x.data[0] - 3) ** 2

        history.append(x.data[0])

        

        if epoch % 10 == 0:

            print(f"Epoch {epoch:3d}: x = {x.data[0]:.4f}, loss = {loss:.4f}")

    

    print(f"\n最终结果: x = {x.data[0]:.4f} (目标: 3.0)")

    print(f"收敛误差: {abs(x.data[0] - 3):.6f}")

    

    # 测试Nesterov动量

    print("\n" + "=" * 50)

    print("Nesterov动量测试")

    print("=" * 50)

    

    x2 = Param(np.array([0.0]))

    optimizer_nesterov = SGD([x2], lr=0.1, momentum=0.9, nesterov=True)

    

    for epoch in range(1, 51):

        x2.grad = 2 * (x2.data - 3)

        optimizer_nesterov.step()

        optimizer_nesterov.zero_grad()

    

    print(f"Nesterov最终: x = {x2.data[0]:.4f}")

    print("SGD优化器测试完成！")

