# -*- coding: utf-8 -*-







from __future__ import annotations












Prime digit replacements




Problem 51









By replacing the 1st digit of the 2-digit number *3, it turns out that six of




the nine possible values: 13, 23, 43, 53, 73, and 83, are all prime.









By replacing the 3rd and 4th digits of 56**3 with the same digit, this 5-digit




number is the first example having seven primes among the ten generated numbers,




yielding the family: 56003, 56113, 56333, 56443, 56663, 56773, and 56993.




Consequently 56003, being the first member of this family, is the smallest prime




with this property.









Find the smallest prime which, by replacing part of the number (not necessarily




adjacent digits) with the same digit, is part of an eight prime value family.




    Function to return all the prime numbers up to a certain number




    https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes









    >>> prime_sieve(3)




    [2]









    >>> prime_sieve(50)




    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]




    contains at least one repeating digit









    >>> digit_replacements(544)




    [[500, 511, 522, 533, 544, 555, 566, 577, 588, 599]]









    >>> digit_replacements(3112)




    [[3002, 3112, 3222, 3332, 3442, 3552, 3662, 3772, 3882, 3992]]









    >>> solution(2)




    229399









    >>> solution(3)




    221311


