# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / mirror_formulae



本文件实现 mirror_formulae 相关的算法功能。

"""



def focal_length(distance_of_object: float, distance_of_image: float) -> float:

    """

    >>> from math import isclose

    >>> isclose(focal_length(10, 20), 6.66666666666666)

    True

    >>> from math import isclose

    >>> isclose(focal_length(9.5, 6.7), 3.929012346)

    True

    >>> focal_length(0, 20)  # doctest: +NORMALIZE_WHITESPACE

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter non zero values with respect

    to the sign convention.

    """



    if distance_of_object == 0 or distance_of_image == 0:

        raise ValueError(

            "Invalid inputs. Enter non zero values with respect to the sign convention."

        )

    focal_length = 1 / ((1 / distance_of_object) + (1 / distance_of_image))

    return focal_length





def object_distance(focal_length: float, distance_of_image: float) -> float:

    """

    >>> from math import isclose

    >>> isclose(object_distance(30, 20), -60.0)

    True

    >>> from math import isclose

    >>> isclose(object_distance(10.5, 11.7), 102.375)

    True

    >>> object_distance(90, 0)  # doctest: +NORMALIZE_WHITESPACE

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter non zero values with respect

    to the sign convention.

    """



    if distance_of_image == 0 or focal_length == 0:

        raise ValueError(

            "Invalid inputs. Enter non zero values with respect to the sign convention."

        )

    object_distance = 1 / ((1 / focal_length) - (1 / distance_of_image))

    return object_distance





def image_distance(focal_length: float, distance_of_object: float) -> float:

    """

    >>> from math import isclose

    >>> isclose(image_distance(10, 40), 13.33333333)

    True

    >>> from math import isclose

    >>> isclose(image_distance(1.5, 6.7), 1.932692308)

    True

    >>> image_distance(0, 0)  # doctest: +NORMALIZE_WHITESPACE

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter non zero values with respect

    to the sign convention.

    """



    if distance_of_object == 0 or focal_length == 0:

        raise ValueError(

            "Invalid inputs. Enter non zero values with respect to the sign convention."

        )

    image_distance = 1 / ((1 / focal_length) - (1 / distance_of_object))

    return image_distance





if __name__ == "__main__":

    print("=== 镜面成像公式测试 ===\n")



    # 凹面镜测试

    print("1. 凹面镜（物距10cm，像距20cm）:")

    f = focal_length(10, 20)

    print(f"   焦距 = {f:.4f} cm")



    # 已知焦距求物距

    print("\n2. 已知焦距30cm，像距20cm，求物距:")

    u = object_distance(30, 20)

    print(f"   物距 = {u:.4f} cm（负值表示虚物）")



    # 已知焦距求像距

    print("\n3. 已知焦距10cm，物距40cm，求像距:")

    v = image_distance(10, 40)

    print(f"   像距 = {v:.4f} cm")



    print("\n=== 镜面公式 ===")

    print("1/f = 1/v + 1/u")

    print("f: 焦距, v: 像距, u: 物距")

    print("符号约定：光线传播方向为正")

