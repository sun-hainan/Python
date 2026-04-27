# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / multi_level_feedback_queue



本文件实现 multi_level_feedback_queue 相关的算法功能。

"""



multi_level_feedback_queue.py

"""



from collections import deque





class Process:

    """进程"""

    def __init__(self, process_name: str, arrival_time: int, burst_time: int):

        self.process_name = process_name

        self.arrival_time = arrival_time

        self.burst_time = burst_time





class MLFQ:

    """多级反馈队列调度"""



    def __init__(

        self,

        number_of_queues: int,

        time_slices: list[int],

        queue: deque[Process],

        current_time: int,

    ) -> None:

        self.number_of_queues = number_of_queues

        self.time_slices = time_slices

        self.ready_queue = queue

        self.current_time = current_time

        self.finish_queue: deque[Process] = deque()



    def calculate_sequence_of_finish_queue(self) -> list[str]:

        """返回完成进程的顺序"""

        sequence = []

        for i in range(len(self.finish_queue)):

            sequence.append(self.finish_queue[i].process_name)

        return sequence



    def calculate_waiting_time(self, queue: list[Process]) -> list[int]:

        """计算进程的等待时间"""

        waiting_times = []

        for process in queue:

            found = False

            for i in range(len(self.finish_queue)):

                if self.finish_queue[i].process_name == process.process_name:

                    waiting_times.append(self.finish_queue[i].burst_time - process.burst_time)

                    found = True

                    break

            if not found:

                waiting_times.append(0)

        return waiting_times



    def multi_level_feedback_queue(self) -> None:

        """执行多级反馈队列调度"""

        processed = set()

        while len(self.ready_queue) > 0:

            process = self.ready_queue.popleft()

            for i in range(self.number_of_queues):

                time_slice = self.time_slices[i] if i < len(self.time_slices) else 100

                if process.burst_time <= time_slice:

                    process.burst_time = 0

                    self.finish_queue.append(process)

                    processed.add(process.process_name)

                    break

                else:

                    process.burst_time -= time_slice

                    self.current_time += time_slice

                    self.ready_queue.append(process)

                    break





if __name__ == "__main__":

    P1 = Process("P1", 0, 53)

    P2 = Process("P2", 0, 17)

    P3 = Process("P3", 0, 68)

    P4 = Process("P4", 0, 24)

    mlfq = MLFQ(3, [17, 25], deque([P1, P2, P3, P4]), 0)

    mlfq.multi_level_feedback_queue()

    print(mlfq.calculate_sequence_of_finish_queue())

