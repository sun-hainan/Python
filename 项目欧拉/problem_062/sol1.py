# -*- coding: utf-8 -*-












































The cube, 41063625 (345^3), can be permuted to produce two other cubes:




56623104 (384^3) and 66430125 (405^3). In fact, 41063625 is the smallest cube




which has exactly three permutations of its digits which are also cube.









Find the smallest cube for which exactly five permutations of its digits are




cube.




    ascending order. Sorting maintains an ordering of the digits that allows




    you to compare permutations. Store each sorted sequence of digits in a




    dictionary, whose key is the sequence of digits and value is a list of




    numbers that are the base of the cube.









    Once you find 5 numbers that produce the same sequence of digits, return




    the smallest one, which is at index 0 since we insert each base number in




    ascending order.









    >>> solution(2)




    125




    >>> solution(3)




    41063625









    >>> get_digits(3)




    '27'




    >>> get_digits(99)




    '027999'




    >>> get_digits(123)




    '0166788'


