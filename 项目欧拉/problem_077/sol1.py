# -*- coding: utf-8 -*-







from __future__ import annotations

















It is possible to write ten as the sum of primes in exactly five different ways:









7 + 3




5 + 5




5 + 3 + 2




3 + 3 + 2 + 2




2 + 2 + 2 + 2 + 2









What is the first value which can be written as the sum of primes in over




five thousand different ways?




    The unique prime partitions can be represented as unique prime decompositions,




    e.g. (7+3) <-> 7*3 = 12, (3+3+2+2) = 3*3*2*2 = 36




    >>> partition(10)




    {32, 36, 21, 25, 30}




    >>> partition(15)




    {192, 160, 105, 44, 112, 243, 180, 150, 216, 26, 125, 126}




    >>> len(partition(20))




    26




    m unique ways.




    >>> solution(4)




    10




    >>> solution(500)




    45




    >>> solution(1000)




    53


