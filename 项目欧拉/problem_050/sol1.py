# -*- coding: utf-8 -*-







from __future__ import annotations

















Consecutive prime sum









The prime 41, can be written as the sum of six consecutive primes:




41 = 2 + 3 + 5 + 7 + 11 + 13









This is the longest sum of consecutive primes that adds to a prime below




one-hundred.









The longest sum of consecutive primes below one-thousand that adds to a prime,




contains 21 terms, and is equal to 953.









Which prime, below one-million, can be written as the sum of the most




consecutive primes?




    Function to return all the prime numbers up to a number 'limit'




    https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes









    >>> prime_sieve(3)




    [2]









    >>> prime_sieve(50)




    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]




    of consecutive the most consecutive primes.









    >>> solution(500)




    499









    >>> solution(1_000)




    953









    >>> solution(10_000)




    9521


