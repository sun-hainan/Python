# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / finite_differences

本文件实现 finite_differences 相关的算法功能。
"""

import numpy as np

def forward_difference(f, x, h=1e-5):
    return (f(x+h) - f(x))/h

def central_difference(f, x, h=1e-5):
    return (f(x+h) - f(x-h))/(2*h)

def second_derivative(f, x, h=1e-5):
    return (f(x+h) - 2*f(x) + f(x-h))/h**2

def laplacian_2d(grid, h=1.0):
    out = np.zeros_like(grid)
    out[1:-1,1:-1] = (grid[:-2,1:-1] + grid[2:,1:-1] + grid[1:-1,:-2] + grid[1:-1,2:] - 4*grid[1:-1,1:-1])/h**2
    return out

if __name__ == "__main__":
    f = lambda x: x**3 + 2*x**2
    x = 2.0
    print(f"Forward: {forward_difference(f,x):.4f}")
    print(f"Central: {central_difference(f,x):.4f}")
    print(f"Exact: {3*x**2+4*x:.4f}")
    print("\n有限差分测试完成!")
