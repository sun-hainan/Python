# -*- coding: utf-8 -*-

"""

算法实现：代数算法 / polynomial_gcd



本文件实现 polynomial_gcd 相关的算法功能。

"""



from typing import List, Tuple



def polynomial_divide(dividend: List[int], divisor: List[int]) -> Tuple[List[int], List[int]]:

    """多项式除法 - 返回商和余数"""

    remainder = dividend.copy()

    quotient_len = max(0, len(dividend) - len(divisor) + 1)

    quotient = [0] * quotient_len

    

    while len(remainder) >= len(divisor) and remainder != [0] * len(remainder):

        lead_coeff = remainder[-1] // divisor[-1]

        lead_power = len(remainder) - len(divisor)

        quotient[lead_power] = lead_coeff

        

        for i in range(len(divisor)):

            remainder[lead_power + i] -= lead_coeff * divisor[i]

        

        while len(remainder) > 0 and remainder[-1] == 0:

            remainder.pop()

    

    return quotient, remainder



def polynomial_gcd(poly_a: List[int], poly_b: List[int]) -> List[int]:

    """

    多项式最大公约数 - 使用欧几里得算法

    

    Args:

        poly_a: 第一个多项式系数列表

        poly_b: 第二个多项式系数列表

    

    Returns:

        GCD多项式系数列表

    """

    if len(poly_a) < len(poly_b):

        poly_a, poly_b = poly_b, poly_a

    

    while len(poly_b) > 0 and poly_b != [0] * len(poly_b):

        _, remainder = polynomial_divide(poly_a, poly_b)

        poly_a, poly_b = poly_b, remainder

    

    if poly_a and poly_a[-1] != 1:

        lead = poly_a[-1]

        poly_a = [c // lead for c in poly_a]

    

    return poly_a if poly_a else [0]



if __name__ == "__main__":

    print("=== 多项式GCD测试 ===")

    

    poly1 = [1, 2, 1]  # (x+1)²

    poly2 = [1, 1]  # (x+1)

    

    gcd = polynomial_gcd(poly1, poly2)

    print(f"GCD({poly1}, {poly2}) = {gcd}")

    

    poly3 = [1, 0, -1]  # x² - 1

    poly4 = [1, -1]  # x - 1

    

    gcd2 = polynomial_gcd(poly3, poly4)

    print(f"GCD({poly3}, {poly4}) = {gcd2}")

    

    poly5 = [1, 0, 0, -1]  # x³ - 1

    poly6 = [1, -1]  # x - 1

    

    gcd3 = polynomial_gcd(poly5, poly6)

    print(f"GCD({poly5}, {poly6}) = {gcd3}")

