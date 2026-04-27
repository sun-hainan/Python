# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / optimization



本文件实现 optimization 相关的算法功能。

"""



import numpy as np



def gradient_descent(f, grad_f, x0, lr=0.01, max_iter=100, tol=1e-6):

    x = x0.copy()

    for _ in range(max_iter):

        g = grad_f(x)

        x_new = x - lr * g

        if np.linalg.norm(x_new - x) < tol:

            break

        x = x_new

    return x



def newton_method(f, grad_f, hess_f, x0, lr=0.1, max_iter=50):

    x = x0.copy()

    for _ in range(max_iter):

        H = hess_f(x)

        g = grad_f(x)

        try:

            delta = np.linalg.solve(H, g)

        except:

            delta = np.linalg.lstsq(H, g, rcond=None)[0]

        x = x - lr * delta

    return x



def coordinate_descent(f, x0, max_iter=100):

    x = x0.copy()

    n = len(x)

    for _ in range(max_iter):

        for i in range(n):

            def fi(a): return f(x)[i]

            x[i] = min(x[i] - 0.01 * grad_f(x)[i], x[i])

    return x



if __name__ == "__main__":

    np.random.seed(42)

    A = np.random.randn(5,5)

    A = A.T @ A + np.eye(5)

    b = np.random.randn(5)

    f = lambda x: 0.5 * x @ A @ x - b @ x

    grad_f = lambda x: A @ x - b

    x_min = gradient_descent(f, grad_f, np.zeros(5))

    print(f"Optimized: {x_min.round(3)}")

    print("\n优化算法测试完成!")

