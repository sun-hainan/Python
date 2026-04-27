# -*- coding: utf-8 -*-

"""

算法实现：special_numbers / bell_numbers



本文件实现 bell_numbers 相关的算法功能。

"""



# =============================================================================

# 算法模块：bell_numbers

# =============================================================================

def bell_numbers(max_set_length: int) -> list[int]:

    # bell_numbers function



    # bell_numbers function

    """

    Calculate Bell numbers for the sets of lengths from 0 to max_set_length.

    In other words, calculate first (max_set_length + 1) Bell numbers.



    Args:

        max_set_length (int): The maximum length of the sets for which

        Bell numbers are calculated.



    Returns:

        list: A list of Bell numbers for sets of lengths from 0 to max_set_length.



    Examples:

    >>> bell_numbers(-2)

    Traceback (most recent call last):

        ...

    ValueError: max_set_length must be non-negative

    >>> bell_numbers(0)

    [1]

    >>> bell_numbers(1)

    [1, 1]

    >>> bell_numbers(5)

    [1, 1, 2, 5, 15, 52]

    """

    if max_set_length < 0:

        raise ValueError("max_set_length must be non-negative")



    bell = [0] * (max_set_length + 1)

    bell[0] = 1



    for i in range(1, max_set_length + 1):

        for j in range(i):

            bell[i] += _binomial_coefficient(i - 1, j) * bell[j]



    return bell





def _binomial_coefficient(total_elements: int, elements_to_choose: int) -> int:

    # _binomial_coefficient function



    # _binomial_coefficient function

    """

    Calculate the binomial coefficient C(total_elements, elements_to_choose)



    Args:

        total_elements (int): The total number of elements.

        elements_to_choose (int): The number of elements to choose.



    Returns:

        int: The binomial coefficient C(total_elements, elements_to_choose).



    Examples:

    >>> _binomial_coefficient(5, 2)

    10

    >>> _binomial_coefficient(6, 3)

    20

    """

    if elements_to_choose in {0, total_elements}:

        return 1



    elements_to_choose = min(elements_to_choose, total_elements - elements_to_choose)



    coefficient = 1

    for i in range(elements_to_choose):

        coefficient *= total_elements - i

        coefficient //= i + 1



    return coefficient





if __name__ == "__main__":

    import doctest



    doctest.testmod()

