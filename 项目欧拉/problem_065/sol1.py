# -*- coding: utf-8 -*-












































The square root of 2 can be written as an infinite continued fraction.









sqrt(2) = 1 + 1 / (2 + 1 / (2 + 1 / (2 + 1 / (2 + ...))))









The infinite continued fraction can be written, sqrt(2) = [1;(2)], (2)




indicates that 2 repeats ad infinitum. In a similar way, sqrt(23) =




[4;(1,3,1,8)].









It turns out that the sequence of partial values of continued




fractions for square roots provide the best rational approximations.




Let us consider the convergents for sqrt(2).









1 + 1 / 2 = 3/2




1 + 1 / (2 + 1 / 2) = 7/5




1 + 1 / (2 + 1 / (2 + 1 / 2)) = 17/12




1 + 1 / (2 + 1 / (2 + 1 / (2 + 1 / 2))) = 41/29









Hence the sequence of the first ten convergents for sqrt(2) are:




1, 3/2, 7/5, 17/12, 41/29, 99/70, 239/169, 577/408, 1393/985, 3363/2378, ...









What is most surprising is that the important mathematical constant,




e = [2;1,2,1,1,4,1,1,6,1,...,1,2k,1,...].









The first ten terms in the sequence of convergents for e are:




2, 3, 8/3, 11/4, 19/7, 87/32, 106/39, 193/71, 1264/465, 1457/536, ...









The sum of digits in the numerator of the 10th convergent is




1 + 4 + 5 + 7 = 17.









Find the sum of the digits in the numerator of the 100th convergent




of the continued fraction for e.









-----









The solution mostly comes down to finding an equation that will generate




the numerator of the continued fraction. For the i-th numerator, the




pattern is:









n_i = m_i * n_(i-1) + n_(i-2)









for m_i = the i-th index of the continued fraction representation of e,




n_0 = 1, and n_1 = 2 as the first 2 numbers of the representation.









For example:




n_9 = 6 * 193 + 106 = 1264




1 + 2 + 6 + 4 = 13









n_10 = 1 * 193 + 1264 = 1457




1 + 4 + 5 + 7 = 17









    >>> sum_digits(1)




    1




    >>> sum_digits(12345)




    15




    >>> sum_digits(999001)




    28




    the continued fraction for e.









    >>> solution(9)




    13




    >>> solution(10)




    17




    >>> solution(50)




    91


