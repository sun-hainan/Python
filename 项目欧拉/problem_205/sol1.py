# -*- coding: utf-8 -*-








Peter has nine four-sided (pyramidal) dice, each with faces numbered 1, 2, 3, 4.
Colin has six six-sided (cubic) dice, each with faces numbered 1, 2, 3, 4, 5, 6.

Peter and Colin roll their dice and compare totals: the highest total wins.
The result is a draw if the totals are equal.

What is the probability that Pyramidal Peter beats Cubic Colin?
Give your answer rounded to seven decimal places in the form 0.abcdefg

    >>> total_frequency_distribution(sides_number=6, dice_number=1)
    [0, 1, 1, 1, 1, 1, 1]

    >>> total_frequency_distribution(sides_number=4, dice_number=2)
    [0, 0, 1, 2, 3, 4, 3, 2, 1]
    rounded to seven decimal places in the form 0.abcdefg

    >>> solution()
    0.5731441