# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / simple_moving_average



本文件实现 simple_moving_average 相关的算法功能。

"""



from collections.abc import Sequence







# simple_moving_average 函数实现

def simple_moving_average(

    data: Sequence[float], window_size: int

) -> list[float | None]:

    """

    Calculate the simple moving average (SMA) for some given time series data.



    :param data: A list of numerical data points.

    :param window_size: An integer representing the size of the SMA window.

    :return: A list of SMA values with the same length as the input data.



    Examples:

    >>> sma = simple_moving_average([10, 12, 15, 13, 14, 16, 18, 17, 19, 21], 3)

    >>> [round(value, 2) if value is not None else None for value in sma]

    [None, None, 12.33, 13.33, 14.0, 14.33, 16.0, 17.0, 18.0, 19.0]

    >>> simple_moving_average([10, 12, 15], 5)

    [None, None, None]

    >>> simple_moving_average([10, 12, 15, 13, 14, 16, 18, 17, 19, 21], 0)

    Traceback (most recent call last):

    ...

    ValueError: Window size must be a positive integer

    """

    if window_size < 1:

    # 条件判断

        raise ValueError("Window size must be a positive integer")



    sma: list[float | None] = []



    for i in range(len(data)):

    # 遍历循环

        if i < window_size - 1:

    # 条件判断

            sma.append(None)  # SMA not available for early data points

        else:

            window = data[i - window_size + 1 : i + 1]

            sma_value = sum(window) / window_size

            sma.append(sma_value)

    return sma

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()



    # Example data (replace with your own time series data)

    data = [10, 12, 15, 13, 14, 16, 18, 17, 19, 21]



    # Specify the window size for the SMA

    window_size = 3



    # Calculate the Simple Moving Average

    sma_values = simple_moving_average(data, window_size)



    # Print the SMA values

    print("Simple Moving Average (SMA) Values:")

    for i, value in enumerate(sma_values):

    # 遍历循环

        if value is not None:

    # 条件判断

            print(f"Day {i + 1}: {value:.2f}")

        else:

            print(f"Day {i + 1}: Not enough data for SMA")

