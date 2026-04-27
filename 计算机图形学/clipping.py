# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / clipping



本文件实现 clipping 相关的算法功能。

"""



import numpy as np





INSIDE, LEFT, RIGHT, LOWER, UPPER = 0, 1, 2, 4, 8





def compute_code(x, y, xmin, ymin, xmax, ymax):

    code = INSIDE

    if x < xmin: code |= LEFT

    elif x > xmax: code |= RIGHT

    if y < ymin: code |= LOWER

    elif y > ymax: code |= UPPER

    return code





def cohen_sutherland(x1, y1, x2, y2, xmin, ymin, xmax, ymax):

    """Cohen-Sutherland 裁剪"""

    code1 = compute_code(x1, y1, xmin, ymin, xmax, ymax)

    code2 = compute_code(x2, y2, xmin, ymin, xmax, ymax)

    accept = False



    while True:

        if not (code1 | code2):

            accept = True

            break

        elif code1 & code2:

            break

        else:

            if code1 != INSIDE:

                code_out = code1

            else:

                code_out = code2

            if code_out & LOWER:

                x = x1 + (x2-x1)*(ymin-y1)/(y2-y1)

                y = ymin

            elif code_out & UPPER:

                x = x1 + (x2-x1)*(ymax-y1)/(y2-y1)

                y = ymax

            elif code_out & RIGHT:

                y = y1 + (y2-y1)*(xmax-x1)/(x2-x1)

                x = xmax

            else:

                y = y1 + (y2-y1)*(xmin-x1)/(x2-x1)

                x = xmin

            if code_out == code1:

                x1, y1 = x, y

                code1 = compute_code(x1, y1, xmin, ymin, xmax, ymax)

            else:

                x2, y2 = x, y

                code2 = compute_code(x2, y2, xmin, ymin, xmax, ymax)



    if accept:

        return (x1, y1), (x2, y2)

    return None





if __name__ == "__main__":

    # 测试各种线段

    test_cases = [

        (0.5, 0.5, 1.5, 1.5),

        (-0.5, 0.5, 1.5, 0.5),

        (0.5, -0.5, 0.5, 1.5),

    ]

    xmin, ymin, xmax, ymax = 0, 0, 1, 1



    print("Cohen-Sutherland 裁剪测试:")

    for x1, y1, x2, y2 in test_cases:

        result = cohen_sutherland(x1, y1, x2, y2, xmin, ymin, xmax, ymax)

        if result:

            print(f"  ({x1:.1f},{y1:.1f})-({x2:.1f},{y2:.1f}) -> ({result[0][0]:.2f},{result[0][1]:.2f})-({result[1][0]:.2f},{result[1][1]:.2f})")

        else:

            print(f"  ({x1:.1f},{y1:.1f})-({x2:.1f},{y2:.1f}) -> 舍弃")

    print("\n裁剪测试完成!")

