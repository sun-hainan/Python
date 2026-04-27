# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / tower_of_hanoi

本文件实现 tower_of_hanoi 相关的算法功能。
"""

# move_tower 函数实现
def move_tower(height, from_pole, to_pole, with_pole):
    """
    >>> move_tower(3, 'A', 'B', 'C')
    moving disk from A to B
    moving disk from A to C
    moving disk from B to C
    moving disk from A to B
    moving disk from C to A
    moving disk from C to B
    moving disk from A to B
    """
    if height >= 1:
    # 条件判断
        move_tower(height - 1, from_pole, with_pole, to_pole)
        move_disk(from_pole, to_pole)
        move_tower(height - 1, with_pole, to_pole, from_pole)



# move_disk 函数实现
def move_disk(fp, tp):
    print("moving disk from", fp, "to", tp)



# main 函数实现
def main():
    height = int(input("Height of hanoi: ").strip())
    move_tower(height, "A", "B", "C")


if __name__ == "__main__":
    # 条件判断
    main()
