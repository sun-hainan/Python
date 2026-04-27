# -*- coding: utf-8 -*-








The number 145 is well known for the property that the sum of the factorial of its
digits is equal to 145:

1! + 4! + 5! = 1 + 24 + 120 = 145

Perhaps less well known is 169, in that it produces the longest chain of numbers that
link back to 169; it turns out that there are only three such loops that exist:

169 → 363601 → 1454 → 169
871 → 45361 → 871
872 → 45362 → 872

It is not difficult to prove that EVERY starting number will eventually get stuck in a
loop. For example,

69 → 363600 → 1454 → 169 → 363601 (→ 1454)
78 → 45360 → 871 → 45361 (→ 871)
540 → 145 (→ 145)

Starting with 69 produces a chain of five non-repeating terms, but the longest
non-repeating chain with a starting number below one million is sixty terms.

How many chains, with a starting number below one million, contain exactly sixty
non-repeating terms?

Solution approach:
This solution simply consists in a loop that generates the chains of non repeating
items using the cached sizes of the previous chains.
The generation of the chain stops before a repeating item or if the size of the chain
is greater then the desired one.
After generating each chain, the length is checked and the counter increases.

    >>> digit_factorial_sum(69.0)
    Traceback (most recent call last):
        ...
    TypeError: Parameter number must be int

    >>> digit_factorial_sum(-1)
    Traceback (most recent call last):
        ...
    ValueError: Parameter number must be greater than or equal to 0

    >>> digit_factorial_sum(0)
    1

    >>> digit_factorial_sum(69)
    363600
    chain_length non repeating elements.

    >>> solution(10.0, 1000)
    Traceback (most recent call last):
        ...
    TypeError: Parameters chain_length and number_limit must be int

    >>> solution(10, 1000.0)
    Traceback (most recent call last):
        ...
    TypeError: Parameters chain_length and number_limit must be int

    >>> solution(0, 1000)
    Traceback (most recent call last):
        ...
    ValueError: Parameters chain_length and number_limit must be greater than 0

    >>> solution(10, 0)
    Traceback (most recent call last):
        ...
    ValueError: Parameters chain_length and number_limit must be greater than 0

    >>> solution(10, 1000)
    26