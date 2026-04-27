# -*- coding: utf-8 -*-

"""

算法实现：可视化 / banker_algorithm_visualizer



本文件实现 banker_algorithm_visualizer 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt

import matplotlib.patches as patches

import matplotlib.animation as animation



# 中文字体设置

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False





class BankersAlgorithm:

    """

    银行家算法类 - 用于死锁检测和安全序列分析

    

    属性:

        num_processes: 进程数量

        num_resources: 资源类型数量

        available: 可用资源向量

        maximum: 最大需求矩阵

        allocation: 已分配矩阵

        need: 需求矩阵 (need = max - allocation)

    """

    

    def __init__(self, available, maximum, allocation):

        """

        初始化银行家算法

        

        参数:

            available: 可用资源向量 [r1, r2, ...]

            maximum: 最大需求矩阵 [[p0_max], [p1_max], ...]

            allocation: 已分配矩阵 [[p0_alloc], [p1_alloc], ...]

        """

        self.available = np.array(available)

        self.maximum = np.array(maximum)

        self.allocation = np.array(allocation)

        self.need = self.maximum - self.allocation

        self.num_processes = len(allocation)

        self.num_resources = len(available)

    

    def is_safe_state(self):

        """

        检查系统是否处于安全状态

        

        返回:

            (bool, list, list): (是否安全, 安全序列, 工作向量历史)

        """

        # 工作向量 = 可用资源副本

        work = self.available.copy()

        # 完成标志

        finish = [False] * self.num_processes

        # 安全序列

        safe_sequence = []

        # 工作向量变化历史（用于可视化）

        work_history = [work.copy()]

        

        while True:

            # 找到一个未完成且需求可满足的进程

            found = False

            for i in range(self.num_processes):

                if not finish[i] and np.all(self.need[i] <= work):

                    # 可以满足：模拟分配

                    work += self.allocation[i]

                    finish[i] = True

                    safe_sequence.append(i)

                    work_history.append(work.copy())

                    found = True

                    break

            

            if not found:

                break

        

        is_safe = all(finish)

        return is_safe, safe_sequence, work_history

    

    def find_deadlock(self):

        """

        检测死锁（找出未完成的进程）

        

        返回:

            list: 死锁进程列表

        """

        _, safe_seq, _ = self.is_safe_state()

        completed = set(safe_seq)

        deadlocked = [i for i in range(self.num_processes) if i not in completed]

        return deadlocked

    

    def can_allocate(self, process_id, request):

        """

        检查请求是否可以满足

        

        参数:

            process_id: 进程ID

            request: 请求资源向量

        

        返回:

            bool: 是否可以分配

        """

        request = np.array(request)

        

        # 条件1: 请求不超过需求

        if not np.all(request <= self.need[process_id]):

            return False

        

        # 条件2: 请求不超过可用资源

        if not np.all(request <= self.available):

            return False

        

        return True

    

    def simulate_request(self, process_id, request):

        """

        模拟资源请求（试探性分配）

        

        参数:

            process_id: 进程ID

            request: 请求资源向量

        

        返回:

            (bool, str): (是否成功, 原因说明)

        """

        request = np.array(request)

        

        # 检查请求是否超过最大需求

        if not np.all(request <= self.need[process_id]):

            return False, "错误: 请求超过最大需求"

        

        # 检查请求是否超过可用资源

        if not np.all(request <= self.available):

            return False, "错误: 资源不足，需要等待"

        

        # 试探性分配

        old_available = self.available.copy()

        old_allocation = self.allocation[process_id].copy()

        old_need = self.need[process_id].copy()

        

        self.available -= request

        self.allocation[process_id] += request

        self.need[process_id] -= request

        

        # 检查安全状态

        is_safe, safe_seq, _ = self.is_safe_state()

        

        if is_safe:

            return True, f"分配成功! 安全序列: {safe_seq}"

        else:

            # 回滚

            self.available = old_available

            self.allocation[process_id] = old_allocation

            self.need[process_id] = old_need

            return False, "危险: 分配后系统可能死锁，拒绝请求"





def visualize_bankers_algorithm(available, maximum, allocation, requests=None):

    """

    可视化银行家算法

    

    参数:

        available: 可用资源

        maximum: 最大需求矩阵

        allocation: 已分配矩阵

        requests: 可选的请求序列 [(process_id, request), ...]

    """

    bankers = BankersAlgorithm(available, maximum, allocation)

    

    # 创建图形

    fig = plt.figure(figsize=(18, 12))

    

    # 左侧：资源分配表

    ax_table = plt.subplot2grid((3, 3), (0, 0), colspan=2, rowspan=2)

    

    # 右上：状态图

    ax_status = plt.subplot2grid((3, 3), (0, 2))

    

    # 右中：安全序列/死锁信息

    ax_info = plt.subplot2grid((3, 3), (1, 2))

    

    # 下方：操作历史

    ax_history = plt.subplot2grid((3, 3), (2, slice(0, 3)))

    ax_history.axis('off')

    

    def draw_resource_table(bankers_obj, ax, highlight_process=None, work_history_step=None, 

                           safe_sequence=None, finish_status=None):

        """

        绘制资源分配表

        

        参数:

            bankers_obj: BankersAlgorithm实例

            ax: matplotlib子图

            highlight_process: 高亮进程ID

            work_history_step: 工作向量历史的步数

            safe_sequence: 当前安全序列

            finish_status: 进程完成状态

        """

        ax.clear()

        ax.axis('off')

        ax.set_title('银行家算法 - 资源分配表', fontsize=14, fontweight='bold')

        

        # 表格数据

        processes = [f'P{i}' for i in range(bankers_obj.num_processes)]

        resources = [f'R{i}' for i in range(bankers_obj.num_resources)]

        

        # 表头

        headers = ['进程'] + [f'Max\n{r}' for r in resources] + \

                  [f'Allocation\n{r}' for r in resources] + \

                  [f'Need\n{r}' for r in resources]

        

        # 数据行

        table_data = []

        for i in range(bankers_obj.num_processes):

            row = [f'P{i}']

            row.extend([str(m) for m in bankers_obj.maximum[i]])

            row.extend([str(a) for a in bankers_obj.allocation[i]])

            row.extend([str(n) for n in bankers_obj.need[i]])

            table_data.append(row)

        

        # 可用资源行

        avail_row = ['Available'] + [str(a) for a in bankers_obj.available]

        

        # 创建表格

        col_count = 1 + 3 * bankers_obj.num_resources

        cell_text = table_data

        

        # 绘制表格

        ax.set_table(cellText=cell_text,

                    colLabels=headers,

                    cellLoc='center',

                    loc='center',

                    colWidths=[0.08] * col_count)

        

        # 设置表格样式

        table = ax.tables[0]

        table.auto_set_font_size(False)

        table.set_fontsize(9)

        table.scale(1.2, 1.8)

        

        # 高亮完成状态的行

        if finish_status:

            for i, finished in enumerate(finish_status):

                if finished:

                    for j in range(col_count):

                        cell = table.get_celld()[(i+1, j)]

                        cell.set_facecolor('#90EE90')  # 浅绿色表示完成

        

        # 高亮当前检查的进程

        if highlight_process is not None:

            for j in range(col_count):

                cell = table.get_celld()[(highlight_process+1, j)]

                cell.set_facecolor('#FFD700')  # 金色高亮

        

        # 添加Available行（在表格下方手动添加）

        ax.text(0.5, -0.15, f'Available: {list(bankers_obj.available)}',

               ha='center', va='top', fontsize=11, fontweight='bold',

               transform=ax.transAxes)

        

        # 绘制Need向量

        ax.text(0.5, -0.22,

               f'Need矩阵: \n{bankers_obj.need}',

               ha='center', va='top', fontsize=10,

               transform=ax.transAxes,

               bbox=dict(boxstyle='round', facecolor='lightyellow'))

    

    def draw_status_dia(bankers_obj, ax, is_safe, safe_sequence, deadlocked):

        """

        绘制状态图

        

        参数:

            bankers_obj: BankersAlgorithm实例

            ax: matplotlib子图

            is_safe: 是否安全

            safe_sequence: 安全序列

            deadlocked: 死锁进程列表

        """

        ax.clear()

        ax.set_xlim(0, 10)

        ax.set_ylim(0, 10)

        ax.set_aspect('equal')

        ax.axis('off')

        

        if is_safe:

            ax.set_facecolor('#f0fff0')  # 浅绿色背景

            status_color = 'green'

            status_text = '✓ 安全状态'

        else:

            ax.set_facecolor('#fff0f0')  # 浅红色背景

            status_color = 'red'

            status_text = '✗ 危险状态!'

        

        ax.set_title(f'系统状态: {status_text}', fontsize=12, fontweight='bold', color=status_color)

        

        # 绘制进程圆

        for i in range(bankers_obj.num_processes):

            x = 2 + (i % 3) * 3

            y = 7 - (i // 3) * 3

            

            # 确定颜色

            if i in deadlocked:

                color = '#FF6B6B'  # 红色 - 死锁

                status = 'DEADLOCK'

            elif safe_sequence and i in safe_sequence[:len([s for s in safe_sequence if s is not None])]:

                idx = safe_sequence.index(i) if i in safe_sequence else -1

                if idx >= 0:

                    color = '#90EE90'  # 绿色渐深 - 已安全

                    status = f'Safe-{idx+1}'

                else:

                    color = '#87CEEB'  # 蓝色 - 等待中

                    status = 'Waiting'

            else:

                color = '#FFD700'  # 金色 - 初始

                status = 'Ready'

            

            circle = plt.Circle((x, y), 1, color=color, ec='black', linewidth=2)

            ax.add_patch(circle)

            ax.text(x, y, f'P{i}', ha='center', va='center', fontsize=14, fontweight='bold')

            ax.text(x, y - 1.5, status, ha='center', va='top', fontsize=9, color=color.replace('#', '#3'))

        

        # 绘制图例

        legend_items = [

            ('#90EE90', '已完成'),

            ('#87CEEB', '就绪/等待'),

            ('#FFD700', '初始状态'),

            ('#FF6B6B', '死锁'),

        ]

        for i, (color, label) in enumerate(legend_items):

            ax.add_patch(plt.Rectangle((0.5, 1 - i * 0.8), 0.5, 0.5, facecolor=color, edgecolor='black'))

            ax.text(1.2, 1.25 - i * 0.8, label, va='center', fontsize=9)

        

        # 安全序列

        if safe_sequence:

            ax.text(5, 1, f'安全序列:\n{" → ".join([f"P{p}" for p in safe_sequence])}',

                   ha='left', va='center', fontsize=10,

                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

    

    def update(frame_idx):

        """更新画面"""

        ax_table.clear()

        ax_status.clear()

        ax_history.clear()

        ax_history.axis('off')

        

        # 初始状态

        if frame_idx == 0:

            draw_resource_table(bankers, ax_table)

            is_safe, safe_seq, work_history = bankers.is_safe_state()

            deadlocked = bankers.find_deadlock()

            draw_status_dia(bankers, ax_status, is_safe, safe_seq, deadlocked)

            

            ax_info.clear()

            ax_info.axis('off')

            ax_info.text(0.5, 0.5, f'安全检查\n\n点击"开始"分析',

                       ha='center', va='center', fontsize=12)

            

            ax_history.text(0.5, 0.5, '操作历史: 初始化完成',

                          ha='center', va='center', fontsize=11)

            return []

        

        # 安全序列检测过程

        is_safe, safe_seq, work_history = bankers.is_safe_state()

        

        # 绘制表格（高亮当前检查的进程）

        highlight = safe_seq[frame_idx - 1] if frame_idx <= len(safe_seq) else None

        finish_status = [False] * bankers.num_processes

        for i in range(frame_idx - 1):

            if i < len(safe_seq):

                finish_status[safe_seq[i]] = True

        

        draw_resource_table(bankers, ax_table, highlight_process=highlight,

                           finish_status=finish_status)

        

        # 绘制状态图

        deadlocked = bankers.find_deadlock()

        draw_status_dia(bankers, ax_status, is_safe, safe_seq, deadlocked)

        

        # 信息面板

        ax_info.clear()

        ax_info.axis('off')

        

        if frame_idx <= len(safe_seq):

            current_p = safe_seq[frame_idx - 1]

            work = work_history[frame_idx]

            alloc = bankers.allocation[current_p]

            

            info_text = f'检查 P{current_p}:\n'

            info_text += f'Need ≤ Work?\n'

            info_text += f'{bankers.need[current_p]} ≤ {work_history[frame_idx-1]}\n'

            info_text += f'= {"是" if np.all(bankers.need[current_p] <= work_history[frame_idx-1]) else "否"}\n\n'

            info_text += f'分配资源给 P{current_p}\n'

            info_text += f'Work = {work_history[frame_idx-1]} + {alloc}\n'

            info_text += f'    = {work}'

            

            ax_info.text(0.5, 0.5, info_text, ha='center', va='center', fontsize=9,

                        bbox=dict(boxstyle='round', facecolor='lightyellow'))

        else:

            if is_safe:

                ax_info.text(0.5, 0.5, f'✓ 系统安全!\n\n安全序列:\n{" → ".join([f"P{p}" for p in safe_seq])}',

                           ha='center', va='center', fontsize=11,

                           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

            else:

                ax_info.text(0.5, 0.5, f'✗ 系统不安全!\n\n死锁进程:\n{[f"P{p}" for p in deadlocked]}',

                           ha='center', va='center', fontsize=11,

                           bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))

        

        # 历史面板

        history_text = f'操作历史: 检查进程 '

        if frame_idx <= len(safe_seq):

            history_text += ' → '.join([f'P{p}' for p in safe_seq[:frame_idx]])

        ax_history.text(0.5, 0.5, history_text, ha='center', va='center', fontsize=11,

                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        

        return []

    

    # 初始化

    is_safe, safe_seq, work_history = bankers.is_safe_state()

    num_frames = len(safe_seq) + 2  # 初始帧 + 每个安全检查 + 结果帧

    

    anim = animation.FuncAnimation(fig, update, frames=num_frames,

                                   interval=1500, repeat=True)

    

    plt.tight_layout()

    plt.show()





def visualize_bankers_static(available, maximum, allocation, test_request=None):

    """

    静态可视化银行家算法

    """

    bankers = BankersAlgorithm(available, maximum, allocation)

    

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    

    # ===== 左上：资源分配表 =====

    ax1 = axes[0, 0]

    ax1.axis('off')

    ax1.set_title('资源分配表', fontsize=13, fontweight='bold')

    

    resources = [f'R{i}' for i in range(bankers.num_resources)]

    headers = ['进程'] + [f'Max' for _ in resources] + \

              [f'Alloc' for _ in resources] + [f'Need' for _ in resources]

    

    table_data = []

    for i in range(bankers.num_processes):

        row = [f'P{i}']

        row.extend([str(m) for m in bankers.maximum[i]])

        row.extend([str(a) for a in bankers.allocation[i]])

        row.extend([str(n) for n in bankers.need[i]])

        table_data.append(row)

    

    table = ax1.table(cellText=table_data, colLabels=headers,

                     cellLoc='center', loc='center')

    table.auto_set_font_size(False)

    table.set_fontsize(10)

    table.scale(1.2, 2)

    

    # ===== 右上：Need矩阵热力图 =====

    ax2 = axes[0, 1]

    im = ax2.imshow(bankers.need, cmap='YlOrRd', aspect='auto')

    ax2.set_xticks(range(bankers.num_resources))

    ax2.set_xticklabels([f'R{i}' for i in range(bankers.num_resources)])

    ax2.set_yticks(range(bankers.num_processes))

    ax2.set_yticklabels([f'P{i}' for i in range(bankers.num_processes)])

    ax2.set_title('Need 矩阵 (需求)', fontsize=13, fontweight='bold')



    

    # 在格子中添加数值

    for i in range(bankers.num_processes):

        for j in range(bankers.num_resources):

            ax2.text(j, i, str(bankers.need[i, j]), ha='center', va='center', fontsize=12)

    

    plt.colorbar(im, ax=ax2, label='需求值')

    

    # ===== 左下：安全序列检测 =====

    ax3 = axes[1, 0]

    ax3.axis('off')

    ax3.set_title('安全序列检测', fontsize=13, fontweight='bold')

    

    is_safe, safe_seq, work_history = bankers.is_safe_state()

    

    # 显示检测过程

    info_text = f'Available: {list(bankers.available)}\n\n'

    info_text += '检测过程:\n'

    

    finish = [False] * bankers.num_processes

    work = bankers.available.copy()

    

    for step, p in enumerate(safe_seq):

        need_str = ' '.join([str(n) for n in bankers.need[p]])

        alloc_str = ' '.join([str(a) for a in bankers.allocation[p]])

        work_before = work.copy()

        work += bankers.allocation[p]

        finish[p] = True

        

        info_text += f'\n步骤{step+1}: 检查 P{p}\n'

        info_text += f'  Need(P{p}) = [{need_str}]\n'

        info_text += f'  Need ≤ Work? {bankers.need[p]} ≤ {work_before} = '

        info_text += f'{"✓" if np.all(bankers.need[p] <= work_before) else "✗"}\n'

        info_text += f'  分配: Work = {work_before} + [{alloc_str}] = {list(work)}\n'

    

    if is_safe:

        info_text += f'\n✓ 所有进程完成！系统处于安全状态。\n'

        info_text += f'  安全序列: {" → ".join([f"P{p}" for p in safe_seq])}'

        bg_color = 'lightgreen'

    else:

        deadlocked = bankers.find_deadlock()

        info_text += f'\n✗ 死锁！无法找到安全序列。\n'

        info_text += f'  死锁进程: {[f"P{p}" for p in deadlocked]}'

        bg_color = 'lightcoral'

    

    ax3.text(0.1, 0.9, info_text, fontsize=10, va='top', family='monospace',

            bbox=dict(boxstyle='round', facecolor=bg_color, alpha=0.5))

    

    # ===== 右下：进程状态图 =====

    ax4 = axes[1, 1]

    ax4.set_xlim(0, 10)

    ax4.set_ylim(0, 10)

    ax4.set_aspect('equal')

    ax4.axis('off')

    ax4.set_title('进程状态图', fontsize=13, fontweight='bold')

    

    deadlocked = bankers.find_deadlock() if not is_safe else []

    

    for i in range(bankers.num_processes):

        x = 2 + (i % 3) * 3

        y = 7 - (i // 3) * 3

        

        if i in deadlocked:

            color = '#FF6B6B'

        elif i in safe_seq:

            idx = safe_seq.index(i)

            color = plt.cm.Greens(0.4 + 0.6 * (idx / len(safe_seq)))

        else:

            color = '#87CEEB'

        

        circle = plt.Circle((x, y), 1, color=color, ec='black', linewidth=2)

        ax4.add_patch(circle)

        ax4.text(x, y, f'P{i}', ha='center', va='center', fontsize=14, fontweight='bold')

        

        # 标注状态

        if i in deadlocked:

            ax4.text(x, y - 1.5, 'DEADLOCK', ha='center', fontsize=9, color='red', fontweight='bold')

        elif i in safe_seq:

            ax4.text(x, y - 1.5, f'Done-{safe_seq.index(i)+1}', ha='center', fontsize=9, color='green')

    

    # 测试请求

    if test_request:

        process_id, request = test_request

        can_alloc, reason = bankers.simulate_request(process_id, request)

        

        ax4.text(5, 0.5, f'测试请求:\nP{process_id} 请求 {list(request)}\n{reason}',

                ha='center', fontsize=10,

                bbox=dict(boxstyle='round', facecolor='lightyellow' if can_alloc else 'lightcoral'))

    

    plt.tight_layout()

    plt.show()





if __name__ == '__main__':

    # 测试用例

    # 5个进程，3种资源类型

    available = [3, 3, 2]  # 可用资源

    

    # 最大需求矩阵

    maximum = [

        [7, 5, 3],  # P0

        [3, 2, 2],  # P1

        [9, 0, 2],  # P2

        [2, 2, 2],  # P3

        [4, 3, 3],  # P4

    ]

    

    # 已分配矩阵

    allocation = [

        [0, 1, 0],  # P0

        [2, 0, 0],  # P1

        [3, 0, 2],  # P2

        [2, 1, 1],  # P3

        [0, 0, 2],  # P4

    ]

    

    print("=" * 60)

    print("银行家算法可视化测试")

    print("=" * 60)

    print(f"可用资源 Available: {available}")

    print(f"\n最大需求矩阵 Max:\n{np.array(maximum)}")

    print(f"\n已分配矩阵 Allocation:\n{np.array(allocation)}")

    

    # 创建银行家算法实例

    bankers = BankersAlgorithm(available, maximum, allocation)

    

    # 计算Need矩阵

    print(f"\n需求矩阵 Need (= Max - Allocation):\n{bankers.need}")

    

    # 安全序列检测

    is_safe, safe_seq, work_history = bankers.is_safe_state()

    

    print(f"\n安全状态检查:")

    print(f"  是否安全: {'是' if is_safe else '否'}")

    if is_safe:

        print(f"  安全序列: {' → '.join([f'P{p}' for p in safe_seq])}")

    else:

        deadlocked = bankers.find_deadlock()

        print(f"  死锁进程: {[f'P{p}' for p in deadlocked]}")

    

    # 测试请求

    test_request = (0, [1, 0, 2])

    print(f"\n测试请求: P{test_request[0]} 请求 {test_request[1]}")

    can_alloc, reason = bankers.simulate_request(*test_request)

    print(f"  结果: {reason}")

    

    # 启动可视化

    print("\n" + "=" * 60)

    print("启动动态可视化...")

    print("=" * 60)

    visualize_bankers_algorithm(available, maximum, allocation)

    

    print("\n启动静态可视化...")

    visualize_bankers_static(available, maximum, allocation, test_request)

    

    print("\n测试完成!")

