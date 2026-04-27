# -*- coding: utf-8 -*-





























Smallest multiple









2520 is the smallest number that can be divided by each of the numbers




from 1 to 10 without any remainder.









What is the smallest positive number that is _evenly divisible_ by all




of the numbers from 1 to 20?









References:




    - https://en.wiktionary.org/wiki/evenly_divisible




    - https://en.wikipedia.org/wiki/Euclidean_algorithm




    - https://en.wikipedia.org/wiki/Least_common_multiple









    Using the property that lcm(a, b) * greatest_common_divisor(a, b) = a*b









    >>> lcm(3, 15)




    15




    >>> lcm(1, 27)




    27




    >>> lcm(13, 27)




    351




    >>> lcm(64, 48)




    192




    with no remainder) by all of the numbers from 1 to n.









    >>> solution(10)




    2520




    >>> solution(15)




    360360




    >>> solution(22)




    232792560


