# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / rfid_collision



本文件实现 rfid_collision 相关的算法功能。

"""



import random

import math





class PureALOHA:

    """纯 ALOHA 防碰撞算法"""



    def __init__(self, frame_time=1.0):

        """

        初始化纯 ALOHA

        

        参数:

            frame_time: 帧时间（秒）

        """

        self.frame_time = frame_time

        # 标签集合

        self.tags = set()

        # 成功传输

        self.successful = []

        # 碰撞

        self.collisions = []



    def add_tags(self, num_tags):

        """

        添加标签

        

        参数:

            num_tags: 标签数量

        """

        for i in range(num_tags):

            self.tags.add(f"TAG_{i}")



    def simulate_slot(self, current_time):

        """

        模拟一个时隙的传输

        

        参数:

            current_time: 当前时间

        返回:

            result: ('success', tag) 或 ('collision', count) 或 ('idle', None)

        """

        if len(self.tags) == 0:

            return ('idle', None)

        

        # 模拟标签随机传输

        # 简化：每个标签有一定概率传输

        transmitting_tags = []

        for tag in list(self.tags):

            if random.random() < 0.1:  # 10% 传输概率

                transmitting_tags.append(tag)

        

        if len(transmitting_tags) == 0:

            return ('idle', None)

        elif len(transmitting_tags) == 1:

            # 成功

            self.tags.discard(transmitting_tags[0])

            self.successful.append((current_time, transmitting_tags[0]))

            return ('success', transmitting_tags[0])

        else:

            # 碰撞

            self.collisions.append((current_time, len(transmitting_tags)))

            return ('collision', len(transmitting_tags))



    def run_simulation(self, duration, num_tags):

        """

        运行模拟

        

        参数:

            duration: 模拟时长

            num_tags: 初始标签数

        """

        self.tags.clear()

        self.successful.clear()

        self.collisions.clear()

        self.add_tags(num_tags)

        

        current_time = 0

        slots = 0

        

        while current_time < duration and self.tags:

            result, data = self.simulate_slot(current_time)

            slots += 1

            current_time += self.frame_time

        

        return {

            'slots': slots,

            'successful': len(self.successful),

            'collisions': len(self.collisions),

            'remaining': len(self.tags)

        }





class SlottedALOHA:

    """时隙 ALOHA（SA）防碰撞算法"""



    def __init__(self, slot_time=0.001):

        """

        初始化时隙 ALOHA

        

        参数:

            slot_time: 时隙时间（秒）

        """

        self.slot_time = slot_time

        self.tags = set()

        self.successful = []

        self.collisions = []



    def add_tags(self, num_tags):

        """添加标签"""

        for i in range(num_tags):

            self.tags.add(f"TAG_{i}")



    def simulate_frame(self, current_time, frame_size):

        """

        模拟一帧的传输

        

        参数:

            current_time: 当前时间

            frame_size: 帧中的时隙数

        返回:

            results: 各时隙结果列表

        """

        results = []

        remaining_tags = set(self.tags)

        

        for slot in range(frame_size):

            if not remaining_tags:

                results.append(('idle', None))

                continue

            

            # 每个剩余标签随机选择一个时隙

            tag_to_slot = {}

            for tag in list(remaining_tags):

                assigned_slot = random.randint(0, frame_size - 1)

                if assigned_slot not in tag_to_slot:

                    tag_to_slot[assigned_slot] = []

                tag_to_slot[assigned_slot].append(tag)

            

            # 检查当前时隙

            if slot in tag_to_slot:

                tags_in_slot = tag_to_slot[slot]

                if len(tags_in_slot) == 1:

                    results.append(('success', tags_in_slot[0]))

                    self.successful.append((current_time, tags_in_slot[0]))

                    self.tags.discard(tags_in_slot[0])

                    remaining_tags.discard(tags_in_slot[0])

                else:

                    results.append(('collision', len(tags_in_slot)))

                    self.collisions.append((current_time, len(tags_in_slot)))

            else:

                results.append(('idle', None))

            

            current_time += self.slot_time

        

        return results



    def run_simulation(self, num_tags, max_frames=1000, frame_size=16):

        """

        运行模拟

        

        参数:

            num_tags: 初始标签数

            max_frames: 最大帧数

            frame_size: 每帧时隙数

        """

        self.tags.clear()

        self.successful.clear()

        self.collisions.clear()

        self.add_tags(num_tags)

        

        frames = 0

        total_slots = 0

        

        while self.tags and frames < max_frames:

            self.simulate_frame(frames * frame_size * self.slot_time, frame_size)

            frames += 1

            total_slots += frame_size

        

        return {

            'frames': frames,

            'total_slots': total_slots,

            'successful': len(self.successful),

            'collisions': len(self.collisions),

            'remaining': len(self.tags),

            'efficiency': len(self.successful) / total_slots if total_slots > 0 else 0

        }





class DynamicFramedSlottedALOHA:

    """

    动态时隙 ALOHA（DFSA）防碰撞算法

    

    根据剩余标签数量动态调整帧大小

    """



    def __init__(self, initial_frame_size=16):

        """

        初始化 DFSA

        

        参数:

            initial_frame_size: 初始帧大小

        """

        self.frame_size = initial_frame_size

        self.tags = set()

        self.successful = []

        self.collisions = []

        self.idle_slots = []



    def add_tags(self, num_tags):

        """添加标签"""

        for i in range(num_tags):

            self.tags.add(f"TAG_{i}")



    def estimate_tag_count(self, idle, success, collision):

        """

        估计剩余标签数量

        

        使用理论公式：n ≈ 2.39 * C / (1 - I/N)

        其中 I 是空闲时隙数，C 是碰撞时隙数，N 是帧大小

        

        参数:

            idle: 空闲时隙数

            success: 成功时隙数

            collision: 碰撞时隙数

        返回:

            estimated_n: 估计的标签数

        """

        if self.frame_size == 0:

            return 0

        

        # 简化的估计

        # 碰撞时隙中平均有 2.39 个标签

        estimated_n = 2.39 * collision

        

        return max(estimated_n, success + collision)



    def adjust_frame_size(self, estimated_tags):

        """

        调整帧大小

        

        理想情况下帧大小应等于标签数

        

        参数:

            estimated_tags: 估计的标签数

        """

        # 调整帧大小为估计标签数或最接近的 2 的幂

        new_size = max(1, min(256, int(estimated_tags)))

        

        # 简化：使用 2 的幂

        self.frame_size = 2 ** math.ceil(math.log2(new_size)) if new_size > 0 else 2

        self.frame_size = min(max(self.frame_size, 2), 256)



    def run_frame(self, frame_num):

        """

        运行一帧

        

        参数:

            frame_num: 帧编号

        返回:

            results: 时隙结果

        """

        results = []

        idle = 0

        success = 0

        collision = 0

        

        tag_list = list(self.tags)

        random.shuffle(tag_list)

        

        for slot in range(self.frame_size):

            if not tag_list:

                results.append(('idle', None))

                idle += 1

                continue

            

            # 模拟标签响应（随机分配到时隙）

            # 简化：使用概率模型

            remaining = len(tag_list)

            # 标签选择当前时隙的概率

            p = 1.0 / self.frame_size

            

            # 模拟哪些标签选择了这个时隙

            selected = []

            for tag in tag_list[:]:  # 复制列表以便修改

                if random.random() < p:

                    selected.append(tag)

            

            # 从剩余标签中移除

            for tag in selected:

                if tag in tag_list:

                    tag_list.remove(tag)

            

            if len(selected) == 0:

                results.append(('idle', None))

                idle += 1

            elif len(selected) == 1:

                results.append(('success', selected[0]))

                self.tags.discard(selected[0])

                self.successful.append((frame_num, slot, selected[0]))

                success += 1

            else:

                results.append(('collision', len(selected)))

                self.collisions.append((frame_num, slot, len(selected)))

                collision += 1

        

        return {

            'results': results,

            'idle': idle,

            'success': success,

            'collision': collision

        }



    def run_simulation(self, num_tags, max_frames=100):

        """

        运行模拟

        

        参数:

            num_tags: 初始标签数

            max_frames: 最大帧数

        """

        self.tags.clear()

        self.successful.clear()

        self.collisions.clear()

        self.idle_slots.clear()

        self.add_tags(num_tags)

        self.frame_size = 16

        

        total_slots = 0

        

        for frame in range(max_frames):

            if not self.tags:

                break

            

            result = self.run_frame(frame)

            total_slots += self.frame_size

            

            # 估计剩余标签数并调整帧大小

            estimated = self.estimate_tag_count(

                result['idle'],

                result['success'],

                result['collision']

            )

            self.adjust_frame_size(estimated)

            

            if frame < 5 or frame % 20 == 0:

                print(f"  帧 {frame}: 帧大小={self.frame_size}, "

                      f"空闲={result['idle']}, 成功={result['success']}, "

                      f"碰撞={result['collision']}, 剩余={len(self.tags)}")

        

        return {

            'frames': max_frames if self.tags else frame + 1,

            'total_slots': total_slots,

            'successful': len(self.successful),

            'collisions': len(self.collisions),

            'remaining': len(self.tags),

            'efficiency': len(self.successful) / total_slots if total_slots > 0 else 0

        }





class BinaryTreeAlgorithm:

    """二进制树防碰撞算法"""



    def __init__(self):

        """初始化二进制树算法"""

        self.tags = set()

        self.identified = []



    def add_tags(self, num_tags):

        """添加标签"""

        for i in range(num_tags):

            self.tags.add(f"TAG_{i}")



    def _split_tags(self, tags, prefix):

        """

        根据下一位分割标签集合

        

        参数:

            tags: 标签集合

            prefix: 当前前缀

        返回:

            (group0, group1): 下一位为 0 和 1 的两组

        """

        group0 = set()

        group1 = set()

        

        for tag in tags:

            # 模拟标签的随机 ID

            tag_id = hash(tag) % (2**8)  # 8 位 ID

            bit = (tag_id >> (7 - len(prefix))) & 1

            if bit == 0:

                group0.add(tag)

            else:

                group1.add(tag)

        

        return group0, group1



    def query(self, prefix):

        """

        查询一个前缀下的标签

        

        参数:

            prefix: 当前前缀

        返回:

            identified: 识别出的标签列表

        """

        if not self.tags:

            return []

        

        # 分割

        group0, group1 = self._split_tags(self.tags, prefix)

        

        identified = []

        

        # 如果只有一组且只有一个标签，识别它

        if len(group0) == 1 and len(group1) == 0:

            tag = list(group0)[0]

            self.tags.discard(tag)

            self.identified.append(tag)

            identified.append(tag)

        elif len(group0) == 0 and len(group1) == 1:

            tag = list(group1)[0]

            self.tags.discard(tag)

            self.identified.append(tag)

            identified.append(tag)

        else:

            # 递归查询

            if group0:

                identified.extend(self.query(prefix + '0'))

            if group1:

                identified.extend(self.query(prefix + '1'))

        

        return identified



    def run_simulation(self, num_tags):

        """

        运行模拟

        

        参数:

            num_tags: 初始标签数

        """

        self.tags.clear()

        self.identified.clear()

        self.add_tags(num_tags)

        

        queries = 0

        identified = self.query('')

        queries = len(self.identified)  # 简化：queries ≈ identified

        

        return {

            'queries': queries,

            'identified': len(self.identified),

            'remaining': len(self.tags)

        }





if __name__ == "__main__":

    # 测试 RFID 防碰撞算法

    print("=== RFID 防碰撞算法测试 ===\n")



    # 1. 纯 ALOHA

    print("--- 纯 ALOHA ---")

    pure_aloha = PureALOHA(frame_time=0.001)

    result = pure_aloha.run_simulation(duration=1.0, num_tags=50)

    print(f"标签数: 50, 时隙数: {result['slots']}")

    print(f"  成功: {result['successful']}, 碰撞: {result['collisions']}, "

          f"剩余: {result['remaining']}")



    # 2. 时隙 ALOHA

    print("\n--- 时隙 ALOHA (SA) ---")

    sa = SlottedALOHA(slot_time=0.001)

    result = sa.run_simulation(num_tags=50, frame_size=16)

    print(f"帧数: {result['frames']}, 总时隙: {result['total_slots']}")

    print(f"  成功: {result['successful']}, 碰撞: {result['collisions']}")

    print(f"  效率: {result['efficiency']:.2%}")



    # 3. 动态时隙 ALOHA

    print("\n--- 动态时隙 ALOHA (DFSA) ---")

    dfsa = DynamicFramedSlottedALOHA(initial_frame_size=16)

    print("模拟 50 个标签:")

    result = dfsa.run_simulation(num_tags=50, max_frames=50)

    print(f"\n总帧数: {result['frames']}, 总时隙: {result['total_slots']}")

    print(f"  成功: {result['successful']}, 碰撞: {result['collisions']}")

    print(f"  剩余: {result['remaining']}, 效率: {result['efficiency']:.2%}")



    # 4. 二进制树算法

    print("\n--- 二进制树算法 ---")

    bt = BinaryTreeAlgorithm()

    result = bt.run_simulation(num_tags=50)

    print(f"查询次数: {result['queries']}")

    print(f"  识别: {result['identified']}, 剩余: {result['remaining']}")



    # 比较

    print("\n=== 算法比较 ===")

    print(f"{'算法':<25} {'时隙/查询数':<12} {'成功数':<8} {'效率':<8}")

    print("-" * 60)

    

    pure_aloha2 = PureALOHA()

    result = pure_aloha2.run_simulation(duration=1.0, num_tags=50)

    print(f"{'纯 ALOHA':<25} {result['slots']:<12} {result['successful']:<8} "

          f"{result['successful']/result['slots']:.2%}")

    

    sa2 = SlottedALOHA()

    result = sa2.run_simulation(num_tags=50, frame_size=16)

    print(f"{'时隙 ALOHA':<25} {result['total_slots']:<12} {result['successful']:<8} "

          f"{result['efficiency']:.2%}")

    

    dfsa2 = DynamicFramedSlottedALOHA()

    result = dfsa2.run_simulation(num_tags=50, max_frames=50)

    print(f"{'动态时隙 ALOHA':<25} {result['total_slots']:<12} {result['successful']:<8} "

          f"{result['efficiency']:.2%}")

    

    bt2 = BinaryTreeAlgorithm()

    result = bt2.run_simulation(num_tags=50)

    print(f"{'二进制树':<25} {result['queries']:<12} {result['identified']:<8} "

          f"{result['identified']/result['queries']:.2%}")

