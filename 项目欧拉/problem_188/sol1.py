# -*- coding: utf-8 -*-












































The hyperexponentiation of a number









The hyperexponentiation or tetration of a number a by a positive integer b,




denoted by a↑↑b or b^a, is recursively defined by:









a↑↑1 = a,




a↑↑(k+1) = a(a↑↑k).









Thus we have e.g. 3↑↑2 = 3^3 = 27, hence 3↑↑3 = 3^27 = 7625597484987 and




3↑↑4 is roughly 103.6383346400240996*10^12.









Find the last 8 digits of 1777↑↑1855.









References:




    - https://en.wikipedia.org/wiki/Tetration




    of `base ** exponent % modulo_value`, without calculating




    the actual number.




    >>> _modexpt(2, 4, 10)




    6




    >>> _modexpt(2, 1024, 100)




    16




    >>> _modexpt(13, 65535, 7)




    6




    height, i.e. the number base↑↑height:









    >>> solution(base=3, height=2)




    27




    >>> solution(base=3, height=3)




    97484987




    >>> solution(base=123, height=456, digits=4)




    2547


