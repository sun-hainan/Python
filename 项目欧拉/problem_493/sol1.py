# -*- coding: utf-8 -*-








70 coloured balls are placed in an urn, 10 for each of the seven rainbow colours.
What is the expected number of distinct colours in 20 randomly picked balls?
Give your answer with nine digits after the decimal point (a.bcdefghij).

-----

This combinatorial problem can be solved by decomposing the problem into the
following steps:
1. Calculate the total number of possible picking combinations
[combinations := binom_coeff(70, 20)]
2. Calculate the number of combinations with one colour missing
[missing := binom_coeff(60, 20)]
3. Calculate the probability of one colour missing
[missing_prob := missing / combinations]
4. Calculate the probability of no colour missing
[no_missing_prob := 1 - missing_prob]
5. Calculate the expected number of distinct colours
[expected = 7 * no_missing_prob]

References:
- https://en.wikipedia.org/wiki/Binomial_coefficient

    >>> solution(10)
    '5.669644129'

    >>> solution(30)
    '6.985042712'