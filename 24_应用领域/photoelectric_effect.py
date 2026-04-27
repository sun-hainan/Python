# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / photoelectric_effect

本文件实现 photoelectric_effect 相关的算法功能。
"""

PLANCK_CONSTANT_JS = 6.6261 * pow(10, -34)  # in SI (Js)
PLANCK_CONSTANT_EVS = 4.1357 * pow(10, -15)  # in eVs



# maximum_kinetic_energy 函数实现
def maximum_kinetic_energy(
    frequency: float, work_function: float, in_ev: bool = False
) -> float:
    """
    Calculates the maximum kinetic energy of emitted electron from the surface.
    if the maximum kinetic energy is zero then no electron will be emitted
    or given electromagnetic wave frequency is small.

    frequency (float): Frequency of electromagnetic wave.
    work_function (float): Work function of the surface.
    in_ev (optional)(bool): Pass True if values are in eV.

    Usage example:
    >>> maximum_kinetic_energy(1000000,2)
    0
    >>> maximum_kinetic_energy(1000000,2,True)
    0
    >>> maximum_kinetic_energy(10000000000000000,2,True)
    39.357000000000006
    >>> maximum_kinetic_energy(-9,20)
    Traceback (most recent call last):
        ...
    ValueError: Frequency can't be negative.

    >>> maximum_kinetic_energy(1000,"a")
    Traceback (most recent call last):
        ...
    TypeError: unsupported operand type(s) for -: 'float' and 'str'

    """
    if frequency < 0:
    # 条件判断
        raise ValueError("Frequency can't be negative.")
    if in_ev:
    # 条件判断
        return max(PLANCK_CONSTANT_EVS * frequency - work_function, 0)
    # 返回结果
    return max(PLANCK_CONSTANT_JS * frequency - work_function, 0)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
