# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / polynomial_roots



本文件实现 polynomial_roots 相关的算法功能。

"""



import numpy as np



def DurandKerner(coeffs):

    n = len(coeffs)-1

    roots = np.random.randn(n) + 1j*np.random.randn(n)

    for _ in range(100):

        for i in range(n):

            f = 0

            for j, c in enumerate(coeffs):

                f += c * roots[i]**(n-1-j)

            if abs(f) < 1e-10: continue

            prod = 1

            for j in range(n):

                if j != i:

                    prod *= roots[i] - roots[j]

            if abs(prod) < 1e-30: roots[i] = np.random.rand() + 1j*np.random.rand()

            else: roots[i] -= f/prod

    return roots



def companion_matrix(coeffs):

    n = len(coeffs)-1

    A = np.zeros((n,n))

    A[1:,:n-1] = np.eye(n-1)

    A[0] = -coeffs[1:]/coeffs[0]

    return A



def bairstow_method(a, b, tol=1e-10, max_iter=50):

    n = len(a)

    for _ in range(max_iter):

        r, s = a[-2], a[-1]

        for _ in range(max_iter):

            det = r**2 + s

            if abs(det) < 1e-15: break

            u = (-a[-2] + s)/det

            v = (-a[-1])/det

            a[-2] += r*u + s*v

            a[-1] += r*u

            if abs(a[-1]) < tol: break

    return a[-2], a[-1]



if __name__ == "__main__":

    c = np.poly([1, 2, -3, 0, 4])

    roots = DurandKerner(c)

    print(f"Roots: {roots.round(3)}")

    print("\n多项式根测试完成!")

