# -*- coding: utf-8 -*-












































Coin sums









In England the currency is made up of pound, f, and pence, p, and there are




eight coins in general circulation:









1p, 2p, 5p, 10p, 20p, 50p, f1 (100p) and f2 (200p).




It is possible to make f2 in the following way:









1xf1 + 1x50p + 2x20p + 1x5p + 1x2p + 3x1p




How many different ways can f2 be made using any number of coins?









Hint:




    > There are 100 pence in a pound (f1 = 100p)




    > There are coins(in pence) are available: 1, 2, 5, 10, 20, 50, 100 and 200.




    > how many different ways you can combine these values to create 200 pence.









Example:




    to make 6p there are 5 ways




      1,1,1,1,1,1




      1,1,1,1,2




      1,1,2,2




      2,2,2




      1,5




    to make 5p there are 4 ways




      1,1,1,1,1




      1,1,1,2




      1,2,2




      5




    The solution is based on dynamic programming paradigm in a bottom-up fashion.









    >>> solution(500)




    6295434




    >>> solution(200)




    73682




    >>> solution(50)




    451




    >>> solution(10)




    11


