# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / queue_by_list



本文件实现 queue_by_list 相关的算法功能。

"""



from collections.abc import Iterable





class QueueByList[T]:

    """

    队列（用列表实现）



    注意：用列表实现时，get() 操作是 O(n)，

          因为需要从队头移除元素。

          生产环境中推荐使用 collections.deque（O(1)）

    """



    def __init__(self, iterable: Iterable[T] | None = None) -> None:

        self.entries: list[T] = list(iterable or [])



    def __len__(self) -> int:

        return len(self.entries)



    def __repr__(self) -> str:

        return f"Queue({tuple(self.entries)})"



    def put(self, item: T) -> None:

        """

        入队：从队尾加入



        示例:

            >>> q = QueueByList()

            >>> q.put(10)

            >>> q.put(20)

            >>> q

            Queue((10, 20))

        """

        self.entries.append(item)



    def get(self) -> T:

        """

        出队：从队头取出



        示例:

            >>> q = QueueByList([10, 20, 30])

            >>> q.get()

            10

            >>> q.get()

            20

        """

        if not self.entries:

            raise IndexError("Queue is empty")

        return self.entries.pop(0)



    def rotate(self, rotation: int) -> None:

        """

        循环移动队列元素



        示例:

            >>> q = QueueByList([10, 20, 30, 40])

            >>> q.rotate(1)

            >>> q

            Queue((20, 30, 40, 10))

        """

        for _ in range(rotation):

            self.entries.append(self.entries.pop(0))



    def get_front(self) -> T:

        """查看队头元素（不取出）"""

        return self.entries[0]





if __name__ == "__main__":

    q = QueueByList([10, 20, 30])

    print(f"初始队列: {q}")

    print(f"出队: {q.get()}, 剩余: {q}")

    q.put(40)

    print(f"入队40: {q}")

    print(f"队头: {q.get_front()}")

