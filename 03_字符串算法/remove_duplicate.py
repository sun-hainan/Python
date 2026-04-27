# -*- coding: utf-8 -*-

"""

算法实现：03_字符串算法 / remove_duplicate



本文件实现 remove_duplicate 相关的算法功能。

"""



from typing import Set





def remove_duplicate_chars(s: str) -> str:

    """

    删除重复字符



    参数：

        s: 输入字符串



    返回：删除重复后的字符串



    复杂度：时间O(n)，空间O(字符集大小)

    """

    seen: Set[str] = set()

    result = []



    for char in s:

        if char not in seen:

            seen.add(char)

            result.append(char)



    return ''.join(result)





def remove_duplicate_chars_in_place(s: str) -> int:

    """

    原地版本（数组思维）



    返回：不同字符的数量

    """

    if not s:

        return 0



    char_list = list(s)

    n = len(char_list)



    # 用整数数组模拟

    seen = [False] * 256  # 假设ASCII字符



    write_idx = 0



    for i in range(n):

        char_val = ord(char_list[i])

        if not seen[char_val]:

            seen[char_val] = True

            if write_idx != i:

                char_list[write_idx] = char_list[i]

            write_idx += 1



    return write_idx





def remove_duplicate_sorted(s: str) -> str:

    """

    如果字符串已排序，更简单



    参数：

        s: 已排序的字符串



    返回：结果字符串

    """

    if not s:

        return s



    result = [s[0]]



    for i in range(1, len(s)):

        if s[i] != s[i - 1]:

            result.append(s[i])



    return ''.join(result)





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    test_cases = [

        "abcabc",

        "aaaaaaaa",

        "abcdef",

        "AaBbCc",

        "",

        "aaaaabbbbbcccccaaaa",

    ]



    print("=== 删除重复字符测试 ===\n")



    for s in test_cases:

        result1 = remove_duplicate_chars(s)

        result2 = remove_duplicate_chars_in_place(s)



        print(f"输入: '{s}'")

        print(f"输出: '{result1}'")

        print()



    print("复杂度分析：")

    print("  时间复杂度: O(n)")

    print("  空间复杂度: O(min(n, 字符集))")

    print()

    print("说明：")

    print("  - 哈希表法是标准解法")

    print("  - 原地版本需要额外数组模拟")

    print("  - 如果字符集有限（如26个字母），可用位运算优化")

