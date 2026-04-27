# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / polynomial_fitting



本文件实现 polynomial_fitting 相关的算法功能。

"""



import numpy as np



# polyfit_robust 算法

def polyfit_robust(x, y, degree=2, outlier_threshold=3.0):

    """带异常值剔除的多项式拟合"""

    for _ in range(5):

        coeffs = np.polyfit(x, y, degree)

        residuals = y - np.polyval(coeffs, x)

        std = np.std(residuals)

        mask = np.abs(residuals) < outlier_threshold * std

        if np.sum(~mask) == 0:

            break

        x, y = x[mask], y[mask]

    return np.polyfit(x, y, degree)



# legendre_polynomials 算法

def legendre_polynomials(x, degree=5):

    P = [np.ones_like(x), x.copy()]

    for n in range(2, degree):

        P.append(((2*n-1)*x*P[-1] - (n-1)*P[-2]) / n)

    return P



# chebyshev_fit 算法

def chebyshev_fit(x, degree=5):

    t = 2*x/(x.max()-x.min()) - 1

    return np.polynomial.chebyshev.chebfit(t, t, degree)



if __name__ == "__main__":

    np.random.seed(42)

    x = np.linspace(-3,3,50)

    y = x**2 + 0.5*x + np.random.randn(50)*0.5

    coeffs = polyfit_robust(x, y, 2)

    print(f"Fitted coeffs: {coeffs.round(3)}")

    print("\n多项式拟合测试完成!")

