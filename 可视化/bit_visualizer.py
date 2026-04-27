# -*- coding: utf-8 -*-

"""

算法实现：可视化 / bit_visualizer



本文件实现 bit_visualizer 相关的算法功能。

"""



#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

位运算可视化器

使用 matplotlib 动画展示二进制数的位操作：AND、OR、XOR、左移、右移

支持逐位动画展示



使用方法:

    python bit_visualizer.py                  # 静态展示

    python bit_visualizer.py --animate        # 动画展示

    python bit_visualizer.py --gif            # 生成 GIF

"""



import matplotlib.pyplot as plt

import matplotlib.animation as animation

import numpy as np



# ============== 全局配置 ==============

# 动画帧间隔（毫秒）

FRAME_INTERVAL = 400

# 位数（默认8位）

NUM_BITS = 8

# 颜色配置

COLOR_0 = '#95a5a6'       # 0 位颜色（灰）

COLOR_1 = '#e74c3c'       # 1 位颜色（红）

COLOR_RESULT = '#3498db'  # 结果位颜色（蓝）

COLOR_HIGHLIGHT = '#f1c40f'  # 高亮颜色（黄）

COLOR_OPERATOR = '#2ecc71'  # 操作符颜色





# ============== 位运算类 ==============



class BitOperation:

    """位运算操作类"""

    

    def __init__(self, num, num_bits=NUM_BITS):

        self.num = num

        self.num_bits = num_bits

        self.binary = self._to_binary(num)

        self.history = []  # 操作历史

    

    def _to_binary(self, num):

        """将数字转换为二进制列表（高位在前）"""

        binary_str = format(num, f'0{self.num_bits}b')

        return [int(b) for b in binary_str]

    

    def _to_int(self, binary_list):

        """将二进制列表转换为整数"""

        return int(''.join(str(b) for b in binary_list), 2)

    

    def get_bit_string(self):

        """获取可读二进制字符串"""

        return ''.join(str(b) for b in self.binary)





class BitVisualizer:

    """位运算可视化器类"""

    

    def __init__(self, num1, num2=None, num_bits=NUM_BITS):

        self.num1 = BitOperation(num1, num_bits)

        self.num2 = BitOperation(num2, num_bits) if num2 is not None else None

        self.result = None

        self.history = []  # 动画历史

        self.num_bits = num_bits

    

    def _add_history(self, state):

        """添加历史状态"""

        self.history.append(state)

    

    def and_op(self):

        """AND 运算"""

        if self.num2 is None:

            raise ValueError("AND 运算需要两个操作数")

        

        result_binary = [a & b for a, b in zip(self.num1.binary, self.num2.binary)]

        self.result = BitOperation(self._to_int(result_binary), self.num_bits)

        self.result.binary = result_binary

        

        # 记录逐位操作历史

        for i in range(self.num_bits):

            bit1 = self.num1.binary[i]

            bit2 = self.num2.binary[i]

            result_bit = bit1 & bit2

            

            self._add_history({

                'step': i + 1,

                'action': 'and',

                'bit_index': i,

                'bit1': bit1,

                'bit2': bit2,

                'result_bit': result_bit,

                'cumulative_result': result_binary[:i+1],

                'message': f"位 {i}: {bit1} AND {bit2} = {result_bit}"

            })

        

        return self.result

    

    def or_op(self):

        """OR 运算"""

        if self.num2 is None:

            raise ValueError("OR 运算需要两个操作数")

        

        result_binary = [a | b for a, b in zip(self.num1.binary, self.num2.binary)]

        self.result = BitOperation(self._to_int(result_binary), self.num_bits)

        self.result.binary = result_binary

        

        for i in range(self.num_bits):

            bit1 = self.num1.binary[i]

            bit2 = self.num2.binary[i]

            result_bit = bit1 | bit2

            

            self._add_history({

                'step': i + 1,

                'action': 'or',

                'bit_index': i,

                'bit1': bit1,

                'bit2': bit2,

                'result_bit': result_bit,

                'cumulative_result': result_binary[:i+1],

                'message': f"位 {i}: {bit1} OR {bit2} = {result_bit}"

            })

        

        return self.result

    

    def xor_op(self):

        """XOR 运算"""

        if self.num2 is None:

            raise ValueError("XOR 运算需要两个操作数")

        

        result_binary = [a ^ b for a, b in zip(self.num1.binary, self.num2.binary)]

        self.result = BitOperation(self._to_int(result_binary), self.num_bits)

        self.result.binary = result_binary

        

        for i in range(self.num_bits):

            bit1 = self.num1.binary[i]

            bit2 = self.num2.binary[i]

            result_bit = bit1 ^ bit2

            

            self._add_history({

                'step': i + 1,

                'action': 'xor',

                'bit_index': i,

                'bit1': bit1,

                'bit2': bit2,

                'result_bit': result_bit,

                'cumulative_result': result_binary[:i+1],

                'message': f"位 {i}: {bit1} XOR {bit2} = {result_bit}"

            })

        

        return self.result

    

    def left_shift(self, shift_amount):

        """左移运算"""

        result_num = self.num1.num << shift_amount

        self.result = BitOperation(result_num, self.num_bits + shift_amount + 2)

        

        # 计算移位后的二进制（扩展位数显示）

        original_binary = self.num1.binary

        result_binary = [0] * shift_amount + original_binary

        

        # 记录移位历史

        for step in range(shift_amount + 1):

            current_result = [0] * step + original_binary + [0] * (shift_amount - step)

            self._add_history({

                'step': step,

                'action': 'left_shift',

                'shift_amount': shift_amount,

                'partial_result': current_result,

                'message': f"左移 {step}/{shift_amount} 位"

            })

        

        self.result.binary = result_binary

        return self.result

    

    def right_shift(self, shift_amount):

        """右移运算"""

        result_num = self.num1.num >> shift_amount

        self.result = BitOperation(result_num, self.num_bits)

        

        # 计算移位后的二进制

        original_binary = self.num1.binary

        result_binary = original_binary[shift_amount:]

        

        # 记录移位历史

        for step in range(shift_amount + 1):

            dropped_bits = original_binary[:step]

            remaining = original_binary[step:]

            current_result = remaining + [0] * step

            self._add_history({

                'step': step,

                'action': 'right_shift',

                'shift_amount': shift_amount,

                'dropped_bits': dropped_bits,

                'partial_result': current_result,

                'message': f"右移 {step}/{shift_amount} 位，移出: {dropped_bits}"

            })

        

        self.result.binary = result_binary

        return self.result

    

    def _to_int(self, binary_list):

        """将二进制列表转换为整数"""

        return int(''.join(str(b) for b in binary_list), 2)

    

    def _get_bit_color(self, bit):

        """根据位值获取颜色"""

        return COLOR_1 if bit else COLOR_0

    

    def _draw_binary_row(self, ax, y_pos, binary_list, colors, labels=None, heights=0.6):

        """绘制一行二进制位"""

        n = len(binary_list)

        x_positions = np.arange(n)

        

        for i, (bit, color) in enumerate(zip(binary_list, colors)):

            # 绘制位方块

            rect = plt.Rectangle((i-0.3, y_pos-heights/2), 0.6, heights,

                                 facecolor=color, edgecolor='black', linewidth=1)

            ax.add_patch(rect)

            

            # 显示位值

            ax.text(i, y_pos, str(bit), ha='center', va='center',

                   fontsize=16, fontweight='bold', color='white')

            

            # 显示位索引标签（顶部）

            ax.text(i, y_pos + heights/2 + 0.3, f"2^{n-1-i}",

                   ha='center', va='bottom', fontsize=8, color='gray')

            

            # 显示标签（底部）

            if labels and i < len(labels):

                ax.text(i, y_pos - heights/2 - 0.3, labels[i],

                       ha='center', va='top', fontsize=9, color='black')

        

        return y_pos

    

    def plot_static(self, save_path=None):

        """绘制静态图"""

        fig, ax = plt.subplots(figsize=(14, 10))

        

        ax.set_xlim(-1, self.num_bits + 1)

        ax.set_ylim(-1, 5)

        ax.axis('off')

        

        # 如果有结果操作，显示操作过程

        if self.result and len(self.history) > 0:

            self._draw_static_operation(ax)

        else:

            # 显示单个数字的二进制

            self._draw_binary_row(ax, 2, self.num1.binary, 

                                 [self._get_bit_color(b) for b in self.num1.binary],

                                 labels=[f"{self.num1.num}"])

        

        plt.tight_layout()

        if save_path:

            plt.savefig(save_path, dpi=150, bbox_inches='tight')

            print(f"图片已保存到: {save_path}")

        plt.show()

    

    def _draw_static_operation(self, ax):

        """绘制静态操作图（两数运算）"""

        if self.num2 is None:

            return

        

        # 绘制操作数1

        y1 = 3.5

        colors1 = [COLOR_1 if b else COLOR_0 for b in self.num1.binary]

        self._draw_binary_row(ax, y1, self.num1.binary, colors1, labels=['A1'])

        

        # 绘制操作符

        action = self.history[0]['action'] if self.history else 'AND'

        ax.text(self.num_bits + 0.5, y1, action, fontsize=14, 

               color=COLOR_OPERATOR, fontweight='bold')

        

        # 绘制操作数2

        y2 = 2

        colors2 = [COLOR_1 if b else COLOR_0 for b in self.num2.binary]

        self._draw_binary_row(ax, y2, self.num2.binary, colors2, labels=['A2'])

        

        # 绘制分隔线

        ax.axhline(y=1.2, color='gray', linestyle='--', alpha=0.5)

        

        # 绘制结果

        y3 = 0.5

        colors3 = [COLOR_RESULT if b else COLOR_0 for b in self.result.binary]

        self._draw_binary_row(ax, y3, self.result.binary, colors3, labels=['Result'])

        

        # 添加标题

        result_value = self.result.num if self.result else 0

        ax.text(0, 4.5, f"位运算结果: {result_value} (0b{self.result.get_bit_string()})",

               fontsize=12, fontweight='bold')

    

    def plot_animate(self, save_gif=False, gif_path='bit_animation.gif'):

        """绘制动画"""

        fig, ax = plt.subplots(figsize=(14, 12))

        

        info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,

                           verticalalignment='top', fontsize=11,

                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        

        def init():

            return []

        

        def update(frame):

            ax.clear()

            ax.set_xlim(-1, self.num_bits + 1)

            ax.set_ylim(-1, 6)

            ax.axis('off')

            

            state = self.history[frame]

            

            # 更新信息

            info_text.set_text(

                f"步骤: {state['step']}/{len(self.history)}\n"

                f"{state['message']}\n"

                f"累计结果: {self._bits_to_int(state.get('cumulative_result', [])) if 'cumulative_result' in state else 'N/A'}"

            )

            

            if state['action'] in ['and', 'or', 'xor']:

                self._draw_binary_op_animate(ax, state)

            elif state['action'] in ['left_shift', 'right_shift']:

                self._draw_shift_animate(ax, state)

            

            return []

        

        ani = animation.FuncAnimation(fig, update, frames=len(self.history),

                                     init_func=init, blit=False, interval=FRAME_INTERVAL)

        

        if save_gif:

            print("正在生成 GIF，请稍候...")

            ani.save(gif_path, writer='pillow', fps=5)

            print(f"GIF 已保存到: {gif_path}")

        

        plt.show()

        return ani

    

    def _draw_binary_op_animate(self, ax, state):

        """绘制二元运算动画帧"""

        action = state['action']

        

        # 绘制操作数1

        colors1 = []

        for i in range(self.num_bits):

            if i == state['bit_index']:

                colors1.append(COLOR_HIGHLIGHT)

            else:

                colors1.append(COLOR_1 if self.num1.binary[i] else COLOR_0)

        self._draw_binary_row(ax, 4, self.num1.binary, colors1, labels=['num1'])

        

        # 绘制操作符

        op_symbol = {'and': 'AND', 'or': 'OR', 'xor': 'XOR'}[action]

        ax.text(self.num_bits + 0.5, 4, op_symbol, fontsize=14,

               color=COLOR_OPERATOR, fontweight='bold')

        

        # 绘制操作数2

        colors2 = []

        for i in range(self.num_bits):

            if i == state['bit_index']:

                colors2.append(COLOR_HIGHLIGHT)

            else:

                colors2.append(COLOR_1 if self.num2.binary[i] else COLOR_0)

        self._draw_binary_row(ax, 2.5, self.num2.binary, colors2, labels=['num2'])

        

        # 绘制分隔线

        ax.axhline(y=1.8, color='gray', linestyle='--', alpha=0.5)

        

        # 绘制结果

        result_colors = []

        for i in range(self.num_bits):

            if i < state['bit_index']:

                # 已计算完成

                result_colors.append(COLOR_RESULT if state['cumulative_result'][i] else COLOR_0)

            elif i == state['bit_index']:

                # 当前计算中

                result_colors.append(COLOR_HIGHLIGHT)

            else:

                # 未计算

                result_colors.append('#dddddd')

        

        result_display = state['cumulative_result'] + [0] * (self.num_bits - len(state['cumulative_result']))

        self._draw_binary_row(ax, 1, result_display, result_colors, labels=['result'])

        

        # 显示当前位计算

        ax.text(0, 0.2, f"计算: {state['bit1']} {op_symbol} {state['bit2']} = {state['result_bit']}",

               fontsize=14, fontweight='bold', color=COLOR_HIGHLIGHT)

    

    def _draw_shift_animate(self, ax, state):

        """绘制移位运算动画帧"""

        shift_amount = state['shift_amount']

        partial = state.get('partial_result', [])

        

        if state['action'] == 'left_shift':

            # 左移：高位补0，低位移出

            # 显示原始值

            self._draw_binary_row(ax, 4, self.num1.binary, 

                                 [COLOR_1 if b else COLOR_0 for b in self.num1.binary],

                                 labels=['原值'])

            

            # 绘制箭头

            ax.annotate('', xy=(self.num_bits + 0.3, 2.5), xytext=(self.num_bits, 4),

                       arrowprops=dict(arrowstyle='->', color='gray'))

            ax.text(self.num_bits + 0.5, 3.2, f"<< {shift_amount}", fontsize=12)

            

            # 显示结果

            colors = []

            for i, bit in enumerate(partial):

                if i < state['step']:

                    colors.append(COLOR_RESULT)

                elif i == state['step']:

                    colors.append(COLOR_HIGHLIGHT)

                else:

                    colors.append(COLOR_0)

            

            self._draw_binary_row(ax, 2.5, partial, colors, labels=['结果'])

            

            # 移位说明

            ax.text(0, 1.5, f"左移 {state['step']}/{shift_amount} 位，{shift_amount - state['step']} 个 0 待移入",

                   fontsize=11)

        

        else:  # right_shift

            # 右移：低位移出，高位补0

            self._draw_binary_row(ax, 4, self.num1.binary,

                                 [COLOR_1 if b else COLOR_0 for b in self.num1.binary],

                                 labels=['原值'])

            

            ax.annotate('', xy=(self.num_bits + 0.3, 2.5), xytext=(self.num_bits, 4),

                       arrowprops=dict(arrowstyle='->', color='gray'))

            ax.text(self.num_bits + 0.5, 3.2, f">> {shift_amount}", fontsize=12)

            

            colors = []

            for i, bit in enumerate(partial):

                if i < self.num_bits - state['step']:

                    colors.append(COLOR_RESULT)

                else:

                    colors.append(COLOR_0)

            

            self._draw_binary_row(ax, 2.5, partial[:self.num_bits], colors, labels=['结果'])

            

            dropped = state.get('dropped_bits', [])

            ax.text(0, 1.5, f"右移 {state['step']}/{shift_amount} 位，移出的位: {dropped}",

                   fontsize=11)

    

    def _bits_to_int(self, bits):

        """将位列表转换为整数"""

        if not bits:

            return 0

        return int(''.join(str(b) for b in bits), 2)





def demo_and():

    """演示 AND 运算"""

    print("=" * 50)

    print("位运算可视化 - AND 运算")

    print("=" * 50)

    

    viz = BitVisualizer(0b10101010, 0b11110000, num_bits=8)

    result = viz.and_op()

    

    print(f"操作数1: {viz.num1.num} (0b{viz.num1.get_bit_string()})")

    print(f"操作数2: {viz.num2.num} (0b{viz.num2.get_bit_string()})")

    print(f"结果:    {result.num} (0b{result.get_bit_string()})")

    

    return viz





def demo_or():

    """演示 OR 运算"""

    print("\n" + "=" * 50)

    print("位运算可视化 - OR 运算")

    print("=" * 50)

    

    viz = BitVisualizer(0b10101010, 0b11110000, num_bits=8)

    result = viz.or_op()

    

    print(f"操作数1: {viz.num1.num} (0b{viz.num1.get_bit_string()})")

    print(f"操作数2: {viz.num2.num} (0b{viz.num2.get_bit_string()})")

    print(f"结果:    {result.num} (0b{result.get_bit_string()})")

    

    return viz





def demo_xor():

    """演示 XOR 运算"""

    print("\n" + "=" * 50)

    print("位运算可视化 - XOR 运算")

    print("=" * 50)

    

    viz = BitVisualizer(0b10101010, 0b11110000, num_bits=8)

    result = viz.xor_op()

    

    print(f"操作数1: {viz.num1.num} (0b{viz.num1.get_bit_string()})")

    print(f"操作数2: {viz.num2.num} (0b{viz.num2.get_bit_string()})")

    print(f"结果:    {result.num} (0b{result.get_bit_string()})")

    

    return viz





def demo_left_shift():

    """演示左移运算"""

    print("\n" + "=" * 50)

    print("位运算可视化 - 左移运算")

    print("=" * 50)

    

    viz = BitVisualizer(0b00010101, num_bits=8)

    result = viz.left_shift(3)

    

    print(f"原值:  {viz.num1.num} (0b{viz.num1.get_bit_string()})")

    print(f"左移3: {result.num} (0b{result.get_bit_string()})")

    

    return viz





def demo_right_shift():

    """演示右移运算"""

    print("\n" + "=" * 50)

    print("位运算可视化 - 右移运算")

    print("=" * 50)

    

    viz = BitVisualizer(0b10101000, num_bits=8)

    result = viz.right_shift(3)

    

    print(f"原值:  {viz.num1.num} (0b{viz.num1.get_bit_string()})")

    print(f"右移3: {result.num} (0b{result.get_bit_string()})")

    

    return viz





def main():

    """主函数"""

    import argparse

    

    parser = argparse.ArgumentParser(description='位运算可视化')

    parser.add_argument('--animate', action='store_true', help='显示动画')

    parser.add_argument('--gif', action='store_true', help='生成 GIF')

    parser.add_argument('--op', type=str, default='all', 

                       choices=['and', 'or', 'xor', 'lshift', 'rshift', 'all'],

                       help='选择操作类型')

    args = parser.parse_args()

    

    if args.gif or args.animate:

        if args.op == 'and':

            viz = demo_and()

            viz.plot_animate(save_gif=args.gif)

        elif args.op == 'or':

            viz = demo_or()

            viz.plot_animate(save_gif=args.gif)

        elif args.op == 'xor':

            viz = demo_xor()

            viz.plot_animate(save_gif=args.gif)

        elif args.op == 'lshift':

            viz = demo_left_shift()

            viz.plot_animate(save_gif=args.gif)

        elif args.op == 'rshift':

            viz = demo_right_shift()

            viz.plot_animate(save_gif=args.gif)

        else:

            # 默认演示 AND

            viz = demo_and()

            viz.plot_animate(save_gif=args.gif)

    else:

        # 静态展示所有操作

        demo_and()

        demo_or()

        demo_xor()

        demo_left_shift()

        demo_right_shift()

    

    print("\n可视化完成!")





if __name__ == '__main__':

    main()

