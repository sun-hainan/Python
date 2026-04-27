# -*- coding: utf-8 -*-

"""

算法实现：25_深度学习核心算法 / optimizer_all_compare



本文件实现 optimizer_all_compare 相关的算法功能。

"""



import numpy as np





def sigmoid(x):

    """Sigmoid函数"""

    x = np.clip(x, -500, 500)

    return 1 / (1 + np.exp(-x))





class SimpleParam:

    """简单参数容器"""

    def __init__(self, data):

        self.data = data.astype(np.float64)

        self.grad = np.zeros_like(self.data)





class Optimizer:

    """优化器基类"""

    def __init__(self, params, lr=0.01):

        self.params = params

        self.lr = lr

    

    def step(self):

        raise NotImplementedError

    

    def zero_grad(self):

        for p in self.params:

            p.grad = np.zeros_like(p.grad)





class SGD(Optimizer):

    """随机梯度下降"""

    def __init__(self, params, lr=0.01, momentum=0.0, nesterov=False):

        super().__init__(params, lr)

        self.momentum = momentum

        self.nesterov = nesterov

        self.velocity = [np.zeros_like(p.data) for p in params]

    

    def step(self):

        for i, p in enumerate(self.params):

            if self.momentum > 0:

                self.velocity[i] = self.momentum * self.velocity[i] + p.grad

                if self.nesterov:

                    grad = p.grad + self.momentum * self.velocity[i]

                else:

                    grad = self.velocity[i]

            else:

                grad = p.grad

            p.data -= self.lr * grad





class AdaGrad(Optimizer):

    """AdaGrad优化器"""

    def __init__(self, params, lr=0.01, eps=1e-8):

        super().__init__(params, lr)

        self.eps = eps

        self.accumulated = [np.zeros_like(p.data) for p in params]

    

    def step(self):

        for i, p in enumerate(self.params):

            self.accumulated[i] += p.grad ** 2

            adaptive_lr = self.lr / (np.sqrt(self.accumulated[i]) + self.eps)

            p.data -= adaptive_lr * p.grad





class RMSProp(Optimizer):

    """RMSProp优化器"""

    def __init__(self, params, lr=0.01, beta=0.9, eps=1e-8):

        super().__init__(params, lr)

        self.beta = beta

        self.eps = eps

        self.ewma = [np.zeros_like(p.data) for p in params]

    

    def step(self):

        for i, p in enumerate(self.params):

            self.ewma[i] = self.beta * self.ewma[i] + (1 - self.beta) * p.grad ** 2

            p.data -= self.lr * p.grad / (np.sqrt(self.ewma[i]) + self.eps)





class Adam(Optimizer):

    """Adam优化器"""

    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):

        super().__init__(params, lr)

        self.beta1 = beta1

        self.beta2 = beta2

        self.eps = eps

        self.m = [np.zeros_like(p.data) for p in params]

        self.v = [np.zeros_like(p.data) for p in params]

        self.t = 0

    

    def step(self):

        self.t += 1

        for i, p in enumerate(self.params):

            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * p.grad

            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * p.grad ** 2

            

            m_hat = self.m[i] / (1 - self.beta1 ** self.t)

            v_hat = self.v[i] / (1 - self.beta2 ** self.t)

            

            p.data -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)





class AdamW(Optimizer):

    """AdamW优化器"""

    def __init__(self, params, lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01):

        super().__init__(params, lr)

        self.beta1, self.beta2 = betas

        self.eps = eps

        self.weight_decay = weight_decay

        self.m = [np.zeros_like(p.data) for p in params]

        self.v = [np.zeros_like(p.data) for p in params]

        self.t = 0

    

    def step(self):

        self.t += 1

        for i, p in enumerate(self.params):

            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * p.grad

            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * p.grad ** 2

            

            m_hat = self.m[i] / (1 - self.beta1 ** self.t)

            v_hat = self.v[i] / (1 - self.beta2 ** self.t)

            

            p.data = p.data - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

            p.data = p.data - self.lr * self.weight_decay * p.data





class LAMB(Optimizer):

    """LAMB优化器"""

    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-6, weight_decay=0.01):

        super().__init__(params, lr)

        self.beta1 = beta1

        self.beta2 = beta2

        self.eps = eps

        self.weight_decay = weight_decay

        self.m = [np.zeros_like(p.data) for p in params]

        self.v = [np.zeros_like(p.data) for p in params]

        self.t = 0

    

    def step(self):

        self.t += 1

        for i, p in enumerate(self.params):

            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * p.grad

            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * p.grad ** 2

            

            m_hat = self.m[i] / (1 - self.beta1 ** self.t)

            v_hat = self.v[i] / (1 - self.beta2 ** self.t)

            

            norm_w = np.linalg.norm(p.data)

            norm_v = np.linalg.norm(np.sqrt(v_hat) + self.eps)

            

            if norm_w > 0 and norm_v > 0:

                trust_ratio = norm_w / norm_v

                trust_ratio = np.clip(trust_ratio, 0.0, 10.0)

            else:

                trust_ratio = 1.0

            

            p.data = p.data - self.lr * trust_ratio * m_hat / (np.sqrt(v_hat) + self.eps)

            if self.weight_decay > 0:

                p.data = p.data - self.lr * self.weight_decay * p.data





# ============================

# 测试代码

# ============================



if __name__ == "__main__":

    np.random.seed(42)

    

    print("=" * 65)

    print("优化器全面对比测试")

    print("=" * 65)

    

    # 测试函数：Rosenbrock

    def rosenbrock(x, y):

        return (1 - x)**2 + 100 * (y - x**2)**2

    

    def rosenbrock_grad(x, y):

        return np.array([

            -2 * (1 - x) - 400 * x * (y - x**2),

            200 * (y - x**2)

        ])

    

    optimizers = {

        'SGD(lr=0.001)': lambda params: SGD(params, lr=0.001),

        'SGD+Momentum(lr=0.001)': lambda params: SGD(params, lr=0.001, momentum=0.9),

        'Nesterov(lr=0.001)': lambda params: SGD(params, lr=0.001, momentum=0.9, nesterov=True),

        'AdaGrad(lr=0.5)': lambda params: AdaGrad(params, lr=0.5),

        'RMSProp(lr=0.01)': lambda params: RMSProp(params, lr=0.01, beta=0.9),

        'Adam(lr=0.001)': lambda params: Adam(params, lr=0.001),

        'AdamW(lr=0.001, wd=0.01)': lambda params: AdamW(params, lr=0.001, weight_decay=0.01),

        'LAMB(lr=0.001)': lambda params: LAMB(params, lr=0.001),

    }

    

    num_epochs = 2000

    

    for name, opt_fn in optimizers.items():

        np.random.seed(42)

        p = SimpleParam(np.array([0.0, 0.0]))

        opt = opt_fn([p])

        

        losses = []

        for epoch in range(num_epochs):

            p.grad = rosenbrock_grad(p.data[0], p.data[1])

            opt.step()

            opt.zero_grad()

            

            loss = rosenbrock(p.data[0], p.data[1])

            losses.append(loss)

        

        final_loss = losses[-1]

        final_pos = p.data.copy()

        

        print(f"\n{name}:")

        print(f"  最终位置: ({final_pos[0]:.6f}, {final_pos[1]:.6f})")

        print(f"  最终损失: {final_loss:.6f}")

        print(f"  收敛速度(前500步损失): {losses[499]:.2f}")

    

    print("\n" + "=" * 65)

    print("优化器对比测试完成！")

    print("=" * 65)

