# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / skip_list



本文件实现 skip_list 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""





"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""









from itertools import pairwise

from random import random

from typing import TypeVar



KT = TypeVar("KT")

VT = TypeVar("VT")







# =============================================================================

# 算法模块：test_insert

# =============================================================================

class Node[KT, VT]:

    # Node class



    # Node class

    def __init__(self, key: KT | str = "root", value: VT | None = None):

    # __init__ function



    # __init__ function

        self.key = key

        self.value = value

        self.forward: list[Node[KT, VT]] = []



    def __repr__(self) -> str:

    # __repr__ function



    # __repr__ function

        """

        :return: Visual representation of Node



        >>> node = Node("Key", 2)

        >>> repr(node)

        'Node(Key: 2)'

        """



        return f"Node({self.key}: {self.value})"



    @property

    def level(self) -> int:

    # level function



    # level function

        """

        :return: Number of forward references



        >>> node = Node("Key", 2)

        >>> node.level

        0

        >>> node.forward.append(Node("Key2", 4))

        >>> node.level

        1

        >>> node.forward.append(Node("Key3", 6))

        >>> node.level

        2

        """



        return len(self.forward)





class SkipList[KT, VT]:

    # SkipList class



    # SkipList class

    def __init__(self, p: float = 0.5, max_level: int = 16):

    # __init__ function



    # __init__ function

        self.head: Node[KT, VT] = Node[KT, VT]()

        self.level = 0

        self.p = p

        self.max_level = max_level



    def __str__(self) -> str:

    # __str__ function



    # __str__ function

        """

        :return: Visual representation of SkipList



        >>> skip_list = SkipList()

        >>> print(skip_list)

        SkipList(level=0)

        >>> skip_list.insert("Key1", "Value")

        >>> print(skip_list) # doctest: +ELLIPSIS

        SkipList(level=...

        [root]--...

        [Key1]--Key1...

        None    *...

        >>> skip_list.insert("Key2", "OtherValue")

        >>> print(skip_list) # doctest: +ELLIPSIS

        SkipList(level=...

        [root]--...

        [Key1]--Key1...

        [Key2]--Key2...

        None    *...

        """



        items = list(self)



        if len(items) == 0:

            return f"SkipList(level={self.level})"



        label_size = max((len(str(item)) for item in items), default=4)

        label_size = max(label_size, 4) + 4



        node = self.head

        lines = []



        forwards = node.forward.copy()

        lines.append(f"[{node.key}]".ljust(label_size, "-") + "* " * len(forwards))

        lines.append(" " * label_size + "| " * len(forwards))



        while len(node.forward) != 0:

            node = node.forward[0]



            lines.append(

                f"[{node.key}]".ljust(label_size, "-")

                + " ".join(str(n.key) if n.key == node.key else "|" for n in forwards)

            )

            lines.append(" " * label_size + "| " * len(forwards))

            forwards[: node.level] = node.forward



        lines.append("None".ljust(label_size) + "* " * len(forwards))

        return f"SkipList(level={self.level})\n" + "\n".join(lines)



    def __iter__(self):

    # __iter__ function



    # __iter__ function

        node = self.head



        while len(node.forward) != 0:

            yield node.forward[0].key

            node = node.forward[0]



    def random_level(self) -> int:

    # random_level function



    # random_level function

        """

        :return: Random level from [1, self.max_level] interval.

                 Higher values are less likely.

        """



        level = 1

        while random() < self.p and level < self.max_level:

            level += 1



        return level



    def _locate_node(self, key) -> tuple[Node[KT, VT] | None, list[Node[KT, VT]]]:

    # _locate_node function



    # _locate_node function

        """

        :param key: Searched key,

        :return: Tuple with searched node (or None if given key is not present)

                 and list of nodes that refer (if key is present) of should refer to

                 given node.

        """



        # Nodes with refer or should refer to output node

        update_vector = []



        node = self.head



        for i in reversed(range(self.level)):

            # i < node.level - When node level is lesser than `i` decrement `i`.

            # node.forward[i].key < key - Jumping to node with key value higher

            #                             or equal to searched key would result

            #                             in skipping searched key.

            while i < node.level and node.forward[i].key < key:

                node = node.forward[i]

            # Each leftmost node (relative to searched node) will potentially have to

            # be updated.

            update_vector.append(node)



        update_vector.reverse()  # Note that we were inserting values in reverse order.



        # len(node.forward) != 0 - If current node doesn't contain any further

        #                          references then searched key is not present.

        # node.forward[0].key == key - Next node key should be equal to search key

        #                              if key is present.

        if len(node.forward) != 0 and node.forward[0].key == key:

            return node.forward[0], update_vector

        else:

            return None, update_vector



    def delete(self, key: KT):

    # delete function



    # delete function

        """

        :param key: Key to remove from list.



        >>> skip_list = SkipList()

        >>> skip_list.insert(2, "Two")

        >>> skip_list.insert(1, "One")

        >>> skip_list.insert(3, "Three")

        >>> list(skip_list)

        [1, 2, 3]

        >>> skip_list.delete(2)

        >>> list(skip_list)

        [1, 3]

        """



        node, update_vector = self._locate_node(key)



        if node is not None:

            for i, update_node in enumerate(update_vector):

                # Remove or replace all references to removed node.

                if update_node.level > i and update_node.forward[i].key == key:

                    if node.level > i:

                        update_node.forward[i] = node.forward[i]

                    else:

                        update_node.forward = update_node.forward[:i]



    def insert(self, key: KT, value: VT):

    # insert function



    # insert function

        """

        :param key: Key to insert.

        :param value: Value associated with given key.



        >>> skip_list = SkipList()

        >>> skip_list.insert(2, "Two")

        >>> skip_list.find(2)

        'Two'

        >>> list(skip_list)

        [2]

        """



        node, update_vector = self._locate_node(key)

        if node is not None:

            node.value = value

        else:

            level = self.random_level()



            if level > self.level:

                # After level increase we have to add additional nodes to head.

                for _ in range(self.level - 1, level):

                    update_vector.append(self.head)

                self.level = level



            new_node = Node(key, value)



            for i, update_node in enumerate(update_vector[:level]):

                # Change references to pass through new node.

                if update_node.level > i:

                    new_node.forward.append(update_node.forward[i])



                if update_node.level < i + 1:

                    update_node.forward.append(new_node)

                else:

                    update_node.forward[i] = new_node



    def find(self, key: VT) -> VT | None:

    # find function



    # find function

        """

        :param key: Search key.

        :return: Value associated with given key or None if given key is not present.



        >>> skip_list = SkipList()

        >>> skip_list.find(2)

        >>> skip_list.insert(2, "Two")

        >>> skip_list.find(2)

        'Two'

        >>> skip_list.insert(2, "Three")

        >>> skip_list.find(2)

        'Three'

        """



        node, _ = self._locate_node(key)



        if node is not None:

            return node.value



        return None





def test_insert():

    # test_insert function



    # test_insert function

    skip_list = SkipList()

    skip_list.insert("Key1", 3)

    skip_list.insert("Key2", 12)

    skip_list.insert("Key3", 41)

    skip_list.insert("Key4", -19)



    node = skip_list.head

    all_values = {}

    while node.level != 0:

        node = node.forward[0]

        all_values[node.key] = node.value



    assert len(all_values) == 4

    assert all_values["Key1"] == 3

    assert all_values["Key2"] == 12

    assert all_values["Key3"] == 41

    assert all_values["Key4"] == -19





def test_insert_overrides_existing_value():

    # test_insert_overrides_existing_value function



    # test_insert_overrides_existing_value function

    skip_list = SkipList()

    skip_list.insert("Key1", 10)

    skip_list.insert("Key1", 12)



    skip_list.insert("Key5", 7)

    skip_list.insert("Key7", 10)

    skip_list.insert("Key10", 5)



    skip_list.insert("Key7", 7)

    skip_list.insert("Key5", 5)

    skip_list.insert("Key10", 10)



    node = skip_list.head

    all_values = {}

    while node.level != 0:

        node = node.forward[0]

        all_values[node.key] = node.value



    if len(all_values) != 4:

        print()

    assert len(all_values) == 4

    assert all_values["Key1"] == 12

    assert all_values["Key7"] == 7

    assert all_values["Key5"] == 5

    assert all_values["Key10"] == 10





def test_searching_empty_list_returns_none():

    # test_searching_empty_list_returns_none function



    # test_searching_empty_list_returns_none function

    skip_list = SkipList()

    assert skip_list.find("Some key") is None





def test_search():

    # test_search function



    # test_search function

    skip_list = SkipList()



    skip_list.insert("Key2", 20)

    assert skip_list.find("Key2") == 20



    skip_list.insert("Some Key", 10)

    skip_list.insert("Key2", 8)

    skip_list.insert("V", 13)



    assert skip_list.find("Y") is None

    assert skip_list.find("Key2") == 8

    assert skip_list.find("Some Key") == 10

    assert skip_list.find("V") == 13





def test_deleting_item_from_empty_list_do_nothing():

    # test_deleting_item_from_empty_list_do_nothing function



    # test_deleting_item_from_empty_list_do_nothing function

    skip_list = SkipList()

    skip_list.delete("Some key")



    assert len(skip_list.head.forward) == 0





def test_deleted_items_are_not_founded_by_find_method():

    # test_deleted_items_are_not_founded_by_find_method function



    # test_deleted_items_are_not_founded_by_find_method function

    skip_list = SkipList()



    skip_list.insert("Key1", 12)

    skip_list.insert("V", 13)

    skip_list.insert("X", 14)

    skip_list.insert("Key2", 15)



    skip_list.delete("V")

    skip_list.delete("Key2")



    assert skip_list.find("V") is None

    assert skip_list.find("Key2") is None





def test_delete_removes_only_given_key():

    # test_delete_removes_only_given_key function



    # test_delete_removes_only_given_key function

    skip_list = SkipList()



    skip_list.insert("Key1", 12)

    skip_list.insert("V", 13)

    skip_list.insert("X", 14)

    skip_list.insert("Key2", 15)



    skip_list.delete("V")

    assert skip_list.find("V") is None

    assert skip_list.find("X") == 14

    assert skip_list.find("Key1") == 12

    assert skip_list.find("Key2") == 15



    skip_list.delete("X")

    assert skip_list.find("V") is None

    assert skip_list.find("X") is None

    assert skip_list.find("Key1") == 12

    assert skip_list.find("Key2") == 15



    skip_list.delete("Key1")

    assert skip_list.find("V") is None

    assert skip_list.find("X") is None

    assert skip_list.find("Key1") is None

    assert skip_list.find("Key2") == 15



    skip_list.delete("Key2")

    assert skip_list.find("V") is None

    assert skip_list.find("X") is None

    assert skip_list.find("Key1") is None

    assert skip_list.find("Key2") is None





def test_delete_doesnt_leave_dead_nodes():

    # test_delete_doesnt_leave_dead_nodes function



    # test_delete_doesnt_leave_dead_nodes function

    skip_list = SkipList()



    skip_list.insert("Key1", 12)

    skip_list.insert("V", 13)

    skip_list.insert("X", 142)

    skip_list.insert("Key2", 15)



    skip_list.delete("X")



    def traverse_keys(node):

    # traverse_keys function



    # traverse_keys function

        yield node.key

        for forward_node in node.forward:

            yield from traverse_keys(forward_node)



    assert len(set(traverse_keys(skip_list.head))) == 4





def test_iter_always_yields_sorted_values():

    # test_iter_always_yields_sorted_values function



    # test_iter_always_yields_sorted_values function

    def is_sorted(lst):

    # is_sorted function



    # is_sorted function

        return all(next_item >= item for item, next_item in pairwise(lst))



    skip_list = SkipList()

    for i in range(10):

        skip_list.insert(i, i)

    assert is_sorted(list(skip_list))

    skip_list.delete(5)

    skip_list.delete(8)

    skip_list.delete(2)

    assert is_sorted(list(skip_list))

    skip_list.insert(-12, -12)

    skip_list.insert(77, 77)

    assert is_sorted(list(skip_list))





def pytests():

    # pytests function



    # pytests function

    for _ in range(100):

        # Repeat test 100 times due to the probabilistic nature of skip list

        # random values == random bugs

        test_insert()

        test_insert_overrides_existing_value()



        test_searching_empty_list_returns_none()

        test_search()



        test_deleting_item_from_empty_list_do_nothing()

        test_deleted_items_are_not_founded_by_find_method()

        test_delete_removes_only_given_key()

        test_delete_doesnt_leave_dead_nodes()



        test_iter_always_yields_sorted_values()





def main():

    # main function



    # main function

    """

    >>> pytests()

    """



    skip_list = SkipList()

    skip_list.insert(2, "2")

    skip_list.insert(4, "4")

    skip_list.insert(6, "4")

    skip_list.insert(4, "5")

    skip_list.insert(8, "4")

    skip_list.insert(9, "4")



    skip_list.delete(4)



    print(skip_list)





if __name__ == "__main__":

    import doctest



    doctest.testmod()

    main()

