# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / dining_philosophers

本文件实现 dining_philosophers 相关的算法功能。
"""

import threading
import time
import random


class Philosopher:
    """哲学家线程"""

    def __init__(self, name: str, left_chopstick: threading.Lock,
                 right_chopstick: threading.Lock, fork_order: int):
        self.name = name
        self.left = left_chopstick
        self.right = right_chopstick
        self.fork_order = fork_order
        self.meals_eaten = 0

    def run(self, num_meals: int):
        for i in range(num_meals):
            print(f"[{self.name}] 思考中...")
            time.sleep(random.uniform(0.5, 1.5))

            # 按固定顺序拿起筷子（避免死锁）
            first = self.left if self.fork_order == 0 else self.right
            second = self.right if self.fork_order == 0 else self.left

            print(f"[{self.name}] 饥饿，拿起筷子...")
            first.acquire()
            second.acquire()

            print(f"[{self.name}] 开始吃饭 (第{i+1}次)")
            time.sleep(random.uniform(0.3, 0.8))
            self.meals_eaten += 1

            # 放下筷子
            second.release()
            first.release()
            print(f"[{self.name}] 放下筷子")


class DiningPhilosophers:
    """哲学家就餐问题模拟器"""

    def __init__(self, num_philosophers: int = 5):
        self.num = num_philosophers
        self.chopsticks = [threading.Lock() for _ in range(num_philosophers)]
        self.philosophers = []

    def simulate_classic(self, meals: int):
        """
        经典方案（有死锁风险）

        所有哲学家都先拿左边的筷子
        """
        print("=== 经典方案（可能死锁）===\n")

        for i in range(self.num):
            p = Philosopher(f"Ph{i+1}", self.chopsticks[i], self.chopsticks[(i+1) % self.num], fork_order=0)
            self.philosophers.append(p)

        threads = []
        for p in self.philosophers:
            t = threading.Thread(target=p.run, args=(meals,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print("\n统计:")
        for p in self.philosophers:
            print(f"  {p.name}: 吃了 {p.meals_eaten} 次")

    def simulate_ordered(self, meals: int):
        """
        资源顺序法（避免死锁）

        规定所有哲学家都按相同顺序拿筷子（左→右）
        """
        print("\n=== 资源顺序法（避免死锁）===\n")

        self.philosophers = []

        for i in range(self.num):
            p = Philosopher(f"Ph{i+1}", self.chopsticks[i], self.chopsticks[(i+1) % self.num], fork_order=0)
            self.philosophers.append(p)

        threads = []
        for p in self.philosophers:
            t = threading.Thread(target=p.run, args=(meals,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print("\n统计:")
        for p in self.philosophers:
            print(f"  {p.name}: 吃了 {p.meals_eaten} 次")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 哲学家就餐问题 ===\n")

    print("场景:")
    print("  5个哲学家")
    print("  每人吃3次")
    print("\n")

    simulator = DiningPhilosophers(5)

    # 运行有序方案（避免死锁）
    simulator.simulate_ordered(meals=3)

    print("\n结论：")
    print("  - 经典方案存在死锁风险（所有哲学家同时拿起左筷子）")
    print("  - 资源顺序法通过规定拿筷子顺序避免循环等待")
    print("  - 其他方案：最多4个哲学家、用单服务员、用管程")
