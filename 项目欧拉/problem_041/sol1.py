# -*- coding: utf-8 -*-







from __future__ import annotations

















We shall say that an n-digit number is pandigital if it makes use of all the digits




1 to n exactly once. For example, 2143 is a 4-digit pandigital and is also prime.




What is the largest n-digit pandigital prime that exists?









All pandigital numbers except for 1, 4 ,7 pandigital numbers are divisible by 3.




So we will check only 7 digit pandigital numbers to obtain the largest possible




pandigital prime.









    A number is prime if it has exactly two factors: 1 and itself.









    >>> is_prime(0)




    False




    >>> is_prime(1)




    False




    >>> is_prime(2)




    True




    >>> is_prime(3)




    True




    >>> is_prime(27)




    False




    >>> is_prime(87)




    False




    >>> is_prime(563)




    True




    >>> is_prime(2999)




    True




    >>> is_prime(67483)




    False




    If there are none, then it will return 0.




    >>> solution(2)




    0




    >>> solution(4)




    4231




    >>> solution(7)




    7652413


