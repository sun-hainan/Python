# -*- coding: utf-8 -*-







from __future__ import annotations

















If p is the perimeter of a right angle triangle with integral length sides,




{a,b,c}, there are exactly three solutions for p = 120.




{20,48,52}, {24,45,51}, {30,40,50}









For which value of p ≤ 1000, is the number of solutions maximised?




    and value as the number of corresponding triplets.




    >>> pythagorean_triple(15)




    Counter({12: 1})




    >>> pythagorean_triple(40)




    Counter({12: 1, 30: 1, 24: 1, 40: 1, 36: 1})




    >>> pythagorean_triple(50)




    Counter({12: 1, 30: 1, 24: 1, 40: 1, 36: 1, 48: 1})




    >>> solution(100)




    90




    >>> solution(200)




    180




    >>> solution(1000)




    840


