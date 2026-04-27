# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / resistor_color_code



本文件实现 resistor_color_code 相关的算法功能。

"""



valid_colors: list = [

    "Black",

    "Brown",

    "Red",

    "Orange",

    "Yellow",

    "Green",

    "Blue",

    "Violet",

    "Grey",

    "White",

    "Gold",

    "Silver",

]



significant_figures_color_values: dict[str, int] = {

    "Black": 0,

    "Brown": 1,

    "Red": 2,

    "Orange": 3,

    "Yellow": 4,

    "Green": 5,

    "Blue": 6,

    "Violet": 7,

    "Grey": 8,

    "White": 9,

}



multiplier_color_values: dict[str, float] = {

    "Black": 10**0,

    "Brown": 10**1,

    "Red": 10**2,

    "Orange": 10**3,

    "Yellow": 10**4,

    "Green": 10**5,

    "Blue": 10**6,

    "Violet": 10**7,

    "Grey": 10**8,

    "White": 10**9,

    "Gold": 10**-1,

    "Silver": 10**-2,

}



tolerance_color_values: dict[str, float] = {

    "Brown": 1,

    "Red": 2,

    "Orange": 0.05,

    "Yellow": 0.02,

    "Green": 0.5,

    "Blue": 0.25,

    "Violet": 0.1,

    "Grey": 0.01,

    "Gold": 5,

    "Silver": 10,

}



temperature_coeffecient_color_values: dict[str, int] = {

    "Black": 250,

    "Brown": 100,

    "Red": 50,

    "Orange": 15,

    "Yellow": 25,

    "Green": 20,

    "Blue": 10,

    "Violet": 5,

    "Grey": 1,

}



band_types: dict[int, dict[str, int]] = {

    3: {"significant": 2, "multiplier": 1},

    4: {"significant": 2, "multiplier": 1, "tolerance": 1},

    5: {"significant": 3, "multiplier": 1, "tolerance": 1},

    6: {"significant": 3, "multiplier": 1, "tolerance": 1, "temp_coeffecient": 1},

}







# get_significant_digits 函数实现

def get_significant_digits(colors: list) -> str:

    """

    Function returns the digit associated with the color. Function takes a

    list containing colors as input and returns digits as string



    >>> get_significant_digits(['Black','Blue'])

    '06'



    >>> get_significant_digits(['Aqua','Blue'])

    Traceback (most recent call last):

      ...

    ValueError: Aqua is not a valid color for significant figure bands



    """

    digit = ""

    for color in colors:

    # 遍历循环

        if color not in significant_figures_color_values:

    # 条件判断

            msg = f"{color} is not a valid color for significant figure bands"

            raise ValueError(msg)

        digit = digit + str(significant_figures_color_values[color])

    return str(digit)

    # 返回结果







# get_multiplier 函数实现

def get_multiplier(color: str) -> float:

    """

    Function returns the multiplier value associated with the color.

    Function takes color as input and returns multiplier value



    >>> get_multiplier('Gold')

    0.1



    >>> get_multiplier('Ivory')

    Traceback (most recent call last):

      ...

    ValueError: Ivory is not a valid color for multiplier band



    """

    if color not in multiplier_color_values:

    # 条件判断

        msg = f"{color} is not a valid color for multiplier band"

        raise ValueError(msg)

    return multiplier_color_values[color]

    # 返回结果







# get_tolerance 函数实现

def get_tolerance(color: str) -> float:

    """

    Function returns the tolerance value associated with the color.

    Function takes color as input and returns tolerance value.



    >>> get_tolerance('Green')

    0.5



    >>> get_tolerance('Indigo')

    Traceback (most recent call last):

      ...

    ValueError: Indigo is not a valid color for tolerance band



    """

    if color not in tolerance_color_values:

    # 条件判断

        msg = f"{color} is not a valid color for tolerance band"

        raise ValueError(msg)

    return tolerance_color_values[color]

    # 返回结果







# get_temperature_coeffecient 函数实现

def get_temperature_coeffecient(color: str) -> int:

    """

    Function returns the temperature coeffecient value associated with the color.

    Function takes color as input and returns temperature coeffecient value.



    >>> get_temperature_coeffecient('Yellow')

    25



    >>> get_temperature_coeffecient('Cyan')

    Traceback (most recent call last):

      ...

    ValueError: Cyan is not a valid color for temperature coeffecient band



    """

    if color not in temperature_coeffecient_color_values:

    # 条件判断

        msg = f"{color} is not a valid color for temperature coeffecient band"

        raise ValueError(msg)

    return temperature_coeffecient_color_values[color]

    # 返回结果







# get_band_type_count 函数实现

def get_band_type_count(total_number_of_bands: int, type_of_band: str) -> int:

    """

    Function returns the number of bands of a given type in a resistor with n bands

    Function takes total_number_of_bands and type_of_band as input and returns

    number of bands belonging to that type in the given resistor



    >>> get_band_type_count(3,'significant')

    2



    >>> get_band_type_count(2,'significant')

    Traceback (most recent call last):

      ...

    ValueError: 2 is not a valid number of bands



    >>> get_band_type_count(3,'sign')

    Traceback (most recent call last):

      ...

    ValueError: sign is not valid for a 3 band resistor



    >>> get_band_type_count(3,'tolerance')

    Traceback (most recent call last):

      ...

    ValueError: tolerance is not valid for a 3 band resistor



    >>> get_band_type_count(5,'temp_coeffecient')

    Traceback (most recent call last):

      ...

    ValueError: temp_coeffecient is not valid for a 5 band resistor



    """

    if total_number_of_bands not in band_types:

    # 条件判断

        msg = f"{total_number_of_bands} is not a valid number of bands"

        raise ValueError(msg)

    if type_of_band not in band_types[total_number_of_bands]:

    # 条件判断

        msg = f"{type_of_band} is not valid for a {total_number_of_bands} band resistor"

        raise ValueError(msg)

    return band_types[total_number_of_bands][type_of_band]

    # 返回结果







# check_validity 函数实现

def check_validity(number_of_bands: int, colors: list) -> bool:

    """

    Function checks if the input provided is valid or not.

    Function takes number_of_bands and colors as input and returns

    True if it is valid



    >>> check_validity(3, ["Black","Blue","Orange"])

    True



    >>> check_validity(4, ["Black","Blue","Orange"])

    Traceback (most recent call last):

      ...

    ValueError: Expecting 4 colors, provided 3 colors



    >>> check_validity(3, ["Cyan","Red","Yellow"])

    Traceback (most recent call last):

      ...

    ValueError: Cyan is not a valid color



    """

    if number_of_bands >= 3 and number_of_bands <= 6:

    # 条件判断

        if number_of_bands == len(colors):

    # 条件判断

            for color in colors:

    # 遍历循环

                if color not in valid_colors:

    # 条件判断

                    msg = f"{color} is not a valid color"

                    raise ValueError(msg)

            return True

    # 返回结果

        else:

            msg = f"Expecting {number_of_bands} colors, provided {len(colors)} colors"

            raise ValueError(msg)

    else:

        msg = "Invalid number of bands. Resistor bands must be 3 to 6"

        raise ValueError(msg)







# calculate_resistance 函数实现

def calculate_resistance(number_of_bands: int, color_code_list: list) -> dict:

    """

    Function calculates the total resistance of the resistor using the color codes.

    Function takes number_of_bands, color_code_list as input and returns

    resistance



    >>> calculate_resistance(3, ["Black","Blue","Orange"])

    {'resistance': '6000Ω ±20% '}



    >>> calculate_resistance(4, ["Orange","Green","Blue","Gold"])

    {'resistance': '35000000Ω ±5% '}



    >>> calculate_resistance(5, ["Violet","Brown","Grey","Silver","Green"])

    {'resistance': '7.18Ω ±0.5% '}



    >>> calculate_resistance(6, ["Red","Green","Blue","Yellow","Orange","Grey"])

    {'resistance': '2560000Ω ±0.05% 1 ppm/K'}



    >>> calculate_resistance(0, ["Violet","Brown","Grey","Silver","Green"])

    Traceback (most recent call last):

      ...

    ValueError: Invalid number of bands. Resistor bands must be 3 to 6



    >>> calculate_resistance(4, ["Violet","Brown","Grey","Silver","Green"])

    Traceback (most recent call last):

      ...

    ValueError: Expecting 4 colors, provided 5 colors



    >>> calculate_resistance(4, ["Violet","Silver","Brown","Grey"])

    Traceback (most recent call last):

      ...

    ValueError: Silver is not a valid color for significant figure bands



    >>> calculate_resistance(4, ["Violet","Blue","Lime","Grey"])

    Traceback (most recent call last):

      ...

    ValueError: Lime is not a valid color



    """

    is_valid = check_validity(number_of_bands, color_code_list)

    if is_valid:

    # 条件判断

        number_of_significant_bands = get_band_type_count(

            number_of_bands, "significant"

        )

        significant_colors = color_code_list[:number_of_significant_bands]

        significant_digits = int(get_significant_digits(significant_colors))

        multiplier_color = color_code_list[number_of_significant_bands]

        multiplier = get_multiplier(multiplier_color)

        if number_of_bands == 3:

    # 条件判断

            tolerance_color = None

        else:

            tolerance_color = color_code_list[number_of_significant_bands + 1]

        tolerance = (

            20 if tolerance_color is None else get_tolerance(str(tolerance_color))

        )

        if number_of_bands != 6:

    # 条件判断

            temperature_coeffecient_color = None

        else:

            temperature_coeffecient_color = color_code_list[

                number_of_significant_bands + 2

            ]

        temperature_coeffecient = (

            0

            if temperature_coeffecient_color is None

            else get_temperature_coeffecient(str(temperature_coeffecient_color))

        )

        resisitance = significant_digits * multiplier

        if temperature_coeffecient == 0:

    # 条件判断

            answer = f"{resisitance}Ω ±{tolerance}% "

        else:

            answer = f"{resisitance}Ω ±{tolerance}% {temperature_coeffecient} ppm/K"

        return {"resistance": answer}

    # 返回结果

    else:

        raise ValueError("Input is invalid")





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

