# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / narcissistic_number



本文件实现 narcissistic_number 相关的算法功能。

"""



def find_narcissistic_numbers(limit: int) -> list[int]:

    # find_narcissistic_numbers function



    # find_narcissistic_numbers function

    # find_narcissistic_numbers 函数实现

    """

    Find all narcissistic numbers up to the given limit using dynamic programming.



    This function uses memoization to cache digit power calculations, avoiding

    redundant computations across different numbers with the same digit count.



    Args:

        limit: The upper bound for searching narcissistic numbers (exclusive)



    Returns:

        list[int]: A sorted list of all narcissistic numbers below the limit



    Examples:

        >>> find_narcissistic_numbers(10)

        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        >>> find_narcissistic_numbers(160)

        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 153]

        >>> find_narcissistic_numbers(400)

        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 153, 370, 371]

        >>> find_narcissistic_numbers(1000)

        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 153, 370, 371, 407]

        >>> find_narcissistic_numbers(10000)

        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 153, 370, 371, 407, 1634, 8208, 9474]

        >>> find_narcissistic_numbers(1)

        [0]

        >>> find_narcissistic_numbers(0)

        []

    """

    if limit <= 0:

        return []



    narcissistic_nums = []



    # Memoization: cache[(power, digit)] = digit^power

    # This avoids recalculating the same power for different numbers

    power_cache: dict[tuple[int, int], int] = {}



    def get_digit_power(digit: int, power: int) -> int:

    # get_digit_power function



    # get_digit_power function

    # get_digit_power 函数实现

        """Get digit^power using memoization (DP optimization)."""

        if (power, digit) not in power_cache:

            power_cache[(power, digit)] = digit**power

        return power_cache[(power, digit)]



    # Check each number up to the limit

    for number in range(limit):

        # Count digits

        num_digits = len(str(number))



        # Calculate sum of powered digits using memoized powers

        remaining = number

        digit_sum = 0

        while remaining > 0:

            digit = remaining % 10

            digit_sum += get_digit_power(digit, num_digits)

            remaining //= 10



        # Check if narcissistic

        if digit_sum == number:

            narcissistic_nums.append(number)



    return narcissistic_nums





if __name__ == "__main__":

    import doctest



    doctest.testmod()



    # Demonstrate the dynamic programming approach

    print("Finding all narcissistic numbers up to 10000:")

    print("(Using memoization to cache digit power calculations)")

    print()



    narcissistic_numbers = find_narcissistic_numbers(10000)

    print(f"Found {len(narcissistic_numbers)} narcissistic numbers:")

    print(narcissistic_numbers)

