# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / protein_folding_hp



本文件实现 protein_folding_hp 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Set, Optional

import math

import random





class HPModel:

    """HP模型蛋白质折叠"""



    def __init__(self, sequence: str):

        """

        参数:

            sequence: 氨基酸序列，如 'HPHPPHPHPH'

        """

        self.sequence = sequence.upper()

        self.n = len(sequence)

        self.positions = {}  # 氨基酸在网格中的位置



    def enumerate_fold(self) -> Tuple[List[Tuple[int, int]], int]:

        """

        枚举所有可能的折叠构象



        穷举所有2^(n-1)种转向序列



        返回:

            (best_conformation, best_hh_contacts)

        """

        best_score = -1

        best_conf = None



        # 方向序列：每个氨基酸可以选择左/右/上/下

        # 用二进制编码：0=左/下, 1=右/上

        for bits in range(2 ** (self.n - 1)):

            directions = []

            for i in range(self.n - 1):

                directions.append(1 if (bits >> i) & 1 else 0)



            try:

                conf = self._build_conformation(directions)

                score = self._count_hh_contacts(conf)

                if score > best_score:

                    best_score = score

                    best_conf = conf

            except:

                pass



        return best_conf, best_score



    def _build_conformation(self, directions: List[int]) -> List[Tuple[int, int]]:

        """根据方向序列构建构象"""

        pos = [(0, 0)]

        x, y = 0, 0



        for i, d in enumerate(directions):

            if d == 0:  # 左

                x -= 1

            elif d == 1:  # 右

                x += 1

            elif d == 2:  # 上

                y += 1

            else:  # 下

                y -= 1

            pos.append((x, y))



        # 检查自交

        if len(set(pos)) != len(pos):

            raise ValueError("Self-intersection")



        return pos



    def _count_hh_contacts(self, conformation: List[Tuple[int, int]]) -> int:

        """

        计算H-H接触数



        两个H氨基酸在空间上相邻（但不在序列上相邻）时+1

        """

        contact_set = set()

        for i in range(self.n):

            for j in range(i + 2, self.n):

                if self.sequence[i] == 'H' and self.sequence[j] == 'H':

                    # 检查是否在网格上相邻

                    if abs(conformation[i][0] - conformation[j][0]) +                        abs(conformation[i][1] - conformation[j][1]) == 1:

                        pair = (min(i, j), max(i, j))

                        contact_set.add(pair)



        return len(contact_set)



    def greedy_fold(self) -> Tuple[List[Tuple[int, int]], int]:

        """

        贪心折叠算法



        每步选择使HH接触最大化的方向

        """

        directions = []

        pos = [(0, 0)]

        x, y = 0, 0

        used = {(0, 0)}



        for step in range(self.n - 1):

            best_dir = 0

            best_contacts = -1



            for d in range(4):

                nx, ny = x, y

                if d == 0:

                    nx -= 1

                elif d == 1:

                    nx += 1

                elif d == 2:

                    ny += 1

                else:

                    ny -= 1



                if (nx, ny) in used:

                    continue



                # 临时添加并计算接触

                temp_pos = pos + [(nx, ny)]

                contacts = self._count_hh_contacts(temp_pos)

                if contacts > best_contacts:

                    best_contacts = contacts

                    best_dir = d

                    best_new = (nx, ny)



            # 应用最佳方向

            directions.append(best_dir)

            x, y = best_new

            pos.append((x, y))

            used.add((x, y))



        conformation = pos

        score = self._count_hh_contacts(conformation)

        return conformation, score



    def simulated_annealing_fold(

        self,

        initial_temp: float = 10.0,

        cooling_rate: float = 0.99,

        n_iter: int = 10000

    ) -> Tuple[List[Tuple[int, int]], int]:

        """

        模拟退火折叠



        参数:

            initial_temp: 初始温度

            cooling_rate: 降温速率

            n_iter: 迭代次数



        返回:

            (best_conformation, best_score)

        """

        # 随机初始构象

        current_pos = [(0, 0)]

        x, y = 0, 0

        for _ in range(self.n - 1):

            d = random.randint(0, 3)

            if d == 0:

                x -= 1

            elif d == 1:

                x += 1

            elif d == 2:

                y += 1

            else:

                y -= 1

            current_pos.append((x, y))



        current_score = self._count_hh_contacts(current_pos)

        best_pos = current_pos.copy()

        best_score = current_score



        temp = initial_temp



        for iteration in range(n_iter):

            # 随机选择一个位置进行"折返"

            if len(current_pos) < 3:

                continue



            i = random.randint(1, len(current_pos) - 2)

            # 简化的邻居移动

            delta_x = random.choice([-1, 1])

            delta_y = random.choice([-1, 1])



            new_pos = current_pos.copy()

            # 反转从i开始的子链

            new_pos[i] = (new_pos[i][0] + delta_x, new_pos[i][1] + delta_y)



            # 检查有效性

            valid = True

            positions_set = set()

            for j, (px, py) in enumerate(new_pos):

                if (px, py) in positions_set:

                    valid = False

                    break

                positions_set.add((px, py))



            if not valid:

                continue



            new_score = self._count_hh_contacts(new_pos)

            delta = new_score - current_score



            # Metropolis准则

            if delta > 0 or random.random() < math.exp(delta / temp):

                current_pos = new_pos

                current_score = new_score



                if current_score > best_score:

                    best_score = current_score

                    best_pos = current_pos.copy()



            temp *= cooling_rate



        return best_pos, best_score



    def visualize_folding(self, conformation: List[Tuple[int, int]]) -> str:

        """生成ASCII可视化"""

        if not conformation:

            return ""



        xs = [p[0] for p in conformation]

        ys = [p[1] for p in conformation]



        min_x, max_x = min(xs), max(xs)

        min_y, max_y = min(ys), max(ys)



        grid = [[' ' for _ in range(max_x - min_x + 3)] for _ in range(max_y - min_y + 3)]



        # 标记氨基酸

        for i, (x, y) in enumerate(conformation):

            gx = x - min_x + 1

            gy = y - min_y + 1

            grid[gy][gx] = self.sequence[i]



        # 标记连接

        for i in range(len(conformation) - 1):

            x1, y1 = conformation[i]

            x2, y2 = conformation[i + 1]

            gx1, gy1 = x1 - min_x + 1, y1 - min_y + 1

            gx2, gy2 = x2 - min_x + 1, y2 - min_y + 1

            if gx1 == gx2:

                for gy in range(min(gy1, gy2), max(gy1, gy2) + 1):

                    if grid[gy][gx1] == ' ':

                        grid[gy][gx1] = '-'

            else:

                for gx in range(min(gx1, gx2), max(gx1, gx2) + 1):

                    if grid[gy1][gx] == ' ':

                        grid[gy1][gx] = '-'



        lines = [''.join(row) for row in grid]

        return '\n'.join(lines)





if __name__ == '__main__':

    print('=== HP模型蛋白质折叠测试 ===')



    sequences = ['HPHPPHPHPH', 'HPPHPHPPHP', 'HPHPPHPPHPH']

    for seq in sequences:

        hp = HPModel(seq)

        print(f'\n序列: {seq}')



        # 贪心

        conf_greedy, score_greedy = hp.greedy_fold()

        print(f'  贪心: HH接触={score_greedy}')

        print(hp.visualize_folding(conf_greedy))



        # 模拟退火

        np.random.seed(42)

        random.seed(42)

        conf_sa, score_sa = hp.simulated_annealing_fold(n_iter=5000)

        print(f'  模拟退火: HH接触={score_sa}')

        print(hp.visualize_folding(conf_sa))



    # 测试枚举（短序列）

    print('\n--- 短序列枚举 ---')

    short_seq = 'HPHP'

    hp = HPModel(short_seq)

    conf_enum, score_enum = hp.enumerate_fold()

    print(f'  序列 {short_seq}: 枚举最优HH接触={score_enum}')

    print(hp.visualize_folding(conf_enum))

