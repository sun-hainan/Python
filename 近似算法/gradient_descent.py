# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / gradient_descent



本文件实现 gradient_descent 相关的算法功能。

"""



import random





def gradient_descent(gradient_fn, x0: float, learning_rate: float = 0.1,

                    max_iter: int = 100, tol: float = 1e-6) -> tuple:

    """

    梯度下降



    参数：

        gradient_fn: 梯度函数 f'(x)

        x0: 初始点

        learning_rate: 学习率

        max_iter: 最大迭代次数

        tol: 收敛容忍度



    返回：(最优解, 迭代次数)

    """

    x = x0

    history = [x]



    for i in range(max_iter):

        grad = gradient_fn(x)

        x_new = x - learning_rate * grad



        if abs(x_new - x) < tol:

            break



        x = x_new

        history.append(x)



    return x, len(history)





def stochastic_gradient_descent(gradients_fn, x0: float, data: list,

                               learning_rate: float = 0.1,

                               max_epochs: int = 100) -> tuple:

    """

    随机梯度下降



    参数：

        gradients_fn: 随机梯度函数 (x, sample) -> gradient

        x0: 初始点

        data: 数据样本

        learning_rate: 学习率（通常随时间衰减）

        max_epochs: 最大轮数

    """

    x = x0



    for epoch in range(max_epochs):

        # 打乱数据

        random.shuffle(data)

        lr = learning_rate / (1 + epoch)  # 衰减



        for sample in data:

            grad = gradients_fn(x, sample)

            x = x - lr * grad



    return x





def newton_method(objective_fn, gradient_fn, hessian_fn, x0: float,

                  max_iter: int = 50) -> tuple:

    """

    牛顿法（二阶优化）



    收敛更快，但需要Hessian矩阵

    """

    x = x0



    for _ in range(max_iter):

        g = gradient_fn(x)

        H = hessian_fn(x)



        # 求解 H * d = -g

        # 简化：假设H可逆

        if abs(H) < 1e-10:

            break



        d = -g / H

        x = x + d



    return x





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 梯度下降测试 ===\n")



    # 例：最小化 f(x) = (x-3)^2 + 1

    # f'(x) = 2(x-3)

    def grad(x):

        return 2 * (x - 3)



    x0 = 0.0

    lr = 0.1



    result, n_iter = gradient_descent(grad, x0, learning_rate=lr)



    print(f"函数: f(x) = (x-3)^2 + 1")

    print(f"初始点: x0 = {x0}")

    print(f"学习率: {lr}")

    print(f"最优解: x* = {result:.6f}")

    print(f"迭代次数: {n_iter}")

    print(f"最优值: f(x*) = {(result-3)**2 + 1:.6f}")



    print("\n--- SGD演示 ---")

    # SGD优化线性回归

    # 目标: min ||Ax - b||^2



    import numpy as np



    np.random.seed(42)

    A = np.random.randn(100, 5)

    b = np.random.randn(100)



    def sgd_grad(x, sample):

        i = sample

        residual = A[i] @ x - b[i]

        return 2 * residual * A[i]



    x0 = np.zeros(5)

    result = stochastic_gradient_descent(sgd_grad, x0, list(range(100)),

                                       learning_rate=0.01, max_epochs=50)



    print(f"线性回归 SGD 结果: {result[:3]}...")



    print("\n说明：")

    print("  - GD是机器学习最基础的优化算法")

    print("  - Adam、RMSProp等是GD的变体")

    print("  - 收敛速度取决于学习率和函数形态")

