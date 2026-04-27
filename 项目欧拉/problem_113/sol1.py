# -*- coding: utf-8 -*-












































Working from left-to-right if no digit is exceeded by the digit to its left it is




called an increasing number; for example, 134468.









Similarly if no digit is exceeded by the digit to its right it is called a decreasing




number; for example, 66420.









We shall call a positive integer that is neither increasing nor decreasing a




"bouncy" number; for example, 155349.









As n increases, the proportion of bouncy numbers below n increases such that there




are only 12951 numbers below one-million that are not bouncy and only 277032




non-bouncy numbers below 10^10.









How many numbers below a googol (10^100) are not bouncy?




    >>> choose(4,2)




    6




    >>> choose(5,3)




    10




    >>> choose(20,6)




    38760




    >>> non_bouncy_exact(1)




    9




    >>> non_bouncy_exact(6)




    7998




    >>> non_bouncy_exact(10)




    136126




    >>> non_bouncy_upto(1)




    9




    >>> non_bouncy_upto(6)




    12951




    >>> non_bouncy_upto(10)




    277032




    >>> solution(6)




    12951




    >>> solution(10)




    277032


