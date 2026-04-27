# -*- coding: utf-8 -*-







































Problem 551









Let a(0), a(1),... be an integer sequence defined by:




     a(0) = 1




     for n >= 1, a(n) is the sum of the digits of all preceding terms









The sequence starts with 1, 1, 2, 4, 8, ...




You are given a(10^6) = 31054319.









Find a(10^15)




    smallest term for which c > 10^k when the terms are written in the form:




            a(i) = b * 10^k + c









    For any a(i), if digitsum(b) and c have the same value, the difference




    between subsequent terms will be the same until c >= 10^k.  This difference




    is cached to greatly speed up the computation.









    Arguments:




    a_i -- array of digits starting from the one's place that represent




           the i-th term in the sequence




    k --  k when terms are written in the from a(i) = b*10^k + c.




          Term are calulcated until c > 10^k or the n-th term is reached.




    i -- position along the sequence




    n -- term to calculate up to if k is large enough









    Return: a tuple of difference between ending term and starting term, and




    the number of terms calculated. ex. if starting term is a_0=1, and




    ending term is a_10=62, then (61, 9) is returned.




    starting at index k









    >>> solution(10)




    62









    >>> solution(10**6)




    31054319









    >>> solution(10**15)




    73597483551591773


