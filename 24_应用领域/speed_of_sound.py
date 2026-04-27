# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / speed_of_sound

本文件实现 speed_of_sound 相关的算法功能。
"""

# speed_of_sound_in_a_fluid 函数实现
def speed_of_sound_in_a_fluid(density: float, bulk_modulus: float) -> float:
    """
    Calculates the speed of sound in a fluid from its density and bulk modulus

    Examples:
    Example 1 --> Water 20°C: bulk_modulus= 2.15MPa, density=998kg/m³
    Example 2 --> Mercury 20°C: bulk_modulus= 28.5MPa, density=13600kg/m³

    >>> speed_of_sound_in_a_fluid(bulk_modulus=2.15e9, density=998)
    1467.7563207952705
    >>> speed_of_sound_in_a_fluid(bulk_modulus=28.5e9, density=13600)
    1447.614670861731
    """

    if density <= 0:
    # 条件判断
        raise ValueError("Impossible fluid density")
    if bulk_modulus <= 0:
    # 条件判断
        raise ValueError("Impossible bulk modulus")

    return (bulk_modulus / density) ** 0.5
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
