# -*- coding: utf-8 -*-

"""

算法实现：差异理论 / word_level_diff



本文件实现 word_level_diff 相关的算法功能。

"""



import re





class WordDiffResult:

    """

    单词级diff结果类

    """

    def __init__(self):

        self.operations = []  # 操作列表

    

    def add_operation(self, op_type, content):

        """

        添加一个操作

        

        参数:

            op_type: 'equal', 'insert', 'delete'

            content: 操作的内容

        """

        self.operations.append((op_type, content))

    

    def to_string(self, show_equal=True):

        """

        转换为可读字符串

        

        参数:

            show_equal: 是否显示相同的部分

        

        返回:

            格式化的字符串

        """

        result = []

        for op_type, content in self.operations:

            if op_type == 'equal' and not show_equal:

                continue

            elif op_type == 'insert':

                result.append(f"+{content}")

            elif op_type == 'delete':

                result.append(f"-{content}")

            else:

                result.append(f" {content}")

        return ' '.join(result)





def tokenize_text(text):

    """

    将文本拆分为单词列表

    

    使用正则表达式保留单词边界信息

    

    参数:

        text: 输入文本

    

    返回:

        单词列表

    """

    # 按单词边界分割，同时保留分隔符

    pattern = r'\S+|\s+'

    tokens = re.findall(pattern, text)

    return tokens





def compute_word_diff(text_a, text_b):

    """

    计算两个文本的单词级差异

    

    参数:

        text_a: 原始文本

        text_b: 新文本

    

    返回:

        WordDiffResult对象

    """

    # 词条化

    words_a = tokenize_text(text_a)

    words_b = tokenize_text(text_b)

    

    n = len(words_a)

    m = len(words_b)

    

    # 构建DP表

    dp = [[0] * (m + 1) for _ in range(n + 1)]

    

    for i in range(1, n + 1):

        for j in range(1, m + 1):

            if words_a[i - 1] == words_b[j - 1]:

                dp[i][j] = dp[i - 1][j - 1] + 1

            else:

                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    

    # 回溯构建diff

    result = WordDiffResult()

    i = n

    j = m

    

    while i > 0 or j > 0:

        if i > 0 and j > 0 and words_a[i - 1] == words_b[j - 1]:

            result.add_operation('equal', words_a[i - 1])

            i -= 1

            j -= 1

        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):

            result.add_operation('insert', words_b[j - 1])

            j -= 1

        else:

            result.add_operation('delete', words_a[i - 1])

            i -= 1

    

    result.operations.reverse()

    return result





def compute_inline_word_diff(words_a, words_b):

    """

    计算行内单词差异（用于一行内的单词比较）

    

    参数:

        words_a: 原始单词列表

        words_b: 新单词列表

    

    返回:

        差异操作列表

    """

    n = len(words_a)

    m = len(words_b)

    

    dp = [[0] * (m + 1) for _ in range(n + 1)]

    

    for i in range(1, n + 1):

        for j in range(1, m + 1):

            if words_a[i - 1] == words_b[j - 1]:

                dp[i][j] = dp[i - 1][j - 1] + 1

            else:

                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    

    operations = []

    i = n

    j = m

    

    while i > 0 or j > 0:

        if i > 0 and j > 0 and words_a[i - 1] == words_b[j - 1]:

            operations.append(('equal', words_a[i - 1]))

            i -= 1

            j -= 1

        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):

            operations.append(('insert', words_b[j - 1]))

            j -= 1

        else:

            operations.append(('delete', words_a[i - 1]))

            i -= 1

    

    operations.reverse()

    return operations





def diff_statistics(diff_result):

    """

    统计diff结果

    

    参数:

        diff_result: WordDiffResult对象

    

    返回:

        统计字典

    """

    stats = {

        'insertions': 0,

        'deletions': 0,

        'equal': 0,

        'total_changes': 0

    }

    

    inserted_words = []

    deleted_words = []

    

    for op_type, content in diff_result.operations:

        if op_type == 'insert':

            stats['insertions'] += 1

            inserted_words.append(content)

        elif op_type == 'delete':

            stats['deletions'] += 1

            deleted_words.append(content)

        else:

            stats['equal'] += 1

    

    stats['total_changes'] = stats['insertions'] + stats['deletions']

    stats['inserted_words'] = inserted_words

    stats['deleted_words'] = deleted_words

    

    return stats





def html_word_diff(text_a, text_b):

    """

    生成HTML格式的单词diff

    

    参数:

        text_a: 原始文本

        text_b: 新文本

    

    返回:

        HTML字符串

    """

    diff_result = compute_word_diff(text_a, text_b)

    

    html_parts = ['<div class="word-diff">']

    

    for op_type, content in diff_result.operations:

        if op_type == 'equal':

            html_parts.append(f'<span class="equal">{content}</span>')

        elif op_type == 'insert':

            html_parts.append(f'<span class="insert">{content}</span>')

        elif op_type == 'delete':

            html_parts.append(f'<span class="delete">{content}</span>')

    

    html_parts.append('</div>')

    

    return ''.join(html_parts)





def unified_word_diff(text_a, text_b, context=0):

    """

    生成统一格式的单词diff

    

    参数:

        text_a: 原始文本

        text_b: 新文本

        context: 上下文单词数

    

    返回:

        统一diff格式字符串

    """

    diff_result = compute_word_diff(text_a, text_b)

    

    lines = []

    lines.append("--- original")

    lines.append("+++ modified")

    

    # 构建变更块

    changes = []

    current_change = []

    

    for op_type, content in diff_result.operations:

        if op_type != 'equal':

            current_change.append((op_type, content))

        else:

            if current_change:

                changes.append(current_change)

                current_change = []

            current_change.append((op_type, content))

    

    if current_change:

        changes.append(current_change)

    

    # 输出变更块

    change_num = 1

    for change in changes:

        lines.append(f"@@ -{change_num} +{change_num} @@")

        

        for op_type, content in change:

            if op_type == 'insert':

                lines.append(f"+ {content}")

            elif op_type == 'delete':

                lines.append(f"- {content}")

            else:

                lines.append(f"  {content}")

        

        change_num += len([c for c in change if c[0] != 'equal'])

    

    return '\n'.join(lines)





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：基本单词diff

    print("=" * 50)

    print("测试1: 基本单词级diff")

    print("=" * 50)

    

    text_a = "The quick brown fox jumps"

    text_b = "The slow brown fox walks"

    

    result = compute_word_diff(text_a, text_b)

    print(f"原始: {text_a}")

    print(f"新:   {text_b}")

    print(f"\nDiff结果: {result.to_string()}")

    print(f"只显示变更: {result.to_string(show_equal=False)}")

    

    # 测试用例2：统计信息

    print("\n" + "=" * 50)

    print("测试2: Diff统计")

    print("=" * 50)

    

    stats = diff_statistics(result)

    print(f"插入: {stats['insertions']}")

    print(f"删除: {stats['deletions']}")

    print(f"相同: {stats['equal']}")

    print(f"总变更: {stats['total_changes']}")

    print(f"插入的词: {stats['inserted_words']}")

    print(f"删除的词: {stats['deleted_words']}")

    

    # 测试用例3：代码注释变更

    print("\n" + "=" * 50)

    print("测试3: 代码注释变更")

    print("=" * 50)

    

    comment_a = "/* This function calculates the sum of two numbers */"

    comment_b = "/* This function calculates the product of two numbers */"

    

    result = compute_word_diff(comment_a, comment_b)

    print(f"原注释: {comment_a}")

    print(f"新注释: {comment_b}")

    print(f"\nDiff: {result.to_string()}")

    

    # 测试用例4：自然语言文本

    print("\n" + "=" * 50)

    print("测试4: 自然语言文本diff")

    print("=" * 50)

    

    sentence_a = "I went to the store yesterday and bought some apples"

    sentence_b = "I went to the market yesterday and bought some oranges"

    

    result = compute_word_diff(sentence_a, sentence_b)

    print(f"原文: {sentence_a}")

    print(f"新文: {sentence_b}")

    print(f"\n变化: {result.to_string(show_equal=False)}")

    

    # 测试用例5：统一格式输出

    print("\n" + "=" * 50)

    print("测试5: 统一格式输出")

    print("=" * 50)

    

    text_a = "one two three"

    text_b = "one four three"

    

    unified = unified_word_diff(text_a, text_b)

    print(unified)

    

    # 测试用例6：HTML格式输出

    print("\n" + "=" * 50)

    print("测试6: HTML格式输出")

    print("=" * 50)

    

    text_a = "Hello world"

    text_b = "Hello there"

    

    html = html_word_diff(text_a, text_b)

    print("HTML输出:")

    print(html)

