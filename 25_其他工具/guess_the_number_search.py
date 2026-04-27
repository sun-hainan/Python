# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / guess_the_number_search



本文件实现 guess_the_number_search 相关的算法功能。

"""



# temp_input_value 函数实现

def temp_input_value(

    min_val: int = 10, max_val: int = 1000, option: bool = True

) -> int:

    """

    Temporary input values for tests



    >>> temp_input_value(option=True)

    10



    >>> temp_input_value(option=False)

    1000



    >>> temp_input_value(min_val=100, option=True)

    100



    >>> temp_input_value(min_val=100, max_val=50)

    Traceback (most recent call last):

        ...

    ValueError: Invalid value for min_val or max_val (min_value < max_value)



    >>> temp_input_value("ten","fifty",1)

    Traceback (most recent call last):

        ...

    AssertionError: Invalid type of value(s) specified to function!



    >>> temp_input_value(min_val=-100, max_val=500)

    -100



    >>> temp_input_value(min_val=-5100, max_val=-100)

    -5100

    """

    assert (

        isinstance(min_val, int)

        and isinstance(max_val, int)

        and isinstance(option, bool)

    ), "Invalid type of value(s) specified to function!"



    if min_val > max_val:

    # 条件判断

        raise ValueError("Invalid value for min_val or max_val (min_value < max_value)")

    return min_val if option else max_val

    # 返回结果







# get_avg 函数实现

def get_avg(number_1: int, number_2: int) -> int:

    """

    Return the mid-number(whole) of two integers a and b



    >>> get_avg(10, 15)

    12



    >>> get_avg(20, 300)

    160



    >>> get_avg("abcd", 300)

    Traceback (most recent call last):

        ...

    TypeError: can only concatenate str (not "int") to str



    >>> get_avg(10.5,50.25)

    30

    """

    return int((number_1 + number_2) / 2)

    # 返回结果







# guess_the_number 函数实现

def guess_the_number(lower: int, higher: int, to_guess: int) -> None:

    """

    The `guess_the_number` function that guess the number by some operations

    and using inner functions



    >>> guess_the_number(10, 1000, 17)

    started...

    guess the number : 17

    details : [505, 257, 133, 71, 40, 25, 17]



    >>> guess_the_number(-10000, 10000, 7)

    started...

    guess the number : 7

    details : [0, 5000, 2500, 1250, 625, 312, 156, 78, 39, 19, 9, 4, 6, 7]



    >>> guess_the_number(10, 1000, "a")

    Traceback (most recent call last):

        ...

    AssertionError: argument values must be type of "int"



    >>> guess_the_number(10, 1000, 5)

    Traceback (most recent call last):

        ...

    ValueError: guess value must be within the range of lower and higher value



    >>> guess_the_number(10000, 100, 5)

    Traceback (most recent call last):

        ...

    ValueError: argument value for lower and higher must be(lower > higher)

    """

    assert (

        isinstance(lower, int) and isinstance(higher, int) and isinstance(to_guess, int)

    ), 'argument values must be type of "int"'



    if lower > higher:

    # 条件判断

        raise ValueError("argument value for lower and higher must be(lower > higher)")



    if not lower < to_guess < higher:

    # 条件判断

        raise ValueError(

            "guess value must be within the range of lower and higher value"

        )





# answer 函数实现

    def answer(number: int) -> str:

        """

        Returns value by comparing with entered `to_guess` number

        """

        if number > to_guess:

    # 条件判断

            return "high"

    # 返回结果

        elif number < to_guess:

            return "low"

    # 返回结果

        else:

            return "same"

    # 返回结果



    print("started...")



    last_lowest = lower

    last_highest = higher



    last_numbers = []



    while True:

    # 条件循环

        number = get_avg(last_lowest, last_highest)

        last_numbers.append(number)



        if answer(number) == "low":

    # 条件判断

            last_lowest = number

        elif answer(number) == "high":

            last_highest = number

        else:

            break



    print(f"guess the number : {last_numbers[-1]}")

    print(f"details : {last_numbers!s}")







# main 函数实现

def main() -> None:

    """

    starting point or function of script

    """

    lower = int(input("Enter lower value : ").strip())

    higher = int(input("Enter high value : ").strip())

    guess = int(input("Enter value to guess : ").strip())

    guess_the_number(lower, higher, guess)





if __name__ == "__main__":

    # 条件判断

    main()

