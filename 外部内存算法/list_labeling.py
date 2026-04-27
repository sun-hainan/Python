# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / list_labeling



本文件实现 list_labeling 相关的算法功能。

"""



from typing import List





class ListLabeling:

    """列表标记算法"""



    def __init__(self, n: int):

        """

        参数：

            n: 元素总数

        """

        self.n = n



    def label_with_gaps(self, elements: List,

                       block_size: int = 1000) -> List[int]:

        """

        使用间隙标记



        参数：

            elements: 元素列表

            block_size: 每块大小



        返回：标签列表

        """

        n = len(elements)

        labels = [0] * n



        # 预留间隙

        gap = max(1, n // 100)



        label = 1

        for i in range(n):

            labels[i] = label

            label += gap



        return labels



    def relabel_with_small_labels(self, elements: List,

                                current_labels: List[int]) -> List[int]:

        """

        重标记使用小标签



        参数：

            elements: 元素

            current_labels: 当前标签



        返回：新标签

        """

        # 保持相对顺序

        order = sorted(range(len(elements)),

                      key=lambda i: current_labels[i])



        new_labels = [0] * len(elements)



        for rank, idx in enumerate(order):

            new_labels[idx] = rank + 1



        return new_labels



    def verify_labeling(self, labels: List[int]) -> bool:

        """

        验证标签有效性



        返回：是否有效

        """

        n = len(labels)



        # 检查范围

        for label in labels:

            if label < 1 or label > n:

                return False



        # 检查唯一性

        if len(set(labels)) != n:

            return False



        # 检查顺序性

        for i in range(n - 1):

            if labels[i] >= labels[i + 1]:

                return False



        return True





def list_labeling_complexity():

    """列表标记复杂度"""

    print("=== 列表标记复杂度 ===")

    print()

    print("问题：")

    print("  - 标签范围 [1, n]")

    print("  - 保持相对顺序")

    print("  - O(1) 的标签间隙")

    print()

    print("算法：")

    print("  - 桶分配：O(n)")

    print("  - 分布式：O(n/B) I/O")

    print()

    print("应用：")

    print("  - 数据库记录ID")

    print("  - 文件系统inode")

    print("  - 图节点标记")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 列表标记测试 ===\n")



    # 创建标记器

    n = 10000

    labeler = ListLabeling(n)



    # 模拟元素

    elements = list(range(n))



    # 使用间隙标记

    labels = labeler.label_with_gaps(elements, block_size=1000)



    print(f"元素数: {n}")

    print(f"标签范围: [{min(labels)}, {max(labels)}]")

    print(f"前10个标签: {labels[:10]}")

    print(f"后10个标签: {labels[-10:]}")

    print()



    # 验证

    is_valid = labeler.verify_labeling(labels)

    print(f"标签有效: {'✅ 是' if is_valid else '❌ 否'}")

    print()



    # 重标记

    print("重标记（压缩）：")

    new_labels = labeler.relabel_with_small_labels(elements, labels)



    print(f"新标签范围: [{min(new_labels)}, {max(new_labels)}]")

    print(f"前10个新标签: {new_labels[:10]}")



    is_valid = labeler.verify_labeling(new_labels)

    print(f"新标签有效: {'✅ 是' if is_valid else '❌ 否'}")



    print()

    list_labeling_complexity()



    print()

    print("说明：")

    print("  - 列表标记用于给元素分配唯一ID")

    print("  - 保持顺序很重要")

    print("  - 外部存储需要特殊处理")

