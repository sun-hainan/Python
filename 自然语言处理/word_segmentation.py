# -*- coding: utf-8 -*-

"""

算法实现：自然语言处理 / word_segmentation



本文件实现 word_segmentation 相关的算法功能。

"""



from typing import List, Set, Optional





class Dictionary:

    """

    词典类

    """

    

    def __init__(self):

        self.words: Set[str] = set()

        self.max_word_length: int = 0

    

    def add_word(self, word: str):

        """

        添加单词到词典

        

        参数:

            word: 要添加的词

        """

        self.words.add(word)

        self.max_word_length = max(self.max_word_length, len(word))

    

    def add_words(self, words: List[str]):

        """

        批量添加单词

        

        参数:

            words: 单词列表

        """

        for word in words:

            self.add_word(word)

    

    def contains(self, word: str) -> bool:

        """

        检查词是否在词典中

        

        参数:

            word: 要检查的词

        

        返回:

            是否存在

        """

        return word in self.words

    

    def get_max_length(self) -> int:

        """

        获取词典中最长词的长度

        

        返回:

            最长词长度

        """

        return self.max_word_length





class ForwardMaximumMatching:

    """

    正向最大匹配算法

    """

    

    def __init__(self, dictionary: Dictionary):

        """

        初始化

        

        参数:

            dictionary: 词典

        """

        self.dictionary = dictionary

    

    def segment(self, text: str) -> List[str]:

        """

        对文本进行分词

        

        参数:

            text: 输入文本

        

        返回:

            分词结果列表

        """

        result = []

        position = 0

        text_length = len(text)

        

        while position < text_length:

            # 从当前位置开始，最多匹配max_length个字符

            max_len = min(

                self.dictionary.get_max_length(),

                text_length - position

            )

            

            matched = False

            

            # 从长到短尝试匹配

            for length in range(max_len, 0, -1):

                word = text[position:position + length]

                

                if self.dictionary.contains(word):

                    result.append(word)

                    position += length

                    matched = True

                    break

            

            # 如果没有匹配到词（单字不成词）

            if not matched:

                # 尝试单字符

                word = text[position]

                result.append(word)

                position += 1

        

        return result





class BackwardMaximumMatching:

    """

    反向最大匹配算法

    """

    

    def __init__(self, dictionary: Dictionary):

        """

        初始化

        

        参数:

            dictionary: 词典

        """

        self.dictionary = dictionary

    

    def segment(self, text: str) -> List[str]:

        """

        对文本进行反向分词

        

        参数:

            text: 输入文本

        

        返回:

            分词结果列表

        """

        result = []

        position = len(text)

        

        while position > 0:

            max_len = min(

                self.dictionary.get_max_length(),

                position

            )

            

            matched = False

            

            for length in range(max_len, 0, -1):

                start = position - length

                word = text[start:position]

                

                if self.dictionary.contains(word):

                    result.insert(0, word)

                    position = start

                    matched = True

                    break

            

            if not matched:

                result.insert(0, text[position - 1])

                position -= 1

        

        return result





class BidirectionalMaximumMatching:

    """

    双向最大匹配算法

    """

    

    def __init__(self, dictionary: Dictionary):

        """

        初始化

        

        参数:

            dictionary: 词典

        """

        self.fmm = ForwardMaximumMatching(dictionary)

        self.bmm = BackwardMaximumMatching(dictionary)

        self.dictionary = dictionary

    

    def segment(self, text: str) -> List[str]:

        """

        对文本进行双向最大匹配分词

        

        参数:

            text: 输入文本

        

        返回:

            分词结果列表

        """

        # 正向最大匹配

        fmm_result = self.fmm.segment(text)

        

        # 反向最大匹配

        bmm_result = self.bmm.segment(text)

        

        # 选择最佳结果

        return self._choose_best(fmm_result, bmm_result, text)

    

    def _choose_best(self, fmm_result: List[str], 

                    bmm_result: List[str], 

                    text: str) -> List[str]:

        """

        选择最佳分词结果

        

        策略：

        1. 如果结果相同，返回任一个

        2. 否则选择词数少的

        3. 如果词数相同，选择单字词少的

        4. 如果还相同，选择词典覆盖率高的

        

        参数:

            fmm_result: 正向匹配结果

            bmm_result: 反向匹配结果

            text: 原始文本

        

        返回:

            最佳分词结果

        """

        # 如果结果相同

        if fmm_result == bmm_result:

            return fmm_result

        

        # 计算各种统计

        fmm_stats = self._compute_stats(fmm_result)

        bmm_stats = self._compute_stats(bmm_result)

        

        # 规则1：词数少优先

        if fmm_stats['word_count'] < bmm_stats['word_count']:

            return fmm_result

        if bmm_stats['word_count'] < fmm_stats['word_count']:

            return bmm_result

        

        # 规则2：单字词少优先

        if fmm_stats['single_char_count'] < bmm_stats['single_char_count']:

            return fmm_result

        if bmm_stats['single_char_count'] < fmm_stats['single_char_count']:

            return bmm_result

        

        # 规则3：词典覆盖率高优先

        if fmm_stats['coverage'] > bmm_stats['coverage']:

            return fmm_result

        elif bmm_stats['coverage'] > fmm_stats['coverage']:

            return bmm_result

        

        # 无法区分，返回正向结果

        return fmm_result

    

    def _compute_stats(self, words: List[str]) -> dict:

        """

        计算分词结果的统计信息

        

        参数:

            words: 分词结果

        

        返回:

            统计字典

        """

        word_count = len(words)

        single_char_count = sum(1 for w in words if len(w) == 1)

        in_dict_count = sum(1 for w in words if self.dictionary.contains(w))

        coverage = in_dict_count / word_count if word_count > 0 else 0

        

        return {

            'word_count': word_count,

            'single_char_count': single_char_count,

            'in_dict_count': in_dict_count,

            'coverage': coverage

        }





def create_sample_dictionary() -> Dictionary:

    """

    创建示例词典

    

    返回:

        填充好的词典

    """

    dictionary = Dictionary()

    

    sample_words = [

        '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安',

        '大学生', '大学', '学生', '生', '学习', '研', '研究', '生物学',

        '生物', '物', '计算机', '计算', '算机', '软件', '工程师', '开发',

        '自然', '自然语言', '语言', '语言处理', '处理', '分词', '词',

        '我们', '你们', '他们', '大家', '人', '民', '人民', '共和国',

        '今天', '天气', '天气很好', '很', '好', '是', '不是', '的',

        '我', '爱', '中国', '中国有', '有', '五', '五千', '千年', '年',

    ]

    

    dictionary.add_words(sample_words)

    

    return dictionary





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：基本分词

    print("=" * 50)

    print("测试1: 基本分词")

    print("=" * 50)

    

    dictionary = create_sample_dictionary()

    

    segmenter = BidirectionalMaximumMatching(dictionary)

    

    test_texts = [

        "北京大学生物系研究自然语言处理",

        "计算机软件工程师开发自然语言处理软件",

        "今天天气很好",

        "我爱中国",

    ]

    

    for text in test_texts:

        fmm = ForwardMaximumMatching(dictionary)

        bmm = BackwardMaximumMatching(dictionary)

        

        fmm_result = fmm.segment(text)

        bmm_result = bmm.segment(text)

        best_result = segmenter.segment(text)

        

        print(f"\n原文: {text}")

        print(f"  正向: {' / '.join(fmm_result)}")

        print(f"  反向: {' / '.join(bmm_result)}")

        print(f"  双向: {' / '.join(best_result)}")

    

    # 测试用例2：词典管理

    print("\n" + "=" * 50)

    print("测试2: 词典操作")

    print("=" * 50)

    

    dictionary = Dictionary()

    

    # 添加词

    dictionary.add_word("计算机")

    dictionary.add_word("科学")

    dictionary.add_word("计算")

    

    print(f"词典最大词长: {dictionary.get_max_length()}")

    print(f"'计算机' 是否在词典: {dictionary.contains('计算机')}")

    print(f"'电脑' 是否在词典: {dictionary.contains('电脑')}")

    

    # 测试用例3：未知词处理

    print("\n" + "=" * 50)

    print("测试3: 未知词处理")

    print("=" * 50)

    

    dictionary = create_sample_dictionary()

    segmenter = BidirectionalMaximumMatching(dictionary)

    

    # 包含未知词的文本

    text_with_unknown = "我喜欢用计算机进行量子编程"

    

    result = segmenter.segment(text_with_unknown)

    print(f"原文: {text_with_unknown}")

    print(f"分词: {' / '.join(result)}")

    

    # 测试用例4：纯单字符文本

    print("\n" + "=" * 50)

    print("测试4: 纯单字符文本")

    print("=" * 50)

    

    text = "ABCDEF"

    result = segmenter.segment(text)

    print(f"原文: {text}")

    print(f"分词: {' / '.join(result)}")

    

    # 测试用例5：空文本

    print("\n" + "=" * 50)

    print("测试5: 空文本处理")

    print("=" * 50)

    

    text = ""

    result = segmenter.segment(text)

    print(f"原文: '{text}'")

    print(f"分词: {result}")

    

    # 测试用例6：统计信息

    print("\n" + "=" * 50)

    print("测试6: 分词统计")

    print("=" * 50)

    

    dictionary = create_sample_dictionary()

    segmenter = BidirectionalMaximumMatching(dictionary)

    

    text = "自然语言处理是计算机科学的重要研究领域"

    result = segmenter.segment(text)

    

    stats = segmenter._compute_stats(result)

    print(f"原文: {text}")

    print(f"分词: {' / '.join(result)}")

    print(f"统计:")

    print(f"  词数: {stats['word_count']}")

    print(f"  单字词数: {stats['single_char_count']}")

    print(f"  词典覆盖: {stats['coverage']:.2%}")

