# -*- coding: utf-8 -*-












































Problem 47









The first two consecutive numbers to have two distinct prime factors are:









14 = 2 x 7




15 = 3 x 5









The first three consecutive numbers to have three distinct prime factors are:









644 = 2² x 7 x 23




645 = 3 x 5 x 43




646 = 2 x 17 x 19.









Find the first four consecutive integers to have four distinct prime factors each.




What is the first of these numbers?




    Tests include sorting because only the set matters,




    not the order in which it is produced.




    >>> sorted(set(unique_prime_factors(14)))




    [2, 7]




    >>> sorted(set(unique_prime_factors(644)))




    [2, 7, 23]




    >>> sorted(set(unique_prime_factors(646)))




    [2, 17, 19]




    >>> upf_len(14)




    2




    >>> equality([1, 2, 3, 4])




    False




    >>> equality([2, 2, 2, 2])




    True




    >>> equality([1, 2, 3, 2, 1])




    False




    >>> run(3)




    [644, 645, 646]




    distinct prime factors each.




    >>> solution()




    134043


