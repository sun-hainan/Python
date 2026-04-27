# -*- coding: utf-8 -*-












































Amicable Chains









The proper divisors of a number are all the divisors excluding the number itself.




For example, the proper divisors of 28 are 1, 2, 4, 7, and 14.




As the sum of these divisors is equal to 28, we call it a perfect number.









Interestingly the sum of the proper divisors of 220 is 284 and




the sum of the proper divisors of 284 is 220, forming a chain of two numbers.




For this reason, 220 and 284 are called an amicable pair.









Perhaps less well known are longer chains.




For example, starting with 12496, we form a chain of five numbers:




    12496 -> 14288 -> 15472 -> 14536 -> 14264 (-> 12496 -> ...)









Since this chain returns to its starting point, it is called an amicable chain.









Find the smallest member of the longest amicable chain with




no element exceeding one million.









Solution is doing the following:




- Get relevant prime numbers




- Iterate over product combination of prime numbers to generate all non-prime




  numbers up to max number, by keeping track of prime factors




- Calculate the sum of factors for each number




- Iterate over found some factors to find longest chain









    >>> generate_primes(6)




    [2, 3, 5]









    >>> chain = [0] * 3




    >>> primes_degrees = {}




    >>> multiply(




    ...     chain=chain,




    ...     primes=[2],




    ...     min_prime_idx=0,




    ...     prev_num=1,




    ...     max_num=2,




    ...     prev_sum=0,




    ...     primes_degrees=primes_degrees,




    ... )




    >>> chain




    [0, 0, 1]




    >>> primes_degrees




    {2: 1}









    >>> find_longest_chain(chain=[0, 0, 0, 0, 0, 0, 6], max_num=6)




    6









    >>> solution(10)




    6




    >>> solution(200000)




    12496


