# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / rail_fence_cipher

本文件实现 rail_fence_cipher 相关的算法功能。
"""

# encrypt 函数实现
def encrypt(input_string: str, key: int) -> str:
    """
    Shuffles the character of a string by placing each of them
    in a grid (the height is dependent on the key) in a zigzag
    formation and reading it left to right.

    >>> encrypt("Hello World", 4)
    'HWe olordll'

    >>> encrypt("This is a message", 0)
    Traceback (most recent call last):
        ...
    ValueError: Height of grid can't be 0 or negative

    >>> encrypt(b"This is a byte string", 5)
    Traceback (most recent call last):
        ...
    TypeError: sequence item 0: expected str instance, int found
    """
    temp_grid: list[list[str]] = [[] for _ in range(key)]
    lowest = key - 1

    if key <= 0:
    # 条件判断
        raise ValueError("Height of grid can't be 0 or negative")
    if key == 1 or len(input_string) <= key:
    # 条件判断
        return input_string
    # 返回结果

    for position, character in enumerate(input_string):
    # 遍历循环
        num = position % (lowest * 2)  # puts it in bounds
        num = min(num, lowest * 2 - num)  # creates zigzag pattern
        temp_grid[num].append(character)
    grid = ["".join(row) for row in temp_grid]
    output_string = "".join(grid)

    return output_string
    # 返回结果



# decrypt 函数实现
def decrypt(input_string: str, key: int) -> str:
    """
    Generates a template based on the key and fills it in with
    the characters of the input string and then reading it in
    a zigzag formation.

    >>> decrypt("HWe olordll", 4)
    'Hello World'

    >>> decrypt("This is a message", -10)
    Traceback (most recent call last):
        ...
    ValueError: Height of grid can't be 0 or negative

    >>> decrypt("My key is very big", 100)
    'My key is very big'
    """
    grid = []
    lowest = key - 1

    if key <= 0:
    # 条件判断
        raise ValueError("Height of grid can't be 0 or negative")
    if key == 1:
    # 条件判断
        return input_string
    # 返回结果

    temp_grid: list[list[str]] = [[] for _ in range(key)]  # generates template
    for position in range(len(input_string)):
    # 遍历循环
        num = position % (lowest * 2)  # puts it in bounds
        num = min(num, lowest * 2 - num)  # creates zigzag pattern
        temp_grid[num].append("*")

    counter = 0
    for row in temp_grid:  # fills in the characters
    # 遍历循环
        splice = input_string[counter : counter + len(row)]
        grid.append(list(splice))
        counter += len(row)

    output_string = ""  # reads as zigzag
    for position in range(len(input_string)):
    # 遍历循环
        num = position % (lowest * 2)  # puts it in bounds
        num = min(num, lowest * 2 - num)  # creates zigzag pattern
        output_string += grid[num][0]
        grid[num].pop(0)
    return output_string
    # 返回结果



# bruteforce 函数实现
def bruteforce(input_string: str) -> dict[int, str]:
    """Uses decrypt function by guessing every key

    >>> bruteforce("HWe olordll")[4]
    'Hello World'
    """
    results = {}
    for key_guess in range(1, len(input_string)):  # tries every key
    # 遍历循环
        results[key_guess] = decrypt(input_string, key_guess)
    return results
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
