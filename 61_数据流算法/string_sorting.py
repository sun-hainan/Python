# -*- coding: utf-8 -*-

"""

算法实现：数据流算法 / string_sorting



本文件实现 string_sorting 相关的算法功能。

"""



from typing import List





class StringSorter:

    """字符串排序器"""



    def __init__(self, alphabet_size: int = 256):

        """

        参数：

            alphabet_size: 字符集大小

        """

        self.alphabet = alphabet_size



    def msd_sort(self, strings: List[str]) -> List[str]:

        """

        MSD排序



        参数：

            strings: 字符串列表



        返回：排序后的字符串

        """

        if not strings:

            return []



        # 找最大长度

        max_len = max(len(s) for s in strings)



        # 递归排序

        return self._msd_recursive(strings, 0, max_len)



    def _msd_recursive(self, strings: List[str],

                      char_index: int, max_len: int) -> List[str]:

        """MSD递归"""

        if char_index >= max_len or len(strings) <= 1:

            return sorted(strings)



        # 桶

        buckets = [[] for _ in range(self.alphabet + 1)]



        # 分配

        for s in strings:

            if char_index < len(s):

                char = ord(s[char_index])

                buckets[char].append(s)

            else:

                buckets[self.alphabet].append(s)



        # 递归排序每个桶

        result = []

        for bucket in buckets:

            if bucket:

                if len(bucket) > 1:

                    sorted_bucket = self._msd_recursive(bucket, char_index + 1, max_len)

                    result.extend(sorted_bucket)

                else:

                    result.extend(bucket)



        return result



    def three_way_radix_quicksort(self, strings: List[str]) -> List[str]:

        """

        三路基数快速排序



        参数：

            strings: 字符串列表



        返回：排序后的字符串

        """

        self._three_way_quicksort(strings, 0, len(strings) - 1, 0)

        return strings



    def _three_way_quicksort(self, strings: List[str],

                            low: int, high: int, d: int) -> None:

        """三路快速排序"""

        if high <= low:

            return



        # 三路划分

        left = low

        right = high

        pivot_char = ord(strings[low][d]) if d < len(strings[low]) else -1



        i = low + 1

        while i <= right:

            char = ord(strings[i][d]) if d < len(strings[i]) else -1



            if char < pivot_char:

                strings[left], strings[i] = strings[i], strings[left]

                left += 1

                i += 1

            elif char > pivot_char:

                strings[i], strings[right] = strings[right], strings[i]

                right -= 1

            else:

                i += 1



        # 递归

        self._three_way_quicksort(strings, low, left - 1, d)



        if pivot_char >= 0:

            self._three_way_quicksort(strings, left, right, d + 1)



        self._three_way_quicksort(strings, right + 1, high, d)





def string_sorting_complexity():

    """字符串排序复杂度"""

    print("=== 字符串排序复杂度 ===")

    print()

    print("MSD排序：")

    print("  - 时间：O(nw + σ)")

    print("  - w 是平均字符串长度")

    print("  - σ 是字符集大小")

    print()

    print("三路快排：")

    print("  - 更好地处理公共前缀")

    print("  - 更小的递归栈")

    print()

    print("实际性能：")

    print("  - 小字符串：快排更好")

    print("  - 大字符串：MSD更好")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 字符串排序测试 ===\n")



    # 测试字符串

    strings = ["banana", "apple", "cherry", "date", "elderberry", "fig", "grape"]



    sorter = StringSorter()



    print(f"原始: {strings}")

    print()



    # MSD排序

    sorted_msd = sorter.msd_sort(strings.copy())

    print(f"MSD排序: {sorted_msd}")



    # 三路快排

    sorted_3way = sorter.three_way_radix_quicksort(strings.copy())

    print(f"三路快排: {sorted_3way}")



    print()

    string_sorting_complexity()



    print()

    print("说明：")

    print("  - MSD适合字符串排序")

    print("  - 三路划分处理重复前缀更好")

    print("  - 是基数排序的变体")

