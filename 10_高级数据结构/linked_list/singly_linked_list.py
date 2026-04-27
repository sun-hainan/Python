# -*- coding: utf-8 -*-

"""

算法实现：linked_list / singly_linked_list



本文件实现 singly_linked_list 相关的算法功能。

"""



from __future__ import annotations

from collections.abc import Iterator

from dataclasses import dataclass

from typing import Any





@dataclass

class Node:

    """链表节点"""

    data: Any

    next_node: Node | None = None



    def __repr__(self):

        return f"Node({self.data})"





class LinkedList:

    """单链表"""



    def __init__(self):

        self.head: Node | None = None



    def __iter__(self) -> Iterator[Any]:

        """迭代器：遍历链表所有节点的数据"""

        node = self.head

        while node:

            yield node.data

            node = node.next_node



    def __len__(self) -> int:

        """返回链表长度"""

        return sum(1 for _ in self)



    def __repr__(self) -> str:

        """链表的可视化表示"""

        return " -> ".join([str(item) for item in self])



    def __getitem__(self, index: int) -> Any:

        """按索引访问节点"""

        if not 0 <= index < len(self):

            raise ValueError("list index out of range.")

        for i, node in enumerate(self):

            if i == index:

                return node



    def __setitem__(self, index: int, data: Any) -> None:

        """按索引修改节点数据"""

        if not 0 <= index < len(self):

            raise ValueError("list index out of range.")

        current = self.head

        for _ in range(index):

            current = current.next_node

        current.data = data



    # ========== 插入操作 ==========



    def insert_tail(self, data: Any) -> None:

        """尾部插入 O(n)"""

        self.insert_nth(len(self), data)



    def insert_head(self, data: Any) -> None:

        """头部插入 O(1)"""

        self.insert_nth(0, data)



    def insert_nth(self, index: int, data: Any) -> None:

        """在指定位置插入"""

        if not 0 <= index <= len(self):

            raise IndexError("list index out of range")

        new_node = Node(data)

        if self.head is None:

            self.head = new_node

        elif index == 0:

            new_node.next_node = self.head

            self.head = new_node

        else:

            temp = self.head

            for _ in range(index - 1):

                temp = temp.next_node

            new_node.next_node = temp.next_node

            temp.next_node = new_node



    # ========== 删除操作 ==========



    def delete_head(self) -> Any:

        """删除头部节点 O(1)"""

        return self.delete_nth(0)



    def delete_tail(self) -> Any:

        """删除尾部节点 O(n)"""

        return self.delete_nth(len(self) - 1)



    def delete_nth(self, index: int = 0) -> Any:

        """删除指定位置节点"""

        if not 0 <= index <= len(self) - 1:

            raise IndexError("List index out of range.")

        delete_node = self.head

        if index == 0:

            self.head = self.head.next_node

        else:

            temp = self.head

            for _ in range(index - 1):

                temp = temp.next_node

            delete_node = temp.next_node

            temp.next_node = temp.next_node.next_node

        return delete_node.data



    # ========== 其他操作 ==========



    def is_empty(self) -> bool:

        """检查链表是否为空"""

        return self.head is None



    def reverse(self) -> None:

        """

        反转链表 O(n)



        思路：三个指针 prev, current, next_node

        遍历时反转每个节点的 next 指针

        """

        prev = None

        current = self.head

        while current:

            next_node = current.next_node  # 保存下一个节点

            current.next_node = prev        # 反转指针

            prev = current                 # prev 前移

            current = next_node            # current 前移

        self.head = prev





def test_singly_linked_list() -> None:

    """测试链表基本功能"""

    linked_list = LinkedList()



    # 测试插入

    for i in range(10):

        linked_list.insert_nth(i, i + 1)

    print(f"插入10个元素: {linked_list}")



    # 测试头尾插入

    linked_list.insert_head(0)

    linked_list.insert_tail(11)

    print(f"头尾插入: {linked_list}")



    # 测试删除

    linked_list.delete_head()

    linked_list.delete_tail()

    print(f"删除头尾: {linked_list}")



    # 测试反转

    linked_list.reverse()

    print(f"反转后: {linked_list}")



    # 测试索引

    print(f"第3个元素: {linked_list[3]}")





if __name__ == "__main__":

    test_singly_linked_list()

