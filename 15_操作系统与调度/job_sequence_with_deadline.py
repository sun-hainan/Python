# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / job_sequence_with_deadline

本文件实现 job_sequence_with_deadline 相关的算法功能。
"""

from dataclasses import dataclass
from operator import attrgetter


@dataclass
class Task:
    task_id: int
    deadline: int
    reward: int


def max_tasks(tasks_info: list[tuple[int, int]]) -> list[int]:
    """
    Create a list of Task objects that are sorted so the highest rewards come first.
    Return a list of those task ids that can be completed before i becomes too high.
    >>> max_tasks([(4, 20), (1, 10), (1, 40), (1, 30)])
    [2, 0]
    >>> max_tasks([(1, 10), (2, 20), (3, 30), (2, 40)])
    [3, 2]
    >>> max_tasks([(9, 10)])
    [0]
    >>> max_tasks([(-9, 10)])
    []
    >>> max_tasks([])
    []
    >>> max_tasks([(0, 10), (0, 20), (0, 30), (0, 40)])
    []
    >>> max_tasks([(-1, 10), (-2, 20), (-3, 30), (-4, 40)])
    []
    """
    tasks = sorted(
        (
            Task(task_id, deadline, reward)
            for task_id, (deadline, reward) in enumerate(tasks_info)
        ),
        key=attrgetter("reward"),
        reverse=True,
    )
    return [task.task_id for i, task in enumerate(tasks, start=1) if task.deadline >= i]


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    print(f"{max_tasks([(4, 20), (1, 10), (1, 40), (1, 30)]) = }")
    print(f"{max_tasks([(1, 10), (2, 20), (3, 30), (2, 40)]) = }")
