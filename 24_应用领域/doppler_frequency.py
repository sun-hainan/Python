# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / doppler_frequency



本文件实现 doppler_frequency 相关的算法功能。

"""



# doppler_effect 函数实现

def doppler_effect(

    org_freq: float, wave_vel: float, obs_vel: float, src_vel: float

) -> float:

    """

    Input Parameters:

    -----------------

    org_freq: frequency of the wave when the source is stationary

    wave_vel: velocity of the wave in the medium

    obs_vel: velocity of the observer, +ve if the observer is moving towards the source

    src_vel: velocity of the source, +ve if the source is moving towards the observer



    Returns:

    --------

    f: frequency of the wave as perceived by the observer



    Docstring Tests:

    >>> doppler_effect(100, 330, 10, 0)  # observer moving towards the source

    103.03030303030303

    >>> doppler_effect(100, 330, -10, 0)  # observer moving away from the source

    96.96969696969697

    >>> doppler_effect(100, 330, 0, 10)  # source moving towards the observer

    103.125

    >>> doppler_effect(100, 330, 0, -10)  # source moving away from the observer

    97.05882352941177

    >>> doppler_effect(100, 330, 10, 10)  # source & observer moving towards each other

    106.25

    >>> doppler_effect(100, 330, -10, -10)  # source and observer moving away

    94.11764705882354

    >>> doppler_effect(100, 330, 10, 330)  # source moving at same speed as the wave

    Traceback (most recent call last):

        ...

    ZeroDivisionError: Division by zero implies vs=v and observer in front of the source

    >>> doppler_effect(100, 330, 10, 340)  # source moving faster than the wave

    Traceback (most recent call last):

        ...

    ValueError: Non-positive frequency implies vs>v or v0>v (in the opposite direction)

    >>> doppler_effect(100, 330, -340, 10)  # observer moving faster than the wave

    Traceback (most recent call last):

        ...

    ValueError: Non-positive frequency implies vs>v or v0>v (in the opposite direction)

    """



    if wave_vel == src_vel:

    # 条件判断

        raise ZeroDivisionError(

            "Division by zero implies vs=v and observer in front of the source"

        )

    doppler_freq = (org_freq * (wave_vel + obs_vel)) / (wave_vel - src_vel)

    if doppler_freq <= 0:

    # 条件判断

        raise ValueError(

            "Non-positive frequency implies vs>v or v0>v (in the opposite direction)"

        )

    return doppler_freq

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

