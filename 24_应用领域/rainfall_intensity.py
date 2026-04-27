# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / rainfall_intensity

本文件实现 rainfall_intensity 相关的算法功能。
"""

# rainfall_intensity 函数实现
def rainfall_intensity(
    coefficient_k: float,
    coefficient_a: float,
    coefficient_b: float,
    coefficient_c: float,
    return_period: float,
    duration: float,
) -> float:
    """
    Calculate the intensity of a rainfall event for a given duration and return period.
    It's based on the Sherman intensity-duration-frequency curve:

    I = k * T^a / (D + b)^c

    where:
        I = Intensity of the rainfall event [mm/h]
        k, a, b, c = Coefficients obtained through statistical distribution adjust
        T = Return period in years
        D = Rainfall event duration in minutes

    Parameters
    ----------
    coefficient_k : float
        Coefficient obtained through statistical distribution adjust.
    coefficient_a : float
        Coefficient obtained through statistical distribution adjust.
    coefficient_b : float
        Coefficient obtained through statistical distribution adjust.
    coefficient_c : float
        Coefficient obtained through statistical distribution adjust.
    return_period : float
        Return period in years.
    duration : float
        Rainfall event duration in minutes.

    Returns
    -------
    intensity : float
        Intensity of the rainfall event in mm/h.

    Raises
    ------
    ValueError
        If any of the parameters are not positive.

    Examples
    --------

    >>> rainfall_intensity(1000, 0.2, 11.6, 0.81, 10, 60)
    49.83339231138578

    >>> rainfall_intensity(1000, 0.2, 11.6, 0.81, 10, 30)
    77.36319588106228

    >>> rainfall_intensity(1000, 0.2, 11.6, 0.81, 5, 60)
    43.382487747633625

    >>> rainfall_intensity(0, 0.2, 11.6, 0.81, 10, 60)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    >>> rainfall_intensity(1000, -0.2, 11.6, 0.81, 10, 60)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    >>> rainfall_intensity(1000, 0.2, -11.6, 0.81, 10, 60)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    >>> rainfall_intensity(1000, 0.2, 11.6, -0.81, 10, 60)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    >>> rainfall_intensity(1000, 0, 11.6, 0.81, 10, 60)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    >>> rainfall_intensity(1000, 0.2, 0, 0.81, 10, 60)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    >>> rainfall_intensity(1000, 0.2, 11.6, 0, 10, 60)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    >>> rainfall_intensity(0, 0.2, 11.6, 0.81, 10, 60)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    >>> rainfall_intensity(1000, 0.2, 11.6, 0.81, 0, 60)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    >>> rainfall_intensity(1000, 0.2, 11.6, 0.81, 10, 0)
    Traceback (most recent call last):
    ...
    ValueError: All parameters must be positive.

    """
    if (
        coefficient_k <= 0
        or coefficient_a <= 0
        or coefficient_b <= 0
        or coefficient_c <= 0
        or return_period <= 0
        or duration <= 0
    ):
        raise ValueError("All parameters must be positive.")
    intensity = (coefficient_k * (return_period**coefficient_a)) / (
        (duration + coefficient_b) ** coefficient_c
    )
    return intensity
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
