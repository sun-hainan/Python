# -*- coding: utf-8 -*-







from __future__ import annotations

















For any integer n, consider the three functions









f1,n(x,y,z) = x^(n+1) + y^(n+1) - z^(n+1)




f2,n(x,y,z) = (xy + yz + zx)*(x^(n-1) + y^(n-1) - z^(n-1))




f3,n(x,y,z) = xyz*(xn-2 + yn-2 - zn-2)









and their combination









fn(x,y,z) = f1,n(x,y,z) + f2,n(x,y,z) - f3,n(x,y,z)









We call (x,y,z) a golden triple of order k if x, y, and z are all rational numbers




of the form a / b with 0 < a < b ≤ k and there is (at least) one integer n,




so that fn(x,y,z) = 0.









Let s(x,y,z) = x + y + z.




Let t = u / v be the sum of all distinct s(x,y,z) for all golden triples




(x,y,z) of order 35.




All the s(x,y,z) and t must be in reduced form.









Find u + v.



















By expanding the brackets it is easy to show that




fn(x, y, z) = (x + y + z) * (x^n + y^n - z^n).









Since x,y,z are positive, the requirement fn(x, y, z) = 0 is fulfilled if and




only if x^n + y^n = z^n.









By Fermat's Last Theorem, this means that the absolute value of n can not




exceed 2, i.e. n is in {-2, -1, 0, 1, 2}. We can eliminate n = 0 since then the




equation would reduce to 1 + 1 = 1, for which there are no solutions.









So all we have to do is iterate through the possible numerators and denominators




of x and y, calculate the corresponding z, and check if the corresponding numerator and




denominator are integer and satisfy 0 < z_num < z_den <= 0. We use a set "uniquq_s"




to make sure there are no duplicates, and the fractions.Fraction class to make sure




we get the right numerator and denominator.









Reference:




https://en.wikipedia.org/wiki/Fermat%27s_Last_Theorem









    >>> is_sq(1)




    True




    >>> is_sq(1000001)




    False




    >>> is_sq(1000000)




    True




    numerator and denominator of their sum in lowest form.




    >>> add_three(1, 3, 1, 3, 1, 3)




    (1, 1)




    >>> add_three(2, 5, 4, 11, 12, 3)




    (262, 55)




    golden triples (x,y,z) of the given order.









    >>> solution(5)




    296




    >>> solution(10)




    12519




    >>> solution(20)




    19408891927


