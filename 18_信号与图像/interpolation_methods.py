# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / interpolation_methods



本文件实现 interpolation_methods 相关的算法功能。

"""



import numpy as np



def lagrange_interpolation(x, y, x_new):

    n = len(x)

    result = np.zeros_like(x_new)

    for i in range(n):

        L = np.ones_like(x_new)

        for j in range(n):

            if i != j:

                L *= (x_new - x[j])/(x[i]-x[j])

        result += y[i] * L

    return result



def newton_interpolation(x, y, x_new):

    n = len(x)

    div_diff = np.zeros((n,n))

    div_diff[:,0] = y

    for j in range(1,n):

        for i in range(j,n):

            div_diff[i,j] = (div_diff[i,j-1]-div_diff[i-1,j-1])/(x[i]-x[i-j])

    def newton_eval(x_new):

        result = div_diff[0,0]

        term = np.ones_like(x_new)

        for i in range(1,n):

            term *= (x_new - x[i-1])

            result += div_diff[i,i]*term

        return result

    return newton_eval(x_new)



def cubic_spline_interp(x, y):

    n = len(x)-1

    h = np.diff(x)

    alpha = np.zeros(n+1)

    alpha[1:-1] = 3*(y[2:]-2*y[1:-1]+y[:-2])/h[1:]

    l = np.ones(n+1)

    mu = np.zeros(n)

    z = np.zeros(n+1)

    for i in range(1,n):

        l[i] = 2*(x[i+1]-x[i-1]) - h[i-1]*mu[i-1]/l[i-1]

        mu[i] = h[i]/l[i]

        z[i] = (alpha[i]-z[i-1]*h[i-1])/l[i]

    l[n] = 1

    z[n] = 0

    c = np.zeros(n+1)

    c[n] = 0

    for j in range(n-1,-1,-1):

        c[j] = (z[j] - mu[j]*c[j+1])/1.0

    return c



if __name__ == "__main__":

    np.random.seed(42)

    x = np.array([0,1,2,3,4])

    y = x**2 + np.random.randn(5)*0.1

    xn = np.linspace(0,4,20)

    yn = lagrange_interpolation(x,y,xn)

    print(f"Lagrange interp range: [{yn.min():.2f},{yn.max():.2f}]")

    print("\n插值方法测试完成!")

