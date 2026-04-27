# -*- coding: utf-8 -*-

"""

算法实现：03_字符串算法 / reverse_words



本文件实现 reverse_words 相关的算法功能。

"""



import re





def reverse_words_basic(s: str) -> str:

    """

    基础版本



    参数：

        s: 输入字符串



    返回：单词顺序反转后的字符串

    """

    # 分割成单词

    words = s.split()



    # 反转

    words.reverse()



    # 拼接

    return ' '.join(words)





def reverse_words_in_place(s: str) -> str:

    """

    原地翻转（两次反转法）



    思路：

    1. 先反转整个字符串

    2. 再逐个反转每个单词



    参数：

        s: 输入字符串



    返回：单词顺序反转后的字符串

    """

    char_list = list(s)



    n = len(char_list)



    # Step 1: 反转整个字符串

    left, right = 0, n - 1

    while left < right:

        char_list[left], char_list[right] = char_list[right], char_list[left]

        left += 1

        right -= 1



    # Step 2: 逐个反转每个单词

    start = 0

    while start < n:

        # 找到单词结束位置

        end = start

        while end < n and char_list[end] != ' ':

            end += 1



        # 反转这个单词

        left, right = start, end - 1

        while left < right:

            char_list[left], char_list[right] = char_list[right], char_list[left]

            left += 1

            right -= 1



        # 移动到下一个单词

        start = end + 1



    return ''.join(char_list)





def reverse_words_regex(s: str) -> str:

    """

    正则表达式版本



    参数：

        s: 输入字符串



    返回：单词顺序反转后的字符串

    """

    words = re.findall(r'\S+', s)

    return ' '.join(reversed(words))





def handle_multiple_spaces(s: str) -> str:

    """

    处理多个空格的情况



    参数：

        s: 可能包含多个空格的字符串



    返回：规范化后的结果

    """

    # 使用正则删除多余空格

    s = re.sub(r'\s+', ' ', s)

    s = s.strip()



    words = s.split(' ')

    words.reverse()



    return ' '.join(words)





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    test_cases = [

        "Hello World",

        "  Hello   World  ",

        "Python isAwesome",

        "single",

        "",

        "   spaces   between   words   ",

        "123 456 789",

    ]



    print("=== 翻转单词顺序测试 ===\n")



    for s in test_cases:

        result1 = reverse_words_basic(s)

        result2 = reverse_words_in_place(s)

        result3 = reverse_words_regex(s)



        print(f"输入: '{s}'")

        print(f"基础版: '{result1}'")

        print(f"原地版: '{result2}'")

        print(f"正则版: '{result3}'")

        print()



    print("算法对比：")

    print("  基础版: 简洁直观，O(n)时间和空间")

    print("  原地版: 两次反转，O(1)额外空间")

    print("  正则版: 代码最简，但可能有性能开销")

    print()

    print("实际应用：")

    print("  - 文本编辑器'逆转字符串'功能")

    print("  - 日志分析（最新时间在前）")

    print("  - 自然语言处理")

