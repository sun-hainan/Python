# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / polynomial_division

本文件实现 polynomial_division 相关的算法功能。
"""

from typing import Tuple, List

def polynomial_division(dividend: List[int], divisor: List[int]) -> Tuple[List[int], List[int]]:
    """
    多项式除法 - 模拟长除法
    
    Args:
        dividend: 被除多项式系数列表
        divisor: 除多项式系数列表
    
    Returns:
        (商, 余数) 元组
    """
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

if __name__ == "__main__":
    dividend = [1, 2, 3, 1]
    divisor = [1, 1]
    
    quotient, remainder = polynomial_division(dividend, divisor)
    print(f"被除多项式: {dividend}")
    print(f"除多项式: {divisor}")
    print(f"商: {quotient}")
    print(f"余数: {remainder}")
    
    dividend2 = [1, 0, 0, -1]
    divisor2 = [1, -1]
    q2, r2 = polynomial_division(dividend2, divisor2)
    print(f"测试2: {dividend2} / {divisor2} = 商{q2}, 余{r2}")
