# -*- coding: utf-8 -*-

"""

算法实现：25_深度学习核心算法 / optimizer_adagrad_rmsprop_lamb



本文件实现 optimizer_adagrad_rmsprop_lamb 相关的算法功能。

"""



import numpy as np





class AdaGrad:

    """

    AdaGrad优化器（Adaptive Gradient）

    思想：对更新频繁的参数使用小学习率，稀疏参数使用大学习率

    

    参数:

        params: 待优化参数列表

        lr: 初始学习率（默认0.01）

        epsilon: 防止除零的小常数（默认1e-8）

    """

    

    def __init__(self, params, lr=0.01, epsilon=1e-8):

        self.params = params

        self.lr = lr

        self.eps = epsilon

        # 累积梯度平方（用于归一化学习率）

        self.accumulated_grad_sq = [

            np.zeros_like(p.data if hasattr(p, 'data') else p) for p in params

        ]

    

    def step(self):

        """执行一次参数更新"""

        for i, param in enumerate(self.params):

            data = param.data if hasattr(param, 'data') else param

            grad = param.grad if hasattr(param, 'grad') else param['grad']

            

            # 累积梯度平方

            self.accumulated_grad_sq[i] += grad ** 2

            

            # 自适应学习率：lr / sqrt(sum + eps)

            adaptive_lr = self.lr / (np.sqrt(self.accumulated_grad_sq[i]) + self.eps)

            

            data -= adaptive_lr * grad

            

            if hasattr(param, 'data'):

                param.data = data

            else:

                param['data'] = data

    

    def zero_grad(self):

        for param in self.params:

            if hasattr(param, 'grad'):

                param.grad = np.zeros_like(param.grad)





class RMSProp:

    """

    RMSProp优化器（Root Mean Square Propagation）

    使用指数衰减平均替代AdaGrad的累积和，解决学习率单调下降问题

    

    参数:

        params: 待优化参数列表

        lr: 学习率（默认0.001）

        beta: 衰减率（默认0.9）

        epsilon: 防止除零（默认1e-8）

        weight_decay: L2正则化系数

    """

    

    def __init__(self, params, lr=0.001, beta=0.9, epsilon=1e-8, weight_decay=0.0):

        self.params = params

        self.lr = lr

        self.beta = beta

        self.eps = epsilon

        self.weight_decay = weight_decay

        

        # 梯度平方的指数移动平均

        self.ewma_grad_sq = [

            np.zeros_like(p.data if hasattr(p, 'data') else p) for p in params

        ]

    

    def step(self):

        for i, param in enumerate(self.params):

            data = param.data if hasattr(param, 'data') else param

            grad = param.grad if hasattr(param, 'grad') else param['grad']

            

            # 更新梯度平方的指数移动平均

            self.ewma_grad_sq[i] = self.beta * self.ewma_grad_sq[i] + (1 - self.beta) * grad ** 2

            

            # 自适应学习率

            if self.weight_decay > 0:

                data = data - self.lr * (grad + self.weight_decay * data)

            else:

                data = data - self.lr * grad / (np.sqrt(self.ewma_grad_sq[i]) + self.eps)

            

            if hasattr(param, 'data'):

                param.data = data

            else:

                param['data'] = data

    

    def zero_grad(self):

        for param in self.params:

            if hasattr(param, 'grad'):

                param.grad = np.zeros_like(param.grad)





class LAMB:

    """

    LAMB优化器（Layer-wise Adaptive Moments for BERT）

    结合Adam和逐层学习率适应，适合大batch训练和BERT类模型

    

    参数:

        params: 待优化参数列表

        lr: 学习率

        beta1, beta2: Adam矩估计的衰减率

        epsilon: 防止除零

        weight_decay: 权重衰减系数

        gamma: 初始trust ratio的倍数（默认1.0）

    """

    

    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999,

                 epsilon=1e-6, weight_decay=0.01, gamma=1.0):

        self.params = params

        self.lr = lr

        self.beta1 = beta1

        self.beta2 = beta2

        self.eps = epsilon

        self.weight_decay = weight_decay

        self.gamma = gamma

        

        self.m = [np.zeros_like(p.data if hasattr(p, 'data') else p) for p in params]

        self.v = [np.zeros_like(p.data if hasattr(p, 'data') else p) for p in params]

        self.t = 0

    

    def step(self):

        self.t += 1

        

        for i, param in enumerate(self.params):

            data = param.data if hasattr(param, 'data') else param

            grad = param.grad if hasattr(param, 'grad') else param['grad']

            

            # Adam更新m和v

            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad

            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * grad ** 2

            

            # 偏置校正

            m_hat = self.m[i] / (1 - self.beta1 ** self.t)

            v_hat = self.v[i] / (1 - self.beta2 ** self.t)

            

            # LAMB的核心：计算trust ratio

            # r = ||w|| / (||m|| / (sqrt(v) + eps))

            norm_m = np.linalg.norm(m_hat)

            norm_v = np.sqrt(v_hat) + self.eps

            norm_w = np.linalg.norm(data)

            

            if norm_w > 0 and norm_m > 0:

                trust_ratio = norm_w / norm_v

                # 限制trust ratio的范围

                trust_ratio = np.clip(trust_ratio, 0.0, 10.0)

                

                # 应用权重衰减（LAMB使用decoupled weight decay）

                if self.weight_decay > 0:

                    data = data - self.lr * self.gamma * trust_ratio * (

                        m_hat / (v_hat + self.eps) + self.weight_decay * data

                    )

                else:

                    data = data - self.lr * self.gamma * trust_ratio * m_hat / (np.sqrt(v_hat) + self.eps)

            else:

                if self.weight_decay > 0:

                    data = data - self.lr * (m_hat / (np.sqrt(v_hat) + self.eps) 

                                            + self.weight_decay * data)

                else:

                    data = data - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

            

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

        def __init__(self, data):

            self.data = data.astype(np.float64)

            self.grad = np.zeros_like(self.data)

    

    print("=" * 55)

    print("自适应学习率优化器测试")

    print("=" * 55)

    

    # 测试函数：Rosenbrock函数

    def rosenbrock_grad(x, y):

        return np.array([

            -2 * (1 - x) - 400 * x * (y - x**2),

            200 * (y - x**2)

        ])

    

    def rosenbrock(x, y):

        return (1 - x)**2 + 100 * (y - x**2)**2

    

    # AdaGrad测试

    print("\n--- AdaGrad ---")

    p1 = SimpleParam(np.array([0.0, 0.0]))

    opt1 = AdaGrad([p1], lr=0.5)

    

    for epoch in range(1, 5001):

        p1.grad = rosenbrock_grad(p1.data[0], p1.data[1])

        opt1.step()

        opt1.zero_grad()

        if epoch % 1000 == 0:

            loss = rosenbrock(p1.data[0], p1.data[1])

            print(f"Epoch {epoch:5d}: ({p1.data[0]:.4f}, {p1.data[1]:.4f}), loss={loss:.2f}")

    

    # RMSProp测试

    print("\n--- RMSProp ---")

    p2 = SimpleParam(np.array([0.0, 0.0]))

    opt2 = RMSProp([p2], lr=0.01, beta=0.9)

    

    for epoch in range(1, 5001):

        p2.grad = rosenbrock_grad(p2.data[0], p2.data[1])

        opt2.step()

        opt2.zero_grad()

        if epoch % 1000 == 0:

            loss = rosenbrock(p2.data[0], p2.data[1])

            print(f"Epoch {epoch:5d}: ({p2.data[0]:.4f}, {p2.data[1]:.4f}), loss={loss:.2f}")

    

    # LAMB测试

    print("\n--- LAMB ---")

    p3 = SimpleParam(np.array([0.0, 0.0]))

    opt3 = LAMB([p3], lr=0.01, weight_decay=0.0)

    

    for epoch in range(1, 5001):

        p3.grad = rosenbrock_grad(p3.data[0], p3.data[1])

        opt3.step()

        opt3.zero_grad()

        if epoch % 1000 == 0:

            loss = rosenbrock(p3.data[0], p3.data[1])

            print(f"Epoch {epoch:5d}: ({p3.data[0]:.4f}, {p3.data[1]:.4f}), loss={loss:.2f}")

    

    print("\n自适应学习率优化器测试完成！")

