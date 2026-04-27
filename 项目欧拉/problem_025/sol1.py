# -*- coding: utf-8 -*-








    Fn = Fn-1 + Fn-2, where F1 = 1 and F2 = 1.

Hence the first 12 terms will be:

    F1 = 1
    F2 = 1
    F3 = 2
    F4 = 3
    F5 = 5
    F6 = 8
    F7 = 13
    F8 = 21
    F9 = 34
    F10 = 55
    F11 = 89
    F12 = 144

The 12th term, F12, is the first term to contain three digits.

What is the index of the first term in the Fibonacci sequence to contain 1000
digits?
    and creating an array of ints using the Fibonacci formula.
    Returns the nth element of the array.

    >>> fibonacci(2)
    1
    >>> fibonacci(3)
    2
    >>> fibonacci(5)
    5
    >>> fibonacci(10)
    55
    >>> fibonacci(12)
    144

    of the resulting Fibonacci result is the input value n. Returns the term
    of the Fibonacci sequence where this occurs.

    >>> fibonacci_digits_index(1000)
    4782
    >>> fibonacci_digits_index(100)
    476
    >>> fibonacci_digits_index(50)
    237
    >>> fibonacci_digits_index(3)
    12
    n digits.

    >>> solution(1000)
    4782
    >>> solution(100)
    476
    >>> solution(50)
    237
    >>> solution(3)
    12