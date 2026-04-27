# -*- coding: utf-8 -*-












































For an integer n ≥ 4, we define the lower prime square root of n, denoted by




lps(n), as the largest prime ≤ √n and the upper prime square root of n, ups(n),




as the smallest prime ≥ √n.









So, for example, lps(4) = 2 = ups(4), lps(1000) = 31, ups(1000) = 37. Let us




call an integer n ≥ 4 semidivisible, if one of lps(n) and ups(n) divides n,




but not both.









The sum of the semidivisible numbers not exceeding 15 is 30, the numbers are 8,




10 and 12. 15 is not semidivisible because it is a multiple of both lps(15) = 3




and ups(15) = 5. As a further example, the sum of the 92 semidivisible numbers




up to 1000 is 34825.









What is the sum of all semidivisible numbers not exceeding 999966663333 ?




    Function to return all the prime numbers up to a certain number




    https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes




    >>> prime_sieve(3)




    [2]




    >>> prime_sieve(50)




    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]




    >>> solution(1000)




    34825









    >>> solution(10_000)




    1134942









    >>> solution(100_000)




    36393008


