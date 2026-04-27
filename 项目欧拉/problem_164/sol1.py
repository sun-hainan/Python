# -*- coding: utf-8 -*-












































Three Consecutive Digital Sum Limit









How many 20 digit numbers n (without any leading zero) exist such that no three




consecutive digits of n have a sum greater than 9?









Brute-force recursive solution with caching of intermediate results.




    previous-previous 'prev2' digit, total sum of 'sum_max'.




    Pass around 'cache' to store/reuse intermediate results.









    >>> solve(digit=1, prev1=0, prev2=0, sum_max=9, first=True, cache={})




    9




    >>> solve(digit=1, prev1=0, prev2=0, sum_max=9, first=False, cache={})




    10









    >>> solution(2)




    45




    >>> solution(10)




    21838806


