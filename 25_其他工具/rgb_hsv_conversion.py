# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / rgb_hsv_conversion

本文件实现 rgb_hsv_conversion 相关的算法功能。
"""

def hsv_to_rgb(hue: float, saturation: float, value: float) -> list[int]:
    """
    将 HSV 颜色转换为 RGB 颜色。
    
    Args:
        hue: 色相（0-360 度）
        saturation: 饱和度（0-1）
        value: 明度（0-1）
    
    Returns:
        [红色, 绿色, 蓝色]（每通道 0-255）
    
    示例:
        >>> hsv_to_rgb(0, 0, 0)
        [0, 0, 0]
        >>> hsv_to_rgb(0, 0, 1)
        [255, 255, 255]
        >>> hsv_to_rgb(0, 1, 1)
        [255, 0, 0]
    """
    if hue < 0 or hue > 360:
        raise Exception("hue should be between 0 and 360")

    if saturation < 0 or saturation > 1:
        raise Exception("saturation should be between 0 and 1")

    if value < 0 or value > 1:
        raise Exception("value should be between 0 and 1")

    #  chroma: 纯色分量
    chroma = value * saturation
    # hue_section: 色相段（0-5）
    hue_section = hue / 60
    # second_largest_component: 次大分量
    second_largest_component = chroma * (1 - abs(hue_section % 2 - 1))
    # match_value: 补偿值
    match_value = value - chroma

    if hue_section >= 0 and hue_section <= 1:
        red = round(255 * (chroma + match_value))
        green = round(255 * (second_largest_component + match_value))
        blue = round(255 * (match_value))
    elif hue_section > 1 and hue_section <= 2:
        red = round(255 * (second_largest_component + match_value))
        green = round(255 * (chroma + match_value))
        blue = round(255 * (match_value))
    elif hue_section > 2 and hue_section <= 3:
        red = round(255 * (match_value))
        green = round(255 * (chroma + match_value))
        blue = round(255 * (second_largest_component + match_value))
    elif hue_section > 3 and hue_section <= 4:
        red = round(255 * (match_value))
        green = round(255 * (second_largest_component + match_value))
        blue = round(255 * (chroma + match_value))
    elif hue_section > 4 and hue_section <= 5:
        red = round(255 * (second_largest_component + match_value))
        green = round(255 * (match_value))
        blue = round(255 * (chroma + match_value))
    else:
        red = round(255 * (chroma + match_value))
        green = round(255 * (match_value))
        blue = round(255 * (second_largest_component + match_value))

    return [red, green, blue]


def rgb_to_hsv(red: int, green: int, blue: int) -> list[float]:
    """
    将 RGB 颜色转换为 HSV 颜色。
    
    Args:
        red: 红色通道（0-255）
        green: 绿色通道（0-255）
        blue: 蓝色通道（0-255）
    
    Returns:
        [色相, 饱和度, 明度]
    
    示例:
        >>> approximately_equal_hsv(rgb_to_hsv(255, 0, 0), [0, 1, 1])
        True
    """
    if red < 0 or red > 255:
        raise Exception("red should be between 0 and 255")

    if green < 0 or green > 255:
        raise Exception("green should be between 0 and 255")

    if blue < 0 or blue > 255:
        raise Exception("blue should be between 0 and 255")

    float_red = red / 255
    float_green = green / 255
    float_blue = blue / 255
    
    # value: 最大通道值
    value = max(float_red, float_green, float_blue)
    # chroma: 最大和最小通道的差
    chroma = value - min(float_red, float_green, float_blue)
    # saturation: 纯度比例
    saturation = 0 if value == 0 else chroma / value

    if chroma == 0:
        hue = 0.0
    elif value == float_red:
        hue = 60 * (0 + (float_green - float_blue) / chroma)
    elif value == float_green:
        hue = 60 * (2 + (float_blue - float_red) / chroma)
    else:
        hue = 60 * (4 + (float_red - float_green) / chroma)

    hue = (hue + 360) % 360

    return [hue, saturation, value]


def approximately_equal_hsv(hsv_1: list[float], hsv_2: list[float]) -> bool:
    """
    检查两个 HSV 颜色是否近似相等（考虑浮点误差）。
    
    Args:
        hsv_1: 第一个 HSV 颜色
        hsv_2: 第二个 HSV 颜色
    
    Returns:
        True 如果近似相等
    
    示例:
        >>> approximately_equal_hsv([0, 0, 0], [0, 0, 0])
        True
    """
    check_hue = abs(hsv_1[0] - hsv_2[0]) < 0.2
    check_saturation = abs(hsv_1[1] - hsv_2[1]) < 0.002
    check_value = abs(hsv_1[2] - hsv_2[2]) < 0.002

    return check_hue and check_saturation and check_value


# ==========================================================
# 测试代码
# ==========================================================
if __name__ == "__main__":
    # 测试 HSV 转 RGB
    test_cases = [
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 1),
        (60, 1, 1),
        (120, 1, 1),
        (240, 1, 1),
    ]
    print("=== HSV 转 RGB 测试 ===")
    for h, s, v in test_cases:
        rgb = hsv_to_rgb(h, s, v)
        print(f"HSV({h}, {s}, {v}) -> RGB({rgb})")
    
    # 测试 RGB 转 HSV
    print("\n=== RGB 转 HSV 测试 ===")
    rgb_tests = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    for r, g, b in rgb_tests:
        hsv = rgb_to_hsv(r, g, b)
        print(f"RGB({r}, {g}, {b}) -> HSV({hsv[0]:.1f}, {hsv[1]:.2f}, {hsv[2]:.2f})")
