# -*- coding: utf-8 -*-












































Problem Statement:









Euler discovered the remarkable quadratic formula:




n2 + n + 41




It turns out that the formula will produce 40 primes for the consecutive values




n = 0 to 39. However, when n = 40, 402 + 40 + 41 = 40(40 + 1) + 41 is divisible




by 41, and certainly when n = 41, 412 + 41 + 41 is clearly divisible by 41.




The incredible formula  n2 - 79n + 1601 was discovered, which produces 80 primes




for the consecutive values n = 0 to 79. The product of the coefficients, -79 and




1601, is -126479.




Considering quadratics of the form:




n² + an + b, where |a| &lt; 1000 and |b| &lt; 1000




where |n| is the modulus/absolute value of ne.g. |11| = 11 and |-4| = 4




Find the product of the coefficients, a and b, for the quadratic expression that




produces the maximum number of primes for consecutive values of n, starting with




n = 0.




    A number is prime if it has exactly two factors: 1 and itself.




    Returns boolean representing primality of given number num (i.e., if the




    result is true, then the number is indeed prime else it is not).









    >>> is_prime(2)




    True




    >>> is_prime(3)




    True




    >>> is_prime(27)




    False




    >>> is_prime(2999)




    True




    >>> is_prime(0)




    False




    >>> is_prime(1)




    False




    >>> is_prime(-10)




    False




    -59231




    >>> solution(200, 1000)




    -59231




    >>> solution(200, 200)




    -4925




    >>> solution(-1000, 1000)




    0




    >>> solution(-1000, -1000)




    0


