# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / grahams_law

本文件实现 grahams_law 相关的算法功能。
"""

from math import pow, sqrt  # noqa: A004


def validate(*values: float) -> bool:
    """
    验证输入参数的有效性

    参数:
        values: 可变数量的浮点数（扩散速率或摩尔质量）

    返回:
        bool: 所有值都大于0时返回 True，否则返回 False

    示例:
        >>> validate(2.016, 4.002)
        True
        >>> validate(-2.016, 4.002)
        False
        >>> validate()
        False
    """
    result = len(values) > 0 and all(value > 0.0 for value in values)
    return result


def effusion_ratio(molar_mass_1: float, molar_mass_2: float) -> float | ValueError:
    """
    计算两种气体的扩散速率比

    参数:
        molar_mass_1: 第一种气体的摩尔质量（g/mol）
        molar_mass_2: 第二种气体的摩尔质量（g/mol）

    返回:
        float: 扩散速率比 r₁/r₂
        ValueError: 当摩尔质量 <= 0 时抛出

    示例:
        >>> effusion_ratio(2.016, 4.002)
        1.408943
        >>> effusion_ratio(-2.016, 4.002)  # doctest: +ELLIPSIS
        ValueError(...)
    """
    return (
        round(sqrt(molar_mass_2 / molar_mass_1), 6)
        if validate(molar_mass_1, molar_mass_2)
        else ValueError("Input Error: Molar mass values must greater than 0.")
    )


def first_effusion_rate(
    effusion_rate: float, molar_mass_1: float, molar_mass_2: float
) -> float | ValueError:
    """
    已知第二种气体的扩散速率，求第一种气体的扩散速率

    参数:
        effusion_rate: 第二种气体的扩散速率（任意单位）
        molar_mass_1: 第一种气体的摩尔质量（g/mol）
        molar_mass_2: 第二种气体的摩尔质量（g/mol）

    返回:
        float: 第一种气体的扩散速率

    示例:
        >>> first_effusion_rate(1, 2.016, 4.002)
        1.408943
    """
    return (
        round(effusion_rate * sqrt(molar_mass_2 / molar_mass_1), 6)
        if validate(effusion_rate, molar_mass_1, molar_mass_2)
        else ValueError(
            "Input Error: Molar mass and effusion rate values must greater than 0."
        )
    )


def second_effusion_rate(
    effusion_rate: float, molar_mass_1: float, molar_mass_2: float
) -> float | ValueError:
    """
    已知第一种气体的扩散速率，求第二种气体的扩散速率

    参数:
        effusion_rate: 第一种气体的扩散速率（任意单位）
        molar_mass_1: 第一种气体的摩尔质量（g/mol）
        molar_mass_2: 第二种气体的摩尔质量（g/mol）

    返回:
        float: 第二种气体的扩散速率

    示例:
        >>> second_effusion_rate(1, 2.016, 4.002)
        0.709752
    """
    return (
        round(effusion_rate / sqrt(molar_mass_2 / molar_mass_1), 6)
        if validate(effusion_rate, molar_mass_1, molar_mass_2)
        else ValueError(
            "Input Error: Molar mass and effusion rate values must greater than 0."
        )
    )


def first_molar_mass(
    molar_mass: float, effusion_rate_1: float, effusion_rate_2: float
) -> float | ValueError:
    """
    已知第二种气体的摩尔质量和两种气体的扩散速率，求第一种气体的摩尔质量

    参数:
        molar_mass: 第二种气体的摩尔质量（g/mol）
        effusion_rate_1: 第一种气体的扩散速率
        effusion_rate_2: 第二种气体的扩散速率

    返回:
        float: 第一种气体的摩尔质量

    示例:
        >>> first_molar_mass(2, 1.408943, 0.709752)
        0.507524
    """
    return (
        round(molar_mass / pow(effusion_rate_1 / effusion_rate_2, 2), 6)
        if validate(molar_mass, effusion_rate_1, effusion_rate_2)
        else ValueError(
            "Input Error: Molar mass and effusion rate values must greater than 0."
        )
    )


def second_molar_mass(
    molar_mass: float, effusion_rate_1: float, effusion_rate_2: float
) -> float | ValueError:
    """
    已知第一种气体的摩尔质量和两种气体的扩散速率，求第二种气体的摩尔质量

    参数:
        molar_mass: 第一种气体的摩尔质量（g/mol）
        effusion_rate_1: 第一种气体的扩散速率
        effusion_rate_2: 第二种气体的扩散速率

    返回:
        float: 第二种气体的摩尔质量

    示例:
        >>> second_molar_mass(2, 1.408943, 0.709752)
        1.970351
    """
    return (
        round(pow(effusion_rate_1 / effusion_rate_2, 2) / molar_mass, 6)
        if validate(molar_mass, effusion_rate_1, effusion_rate_2)
        else ValueError(
            "Input Error: Molar mass and effusion rate values must greater than 0."
        )
    )


if __name__ == "__main__":
    print("=== Graham 气体扩散定律 ===\n")

    # 测试：氦气（He, MW=4）和甲烷（CH4, MW=16）
    molar_mass_he = 4.002
    molar_mass_ch4 = 16.04

    ratio = effusion_ratio(molar_mass_he, molar_mass_ch4)
    print(f"He vs CH4 扩散速率比: {ratio:.6f}")
    print(f"解释: He 的摩尔质量是 CH4 的 {molar_mass_he/molar_mass_ch4:.4f} 倍")
    print(f"      He 扩散速率应该是 CH4 的 √(16.04/4.002) = {ratio:.4f} 倍\n")

    # 测试：氦气 vs 氢气（H2, MW=2.016）
    molar_mass_h2 = 2.016
    ratio_h2_he = effusion_ratio(molar_mass_h2, molar_mass_he)
    print(f"H2 vs He 扩散速率比: {ratio_h2_he:.6f}")
    print(f"解释: H2 比 He 更轻，扩散更快")

    print("\n=== 公式验证 ===")
    print("r₁/r₂ = √(m₂/m₁)")
    print(f"√({molar_mass_ch4}/{molar_mass_he}) = √{molar_mass_ch4/molar_mass_he:.4f} = {ratio:.4f}")
