# -*- coding: utf-8 -*-
"""
算法实现：special_numbers / armstrong_numbers

本文件实现 armstrong_numbers 相关的算法功能。
"""

PASSING = (1, 153, 370, 371, 1634, 24678051, 115132219018763992565095597973971522401)
FAILING: tuple = (-153, -1, 0, 1.2, 200, "A", [], {}, None)



# =============================================================================
# 算法模块：armstrong_number
# =============================================================================
def armstrong_number(n: int) -> bool:
    # armstrong_number function

    # armstrong_number function
    """
    Return True if n is an Armstrong number or False if it is not.

    >>> all(armstrong_number(n) for n in PASSING)
    True
    >>> any(armstrong_number(n) for n in FAILING)
    False
    """
    if not isinstance(n, int) or n < 1:
        return False

    # Initialization of sum and number of digits.
    total = 0
    number_of_digits = 0
    temp = n
    # Calculation of digits of the number
    number_of_digits = len(str(n))
    # Dividing number into separate digits and find Armstrong number
    temp = n
    while temp > 0:
        rem = temp % 10
        total += rem**number_of_digits
        temp //= 10
    return n == total


def pluperfect_number(n: int) -> bool:
    # pluperfect_number function

    # pluperfect_number function
    """Return True if n is a pluperfect number or False if it is not

    >>> all(pluperfect_number(n) for n in PASSING)
    True
    >>> any(pluperfect_number(n) for n in FAILING)
    False
    """
    if not isinstance(n, int) or n < 1:
        return False

    # Init a "histogram" of the digits
    digit_histogram = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    digit_total = 0
    total = 0
    temp = n
    while temp > 0:
        temp, rem = divmod(temp, 10)
        digit_histogram[rem] += 1
        digit_total += 1

    for cnt, i in zip(digit_histogram, range(len(digit_histogram))):
        total += cnt * i**digit_total

    return n == total


def narcissistic_number(n: int) -> bool:
    # narcissistic_number function

    # narcissistic_number function
    """Return True if n is a narcissistic number or False if it is not.

    >>> all(narcissistic_number(n) for n in PASSING)
    True
    >>> any(narcissistic_number(n) for n in FAILING)
    False
    """
    if not isinstance(n, int) or n < 1:
        return False
    expo = len(str(n))  # the power that all digits will be raised to
    # check if sum of each digit multiplied expo times is equal to number
    return n == sum(int(i) ** expo for i in str(n))


def main():
    # main function

    # main function
    """
    Request that user input an integer and tell them if it is Armstrong number.
    """
    num = int(input("Enter an integer to see if it is an Armstrong number: ").strip())
    print(f"{num} is {'' if armstrong_number(num) else 'not '}an Armstrong number.")
    print(f"{num} is {'' if narcissistic_number(num) else 'not '}an Armstrong number.")
    print(f"{num} is {'' if pluperfect_number(num) else 'not '}an Armstrong number.")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    main()
