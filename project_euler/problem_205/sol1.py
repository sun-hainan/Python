# -*- coding: utf-8 -*-

"""

Project Euler Problem 205



解决 Project Euler 第 205 题的 Python 实现。

https://projecteuler.net/problem=205

"""



from itertools import product







# =============================================================================

# Project Euler 问题 205

# =============================================================================

def total_frequency_distribution(sides_number: int, dice_number: int) -> list[int]:

    """

    Returns frequency distribution of total



    >>> total_frequency_distribution(sides_number=6, dice_number=1)

    [0, 1, 1, 1, 1, 1, 1]



    >>> total_frequency_distribution(sides_number=4, dice_number=2)

    [0, 0, 1, 2, 3, 4, 3, 2, 1]

    """



    max_face_number = sides_number

    max_total = max_face_number * dice_number

    totals_frequencies = [0] * (max_total + 1)



    min_face_number = 1

    faces_numbers = range(min_face_number, max_face_number + 1)

    for dice_numbers in product(faces_numbers, repeat=dice_number):

    # 遍历循环

        total = sum(dice_numbers)

        totals_frequencies[total] += 1



    return totals_frequencies

    # 返回结果





def solution() -> float:

    # solution 函数实现

    """

    Returns probability that Pyramidal Peter beats Cubic Colin

    rounded to seven decimal places in the form 0.abcdefg



    >>> solution()

    0.5731441

    """



    peter_totals_frequencies = total_frequency_distribution(

        sides_number=4, dice_number=9

    )

    colin_totals_frequencies = total_frequency_distribution(

        sides_number=6, dice_number=6

    )



    peter_wins_count = 0

    min_peter_total = 9

    max_peter_total = 4 * 9

    min_colin_total = 6

    for peter_total in range(min_peter_total, max_peter_total + 1):

    # 遍历循环

        peter_wins_count += peter_totals_frequencies[peter_total] * sum(

            colin_totals_frequencies[min_colin_total:peter_total]

        )



    total_games_number = (4**9) * (6**6)

    peter_win_probability = peter_wins_count / total_games_number



    rounded_peter_win_probability = round(peter_win_probability, ndigits=7)



    return rounded_peter_win_probability

    # 返回结果





if __name__ == "__main__":

    print(f"{solution() = }")

