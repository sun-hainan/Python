# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / equated_monthly_installments



本文件实现 equated_monthly_installments 相关的算法功能。

"""



# equated_monthly_installments 函数实现

def equated_monthly_installments(

    principal: float, rate_per_annum: float, years_to_repay: int

) -> float:

    """

    Formula for amortization amount per month:

    A = p * r * (1 + r)^n / ((1 + r)^n - 1)

    where p is the principal, r is the rate of interest per month

    and n is the number of payments



    >>> equated_monthly_installments(25000, 0.12, 3)

    830.3577453212793

    >>> equated_monthly_installments(25000, 0.12, 10)

    358.67737100646826

    >>> equated_monthly_installments(0, 0.12, 3)

    Traceback (most recent call last):

        ...

    Exception: Principal borrowed must be > 0

    >>> equated_monthly_installments(25000, -1, 3)

    Traceback (most recent call last):

        ...

    Exception: Rate of interest must be >= 0

    >>> equated_monthly_installments(25000, 0.12, 0)

    Traceback (most recent call last):

        ...

    Exception: Years to repay must be an integer > 0

    """

    if principal <= 0:

    # 条件判断

        raise Exception("Principal borrowed must be > 0")

    if rate_per_annum < 0:

    # 条件判断

        raise Exception("Rate of interest must be >= 0")

    if years_to_repay <= 0 or not isinstance(years_to_repay, int):

    # 条件判断

        raise Exception("Years to repay must be an integer > 0")



    # Yearly rate is divided by 12 to get monthly rate

    rate_per_month = rate_per_annum / 12



    # Years to repay is multiplied by 12 to get number of payments as payment is monthly

    number_of_payments = years_to_repay * 12



    return (

    # 返回结果

        principal

        * rate_per_month

        * (1 + rate_per_month) ** number_of_payments

        / ((1 + rate_per_month) ** number_of_payments - 1)

    )





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

