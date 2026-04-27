# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / rms_speed_of_molecule



本文件实现 rms_speed_of_molecule 相关的算法功能。

"""



UNIVERSAL_GAS_CONSTANT = 8.3144598







# rms_speed_of_molecule 函数实现

def rms_speed_of_molecule(temperature: float, molar_mass: float) -> float:

    """

    >>> rms_speed_of_molecule(100, 2)

    35.315279554323226

    >>> rms_speed_of_molecule(273, 12)

    23.821458421977443

    """

    if temperature < 0:

    # 条件判断

        raise Exception("Temperature cannot be less than 0 K")

    if molar_mass <= 0:

    # 条件判断

        raise Exception("Molar mass cannot be less than or equal to 0 kg/mol")

    else:

        return (3 * UNIVERSAL_GAS_CONSTANT * temperature / molar_mass) ** 0.5

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    # run doctest

    doctest.testmod()



    # example

    temperature = 300

    molar_mass = 28

    vrms = rms_speed_of_molecule(temperature, molar_mass)

    print(f"Vrms of Nitrogen gas at 300 K is {vrms} m/s")

