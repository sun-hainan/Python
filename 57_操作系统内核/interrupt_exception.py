# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / interrupt_exception



本文件实现 interrupt_exception 相关的算法功能。

"""



from typing import Dict, List, Optional, Callable

from dataclasses import dataclass

from enum import Enum





class ExceptionType(Enum):

    """异常类型"""

    DIVIDE_ERROR = 0

    DEBUG = 1

    NMI = 2

    BREAKPOINT = 3

    OVERFLOW = 4

    BOUNDS = 5

    INVALID_OPCODE = 6

    NO_DEVICE = 7

    DOUBLE_FAULT = 8

    Coprocessor_Segment_Overrun = 9

    INVALID_TSS = 10

    SEGMENT_NOT_PRESENT = 11

    STACK_FAULT = 12

    GENERAL_PROTECTION = 13

    PAGE_FAULT = 14

    RESERVED = 15

    MATH_FAULT = 16

    ALIGNMENT_CHECK = 17

    MACHINE_CHECK = 18

    SIMD_FP = 19





class InterruptType(Enum):

    """中断类型"""

    IRQ0_TIMER = 0x20

    IRQ1_KEYBOARD = 0x21

    IRQ2_CASCADE = 0x22

    IRQ3_COM2 = 0x23

    IRQ4_COM1 = 0x24

    IRQ6_FLOPPY = 0x26

    IRQ7_PARALLEL = 0x27

    IRQ8_RTC = 0x28

    IRQ12_MOUSE = 0x2C

    IRQ13_FPU = 0x2D

    IRQ14_IDE = 0x2E

    IRQ15_IDE = 0x2F





@dataclass

class IDTEntry:

    """中断描述符表条目"""

    offset_low: int = 0       # 偏移低16位

    selector: int = 0x08      # 代码段选择子

    zero: int = 0             # 必须是0

    type_attr: int = 0x8E     # 类型和属性

    offset_high: int = 0      # 偏移高16位



    def set_offset(self, offset: int):

        """设置处理程序偏移"""

        self.offset_low = offset & 0xFFFF

        self.offset_high = (offset >> 16) & 0xFFFF



    def get_offset(self) -> int:

        """获取处理程序偏移"""

        return self.offset_low | (self.offset_high << 16)





@dataclass

class TrapFrame:

    """陷阱帧（中断/异常时的CPU状态）"""

    # 通用寄存器

    eax: int = 0

    ebx: int = 0

    ecx: int = 0

    edx: int = 0

    esi: int = 0

    edi: int = 0

    ebp: int = 0



    # 特定寄存器

    esp: int = 0

    ss: int = 0

    eflags: int = 0

    eip: int = 0

    cs: int = 0

    error_code: int = 0





class InterruptDescriptorTable:

    """中断描述符表"""



    def __init__(self, num_entries: int = 256):

        self.num_entries = num_entries

        self.entries: List[IDTEntry] = [IDTEntry() for _ in range(num_entries)]



        # 处理函数映射

        self.handlers: Dict[int, Callable] = {}



    def set_gate(self, vector: int, handler: Callable, dpl: int = 0):

        """

        设置中断门

        param vector: 中断向量号

        param handler: 处理函数

        param dpl: 描述符优先级

        """

        entry = self.entries[vector]

        entry.set_offset(id(handler))

        entry.selector = 0x08  # 内核代码段

        entry.type_attr = 0x8E  # 32位中断门，DPL=0

        self.handlers[vector] = handler



    def get_handler(self, vector: int) -> Optional[Callable]:

        """获取处理函数"""

        return self.handlers.get(vector)





class InterruptController:

    """

    中断控制器（8259A PIC模拟）



    负责接收硬件中断并发送给CPU。

    """



    def __init__(self):

        # 中断请求寄存器

        self.irr: int = 0  # Interrupt Request Register

        self.isr: int = 0  # In-Service Register

        self.imr: int = 0  # Interrupt Mask Register



        # 挂起的中断

        self.pending_interrupts: List[int] = []



        # 中断处理中

        self.in_service: List[int] = []



    def raise_interrupt(self, irq: int):

        """触发中断"""

        self.irr |= (1 << irq)

        self.pending_interrupts.append(irq)

        print(f"  [PIC] IRQ{irq} 中断请求")



    def acknowledge_interrupt(self, irq: int):

        """响应中断"""

        if irq in self.pending_interrupts:

            self.pending_interrupts.remove(irq)

        self.irr &= ~(1 << irq)

        self.isr |= (1 << irq)

        self.in_service.append(irq)

        print(f"  [PIC] 响应 IRQ{irq}")



    def end_of_interrupt(self, irq: int):

        """中断结束"""

        if irq in self.in_service:

            self.in_service.remove(irq)

        self.isr &= ~(1 << irq)

        print(f"  [PIC] IRQ{irq} 处理完成")



    def mask_interrupt(self, irq: int):

        """屏蔽中断"""

        self.imr |= (1 << irq)

        print(f"  [PIC] 屏蔽 IRQ{irq}")



    def unmask_interrupt(self, irq: int):

        """取消屏蔽"""

        self.imr &= ~(1 << irq)

        print(f"  [PIC] 取消屏蔽 IRQ{irq}")





class ExceptionHandler:

    """异常处理"""



    @staticmethod

    def handle_divide_error(tf: TrapFrame):

        """除零错误 (#DE)"""

        print(f"\n[异常] 除零错误!")

        print(f"  EIP = 0x{tf.eip:08X}")

        return -1



    @staticmethod

    def handle_page_fault(tf: TrapFrame):

        """缺页错误 (#PF)"""

        print(f"\n[异常] 缺页错误!")

        print(f"  EIP = 0x{tf.eip:08X}")

        print(f"  错误码 = 0x{tf.error_code:X}")

        # P位

        present = tf.error_code & 1

        # W/R位

        write = (tf.error_code >> 1) & 1

        print(f"  页存在 = {present}, 写操作 = {write}")

        return -1



    @staticmethod

    def handle_general_protection(tf: TrapFrame):

        """通用保护错误 (#GP)"""

        print(f"\n[异常] 通用保护错误!")

        print(f"  EIP = 0x{tf.eip:08X}")

        print(f"  错误码 = 0x{tf.error_code:X}")

        return -1





class InterruptSimulator:

    """中断模拟器"""



    def __init__(self):

        self.idt = InterruptDescriptorTable()

        self.pic = InterruptController()

        self.current_tf: Optional[TrapFrame] = None



        # 初始化IDT

        self._setup_idt()



        # 统计

        self.interrupt_count = 0

        self.exception_count = 0



    def _setup_idt(self):

        """设置IDT"""

        # 设置异常处理

        self.idt.set_gate(ExceptionType.DIVIDE_ERROR.value,

                         ExceptionHandler.handle_divide_error)

        self.idt.set_gate(ExceptionType.PAGE_FAULT.value,

                         ExceptionHandler.handle_page_fault)

        self.idt.set_gate(ExceptionType.GENERAL_PROTECTION.value,

                         ExceptionHandler.handle_general_protection)



        # 设置硬件中断处理

        self.idt.set_gate(0x20, self.handle_timer_interrupt)

        self.idt.set_gate(0x21, self.handle_keyboard_interrupt)

        self.idt.set_gate(0x2C, self.handle_mouse_interrupt)



    def handle_timer_interrupt(self, tf: TrapFrame):

        """时钟中断处理"""

        print(f"  [时钟中断] 系统时间更新")

        return 0



    def handle_keyboard_interrupt(self, tf: TrapFrame):

        """键盘中断处理"""

        print(f"  [键盘中断] 读取键盘输入")

        return 0



    def handle_mouse_interrupt(self, tf: TrapFrame):

        """鼠标中断处理"""

        print(f"  [鼠标中断] 读取鼠标数据")

        return 0



    def trigger_exception(self, exc_type: ExceptionType, tf: TrapFrame):

        """触发异常"""

        handler = self.idt.get_handler(exc_type.value)

        if handler:

            self.exception_count += 1

            return handler(tf)

        return 0



    def trigger_interrupt(self, irq: int):

        """触发硬件中断"""

        handler = self.idt.get_handler(irq)

        if handler:

            self.pic.acknowledge_interrupt(irq)

            self.interrupt_count += 1

            return handler(self.current_tf)

        return 0





def simulate_interrupt_exception():

    """

    模拟中断与异常处理

    """

    print("=" * 60)

    print("中断与异常处理")

    print("=" * 60)



    # 创建模拟器

    sim = InterruptSimulator()



    # 创建陷阱帧

    tf = TrapFrame(eip=0x1000, cs=0x08, eflags=0x200)



    # 模拟异常

    print("\n" + "-" * 50)

    print("异常模拟")

    print("-" * 50)



    # 除零错误

    print("\n1. 触发除零错误:")

    result = sim.trigger_exception(ExceptionType.DIVIDE_ERROR, tf)

    print(f"   处理结果: {result}")



    # 缺页错误

    tf.error_code = 0x02  # 写操作

    print("\n2. 触发缺页错误:")

    result = sim.trigger_exception(ExceptionType.PAGE_FAULT, tf)

    print(f"   处理结果: {result}")



    # 模拟硬件中断

    print("\n" + "-" * 50)

    print("硬件中断模拟")

    print("-" * 50)



    print("\n3. 触发时钟中断 (IRQ0):")

    result = sim.trigger_interrupt(0x20)

    print(f"   处理结果: {result}")



    print("\n4. 触发键盘中断 (IRQ1):")

    result = sim.trigger_interrupt(0x21)

    print(f"   处理结果: {result}")



    # 统计

    print("\n" + "-" * 50)

    print("中断/异常统计")

    print("-" * 50)

    print(f"  异常数: {sim.exception_count}")

    print(f"  中断数: {sim.interrupt_count}")



    # IDT结构

    print("\n" + "-" * 50)

    print("IDT结构")

    print("-" * 50)

    print(f"  IDT条目数: {sim.idt.num_entries}")

    print(f"  已注册处理函数: {len(sim.idt.handlers)}")

    for vector in sorted(sim.idt.handlers.keys())[:5]:

        print(f"    向量 0x{vector:02X}: handler_{vector}")





if __name__ == "__main__":

    simulate_interrupt_exception()

