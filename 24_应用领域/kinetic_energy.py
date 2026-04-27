# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / kinetic_energy

本文件实现 kinetic_energy 相关的算法功能。
"""

# kinetic_energy 函数实现
def kinetic_energy(mass: float, velocity: float) -> float:
    """
    Calculate kinetic energy.

    The kinetic energy of a non-rotating object of mass m traveling at a speed v is ½mv²

    >>> kinetic_energy(10,10)
    500.0
    >>> kinetic_energy(0,10)
    0.0
    >>> kinetic_energy(10,0)
    0.0
    >>> kinetic_energy(20,-20)
    4000.0
    >>> kinetic_energy(0,0)
    0.0
    >>> kinetic_energy(2,2)
    4.0
    >>> kinetic_energy(100,100)
    500000.0
    """
    if mass < 0:
    # 条件判断
        raise ValueError("The mass of a body cannot be negative")
    return 0.5 * mass * abs(velocity) * abs(velocity)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod(verbose=True)
