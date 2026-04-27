# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / hubble_parameter

本文件实现 hubble_parameter 相关的算法功能。
"""

# hubble_parameter 函数实现
def hubble_parameter(
    hubble_constant: float,
    radiation_density: float,
    matter_density: float,
    dark_energy: float,
    redshift: float,
) -> float:
    """
    Input Parameters
    ----------------
    hubble_constant: Hubble constante is the expansion rate today usually
    given in km/(s*Mpc)

    radiation_density: relative radiation density today

    matter_density: relative mass density today

    dark_energy: relative dark energy density today

    redshift: the light redshift

    Returns
    -------
    result : Hubble parameter in and the unit km/s/Mpc (the unit can be
    changed if you want, just need to change the unit of the Hubble constant)

    >>> hubble_parameter(hubble_constant=68.3, radiation_density=1e-4,
    ... matter_density=-0.3, dark_energy=0.7, redshift=1)
    Traceback (most recent call last):
    ...
    ValueError: All input parameters must be positive

    >>> hubble_parameter(hubble_constant=68.3, radiation_density=1e-4,
    ... matter_density= 1.2, dark_energy=0.7, redshift=1)
    Traceback (most recent call last):
    ...
    ValueError: Relative densities cannot be greater than one

    >>> hubble_parameter(hubble_constant=68.3, radiation_density=1e-4,
    ... matter_density= 0.3, dark_energy=0.7, redshift=0)
    68.3
    """
    parameters = [redshift, radiation_density, matter_density, dark_energy]
    if any(p < 0 for p in parameters):
    # 条件判断
        raise ValueError("All input parameters must be positive")

    if any(p > 1 for p in parameters[1:4]):
    # 条件判断
        raise ValueError("Relative densities cannot be greater than one")
    else:
        curvature = 1 - (matter_density + radiation_density + dark_energy)

        e_2 = (
            radiation_density * (redshift + 1) ** 4
            + matter_density * (redshift + 1) ** 3
            + curvature * (redshift + 1) ** 2
            + dark_energy
        )

        hubble = hubble_constant * e_2 ** (1 / 2)
        return hubble
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    # run doctest
    doctest.testmod()

    # demo LCDM approximation
    matter_density = 0.3

    print(
        hubble_parameter(
            hubble_constant=68.3,
            radiation_density=1e-4,
            matter_density=matter_density,
            dark_energy=1 - matter_density,
            redshift=0,
        )
    )
