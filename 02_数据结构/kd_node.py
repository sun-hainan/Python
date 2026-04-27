# -*- coding: utf-8 -*-
"""
算法实现：02_数据结构 / kd_node

本文件实现 kd_node 相关的算法功能。
"""

#  Created by: Ramy-Badr-Ahmed (https://github.com/Ramy-Badr-Ahmed)
#  in Pull Request: #11532
#  https://github.com/TheAlgorithms/Python/pull/11532
#
#  Please mention me (@Ramy-Badr-Ahmed) in any issue or pull request
#  addressing bugs/corrections to this file.
#  Thank you!

from __future__ import annotations


class KDNode:
    """
    Represents a node in a KD-Tree.

    Attributes:
        point: The point stored in this node.
        left: The left child node.
        right: The right child node.
    """

    def __init__(
        self,
        point: list[float],
        left: KDNode | None = None,
        right: KDNode | None = None,
    ) -> None:
        """
        Initializes a KDNode with the given point and child nodes.

        Args:
            point (list[float]): The point stored in this node.
            left (Optional[KDNode]): The left child node.
            right (Optional[KDNode]): The right child node.
        """
        self.point = point
        self.left = left
        self.right = right
if __name__ == "__main__":
    import doctest
    doctest.testmod()
