# -*- coding: utf-8 -*-

















































Let r be the remainder when (a-1)^n + (a+1)^n is divided by a^2.




For example, if a = 7 and n = 3, then r = 42: 6^3 + 8^3 = 728 ≡ 42 mod 49.




And as n varies, so too will r, but for a = 7 it turns out that r_max = 42.




For 3 ≤ a ≤ 1000, find ∑ r_max.














On expanding the terms, we get 2 if n is even and 2an if n is odd.




For maximizing the value, 2an < a*a => n <= (a - 1)/2 (integer division)




    >>> solution(10)




    300




    >>> solution(100)




    330750




    >>> solution(1000)




    333082500


