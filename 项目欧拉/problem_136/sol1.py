# -*- coding: utf-8 -*-












































Singleton Difference









The positive integers, x, y, and z, are consecutive terms of an arithmetic progression.




Given that n is a positive integer, the equation, x^2 - y^2 - z^2 = n,




has exactly one solution when n = 20:




                              13^2 - 10^2 - 7^2 = 20.









In fact there are twenty-five values of n below one hundred for which




the equation has a unique solution.









How many values of n less than fifty million have exactly one solution?









By change of variables









x = y + delta




z = y - delta









The expression can be rewritten:









x^2 - y^2 - z^2 = y * (4 * delta - y) = n









The algorithm loops over delta and y, which is restricted in upper and lower limits,




to count how many solutions each n has.




In the end it is counted how many n's have one solution.




    which n has count == 1.









    >>> solution(3)




    0




    >>> solution(10)




    3




    >>> solution(100)




    25




    >>> solution(110)




    27


