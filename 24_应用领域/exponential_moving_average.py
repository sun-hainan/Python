# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / exponential_moving_average



本文件实现 exponential_moving_average 相关的算法功能。

"""



from collections.abc import Iterator







# exponential_moving_average 函数实现

def exponential_moving_average(

    stock_prices: Iterator[float], window_size: int

) -> Iterator[float]:

    """

    Yields exponential moving averages of the given stock prices.

    >>> tuple(exponential_moving_average(iter([2, 5, 3, 8.2, 6, 9, 10]), 3))

    (2, 3.5, 3.25, 5.725, 5.8625, 7.43125, 8.715625)



    :param stock_prices: A stream of stock prices

    :param window_size: The number of stock prices that will trigger a new calculation

                        of the exponential average (window_size > 0)

    :return: Yields a sequence of exponential moving averages



    Formula:



    st = alpha * xt + (1 - alpha) * st_prev



    Where,

    st : Exponential moving average at timestamp t

    xt : stock price in from the stock prices at timestamp t

    st_prev : Exponential moving average at timestamp t-1

    alpha : 2/(1 + window_size) - smoothing factor



    Exponential moving average (EMA) is a rule of thumb technique for

    smoothing time series data using an exponential window function.

    """



    if window_size <= 0:

    # 条件判断

        raise ValueError("window_size must be > 0")



    # Calculating smoothing factor

    alpha = 2 / (1 + window_size)



    # Exponential average at timestamp t

    moving_average = 0.0



    for i, stock_price in enumerate(stock_prices):

    # 遍历循环

        if i <= window_size:

    # 条件判断

            # Assigning simple moving average till the window_size for the first time

            # is reached

            moving_average = (moving_average + stock_price) * 0.5 if i else stock_price

        else:

            # Calculating exponential moving average based on current timestamp data

            # point and previous exponential average value

            moving_average = (alpha * stock_price) + ((1 - alpha) * moving_average)

        yield moving_average





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()



    stock_prices = [2.0, 5, 3, 8.2, 6, 9, 10]

    window_size = 3

    result = tuple(exponential_moving_average(iter(stock_prices), window_size))

    print(f"{stock_prices = }")

    print(f"{window_size = }")

    print(f"{result = }")

