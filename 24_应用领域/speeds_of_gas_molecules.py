# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / speeds_of_gas_molecules



本文件实现 speeds_of_gas_molecules 相关的算法功能。

"""



# import the constants R and pi from the scipy.constants library

from scipy.constants import R, pi







# avg_speed_of_molecule 函数实现

def avg_speed_of_molecule(temperature: float, molar_mass: float) -> float:

    """

    Takes the temperature (in K) and molar mass (in kg/mol) of a gas

    and returns the average speed of a molecule in the gas (in m/s).



    Examples:



    >>> avg_speed_of_molecule(273, 0.028) # nitrogen at 273 K

    454.3488755062257

    >>> avg_speed_of_molecule(300, 0.032) # oxygen at 300 K

    445.5257273433045

    >>> avg_speed_of_molecule(-273, 0.028) # invalid temperature

    Traceback (most recent call last):

        ...

    Exception: Absolute temperature cannot be less than 0 K

    >>> avg_speed_of_molecule(273, 0) # invalid molar mass

    Traceback (most recent call last):

        ...

    Exception: Molar mass should be greater than 0 kg/mol

    """



    if temperature < 0:

    # 条件判断

        raise Exception("Absolute temperature cannot be less than 0 K")

    if molar_mass <= 0:

    # 条件判断

        raise Exception("Molar mass should be greater than 0 kg/mol")

    return (8 * R * temperature / (pi * molar_mass)) ** 0.5

    # 返回结果







# mps_speed_of_molecule 函数实现

def mps_speed_of_molecule(temperature: float, molar_mass: float) -> float:

    """

    Takes the temperature (in K) and molar mass (in kg/mol) of a gas

    and returns the most probable speed of a molecule in the gas (in m/s).



    Examples:



    >>> mps_speed_of_molecule(273, 0.028) # nitrogen at 273 K

    402.65620702280023

    >>> mps_speed_of_molecule(300, 0.032) # oxygen at 300 K

    394.8368955535605

    >>> mps_speed_of_molecule(-273, 0.028) # invalid temperature

    Traceback (most recent call last):

        ...

    Exception: Absolute temperature cannot be less than 0 K

    >>> mps_speed_of_molecule(273, 0) # invalid molar mass

    Traceback (most recent call last):

        ...

    Exception: Molar mass should be greater than 0 kg/mol

    """



    if temperature < 0:

    # 条件判断

        raise Exception("Absolute temperature cannot be less than 0 K")

    if molar_mass <= 0:

    # 条件判断

        raise Exception("Molar mass should be greater than 0 kg/mol")

    return (2 * R * temperature / molar_mass) ** 0.5

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

