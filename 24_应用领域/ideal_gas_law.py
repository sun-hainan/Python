# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / ideal_gas_law



本文件实现 ideal_gas_law 相关的算法功能。

"""



UNIVERSAL_GAS_CONSTANT = 8.314462  # Unit - J mol-1 K-1







# pressure_of_gas_system 函数实现

def pressure_of_gas_system(moles: float, kelvin: float, volume: float) -> float:

    """

    >>> pressure_of_gas_system(2, 100, 5)

    332.57848

    >>> pressure_of_gas_system(0.5, 273, 0.004)

    283731.01575

    >>> pressure_of_gas_system(3, -0.46, 23.5)

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter positive value.

    """

    if moles < 0 or kelvin < 0 or volume < 0:

    # 条件判断

        raise ValueError("Invalid inputs. Enter positive value.")

    return moles * kelvin * UNIVERSAL_GAS_CONSTANT / volume

    # 返回结果







# volume_of_gas_system 函数实现

def volume_of_gas_system(moles: float, kelvin: float, pressure: float) -> float:

    """

    >>> volume_of_gas_system(2, 100, 5)

    332.57848

    >>> volume_of_gas_system(0.5, 273, 0.004)

    283731.01575

    >>> volume_of_gas_system(3, -0.46, 23.5)

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter positive value.

    """

    if moles < 0 or kelvin < 0 or pressure < 0:

    # 条件判断

        raise ValueError("Invalid inputs. Enter positive value.")

    return moles * kelvin * UNIVERSAL_GAS_CONSTANT / pressure

    # 返回结果







# temperature_of_gas_system 函数实现

def temperature_of_gas_system(moles: float, volume: float, pressure: float) -> float:

    """

    >>> temperature_of_gas_system(2, 100, 5)

    30.068090996146232

    >>> temperature_of_gas_system(11, 5009, 1000)

    54767.66101807144

    >>> temperature_of_gas_system(3, -0.46, 23.5)

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter positive value.

    """

    if moles < 0 or volume < 0 or pressure < 0:

    # 条件判断

        raise ValueError("Invalid inputs. Enter positive value.")



    return pressure * volume / (moles * UNIVERSAL_GAS_CONSTANT)

    # 返回结果







# moles_of_gas_system 函数实现

def moles_of_gas_system(kelvin: float, volume: float, pressure: float) -> float:

    """

    >>> moles_of_gas_system(100, 5, 10)

    0.06013618199229246

    >>> moles_of_gas_system(110, 5009, 1000)

    5476.766101807144

    >>> moles_of_gas_system(3, -0.46, 23.5)

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter positive value.

    """

    if kelvin < 0 or volume < 0 or pressure < 0:

    # 条件判断

        raise ValueError("Invalid inputs. Enter positive value.")



    return pressure * volume / (kelvin * UNIVERSAL_GAS_CONSTANT)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    from doctest import testmod



    testmod()

