# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / job_sequencing_with_deadline

本文件实现 job_sequencing_with_deadline 相关的算法功能。
"""

job_sequencing_with_deadline.py
"""


def schedule_jobs(jobs: list) -> list:
    """
    带截止时间的作业调度（Job Sequencing with Deadline）
    每个作业格式为 (job_id, deadline, profit)
    返回 [完成作业数, 最大利润]
    >>> schedule_jobs([(1, 4, 20), (2, 1, 10), (3, 1, 40), (4, 1, 30)])
    [2, 60]
    """
    max_deadline = max(jobs, key=lambda value: value[1])[1]
    time_slots = [-1] * max_deadline

    count = 0
    max_profit = 0
    for job in jobs:
        for i in range(job[1] - 1, -1, -1):
            if time_slots[i] == -1:
                time_slots[i] = job[0]
                count += 1
                max_profit += job[2]
                break
    return [count, max_profit]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
