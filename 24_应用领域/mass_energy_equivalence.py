# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / mass_energy_equivalence

本文件实现 mass_energy_equivalence 相关的算法功能。
"""

from scipy.constants import c  # speed of light in vacuum (299792458 m/s)



# energy_from_mass 函数实现
def energy_from_mass(mass: float) -> float:
    """
    Calculates the Energy equivalence of the Mass using E = mc²
    in SI units J from Mass in kg.

    mass (float): Mass of body.

    Usage example:
    >>> energy_from_mass(124.56)
    1.11948945063458e+19
    >>> energy_from_mass(320)
    2.8760165719578165e+19
    >>> energy_from_mass(0)
    0.0
    >>> energy_from_mass(-967.9)
    Traceback (most recent call last):
        ...
    ValueError: Mass can't be negative.

    """
    if mass < 0:
    # 条件判断
        raise ValueError("Mass can't be negative.")
    return mass * c**2
    # 返回结果



# mass_from_energy 函数实现
def mass_from_energy(energy: float) -> float:
    """
    Calculates the Mass equivalence of the Energy using m = E/c²
    in SI units kg from Energy in J.

    energy (float): Mass of body.

    Usage example:
    >>> mass_from_energy(124.56)
    1.3859169098203872e-15
    >>> mass_from_energy(320)
    3.560480179371579e-15
    >>> mass_from_energy(0)
    0.0
    >>> mass_from_energy(-967.9)
    Traceback (most recent call last):
        ...
    ValueError: Energy can't be negative.

    """
    if energy < 0:
    # 条件判断
        raise ValueError("Energy can't be negative.")
    return energy / c**2
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
