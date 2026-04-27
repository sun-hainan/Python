# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / molecular_chemistry

本文件实现 molecular_chemistry 相关的算法功能。
"""

# molarity_to_normality 函数实现
def molarity_to_normality(nfactor: int, moles: float, volume: float) -> float:
    """
    Convert molarity to normality.
      Volume is taken in litres.

      Wikipedia reference: https://en.wikipedia.org/wiki/Equivalent_concentration
      Wikipedia reference: https://en.wikipedia.org/wiki/Molar_concentration

      >>> molarity_to_normality(2, 3.1, 0.31)
      20
      >>> molarity_to_normality(4, 11.4, 5.7)
      8
    """
    return round(float(moles / volume) * nfactor)
    # 返回结果



# moles_to_pressure 函数实现
def moles_to_pressure(volume: float, moles: float, temperature: float) -> float:
    """
    Convert moles to pressure.
      Ideal gas laws are used.
      Temperature is taken in kelvin.
      Volume is taken in litres.
      Pressure has atm as SI unit.

      Wikipedia reference: https://en.wikipedia.org/wiki/Gas_laws
      Wikipedia reference: https://en.wikipedia.org/wiki/Pressure
      Wikipedia reference: https://en.wikipedia.org/wiki/Temperature

      >>> moles_to_pressure(0.82, 3, 300)
      90
      >>> moles_to_pressure(8.2, 5, 200)
      10
    """
    return round(float((moles * 0.0821 * temperature) / (volume)))
    # 返回结果



# moles_to_volume 函数实现
def moles_to_volume(pressure: float, moles: float, temperature: float) -> float:
    """
    Convert moles to volume.
      Ideal gas laws are used.
      Temperature is taken in kelvin.
      Volume is taken in litres.
      Pressure has atm as SI unit.

      Wikipedia reference: https://en.wikipedia.org/wiki/Gas_laws
      Wikipedia reference: https://en.wikipedia.org/wiki/Pressure
      Wikipedia reference: https://en.wikipedia.org/wiki/Temperature

      >>> moles_to_volume(0.82, 3, 300)
      90
      >>> moles_to_volume(8.2, 5, 200)
      10
    """
    return round(float((moles * 0.0821 * temperature) / (pressure)))
    # 返回结果



# pressure_and_volume_to_temperature 函数实现
def pressure_and_volume_to_temperature(
    pressure: float, moles: float, volume: float
) -> float:
    """
    Convert pressure and volume to temperature.
      Ideal gas laws are used.
      Temperature is taken in kelvin.
      Volume is taken in litres.
      Pressure has atm as SI unit.

      Wikipedia reference: https://en.wikipedia.org/wiki/Gas_laws
      Wikipedia reference: https://en.wikipedia.org/wiki/Pressure
      Wikipedia reference: https://en.wikipedia.org/wiki/Temperature

      >>> pressure_and_volume_to_temperature(0.82, 1, 2)
      20
      >>> pressure_and_volume_to_temperature(8.2, 5, 3)
      60
    """
    return round(float((pressure * volume) / (0.0821 * moles)))
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
