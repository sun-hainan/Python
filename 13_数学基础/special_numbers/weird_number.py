# -*- coding: utf-8 -*-

"""

算法实现：special_numbers / weird_number



本文件实现 weird_number 相关的算法功能。

"""



from math import sqrt







# =============================================================================

# 算法模块：factors

# =============================================================================

def factors(number: int) -> list[int]:

    # factors function



    # factors function

    """

    >>> factors(12)

    [1, 2, 3, 4, 6]

    >>> factors(1)

    [1]

    >>> factors(100)

    [1, 2, 4, 5, 10, 20, 25, 50]



    # >>> factors(-12)

    # [1, 2, 3, 4, 6]

    """



    values = [1]

    for i in range(2, int(sqrt(number)) + 1, 1):

        if number % i == 0:

            values.append(i)

            if int(number // i) != i:

                values.append(int(number // i))

    return sorted(values)





def abundant(n: int) -> bool:

    # abundant function



    # abundant function

    """

    >>> abundant(0)

    True

    >>> abundant(1)

    False

    >>> abundant(12)

    True

    >>> abundant(13)

    False

    >>> abundant(20)

    True



    # >>> abundant(-12)

    # True

    """

    return sum(factors(n)) > n





def semi_perfect(number: int) -> bool:

    # semi_perfect function



    # semi_perfect function

    """

    >>> semi_perfect(0)

    True

    >>> semi_perfect(1)

    True

    >>> semi_perfect(12)

    True

    >>> semi_perfect(13)

    False



    # >>> semi_perfect(-12)

    # True

    """

    values = factors(number)

    r = len(values)

    subset = [[0 for i in range(number + 1)] for j in range(r + 1)]

    for i in range(r + 1):

        subset[i][0] = True



    for i in range(1, number + 1):

        subset[0][i] = False



    for i in range(1, r + 1):

        for j in range(1, number + 1):

            if j < values[i - 1]:

                subset[i][j] = subset[i - 1][j]

            else:

                subset[i][j] = subset[i - 1][j] or subset[i - 1][j - values[i - 1]]



    return subset[r][number] != 0





def weird(number: int) -> bool:

    # weird function



    # weird function

    """

    >>> weird(0)

    False

    >>> weird(70)

    True

    >>> weird(77)

    False

    """

    return abundant(number) and not semi_perfect(number)





if __name__ == "__main__":

    import doctest



    doctest.testmod(verbose=True)

    for number in (69, 70, 71):

        print(f"{number} is {'' if weird(number) else 'not '}weird.")

