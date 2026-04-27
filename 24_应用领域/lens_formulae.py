# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / lens_formulae



本文件实现 lens_formulae 相关的算法功能。

"""



def focal_length_of_lens(

    object_distance_from_lens: float, image_distance_from_lens: float

) -> float:

    """

    Doctests:

    >>> from math import isclose

    >>> isclose(focal_length_of_lens(10,4), 6.666666666666667)

    True

    >>> from math import isclose

    >>> isclose(focal_length_of_lens(2.7,5.8), -5.0516129032258075)

    True

    >>> focal_length_of_lens(0, 20)  # doctest: +NORMALIZE_WHITESPACE

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter non zero values with respect

    to the sign convention.

    """



    if object_distance_from_lens == 0 or image_distance_from_lens == 0:

        raise ValueError(

            "Invalid inputs. Enter non zero values with respect to the sign convention."

        )

    focal_length = 1 / (

        (1 / image_distance_from_lens) - (1 / object_distance_from_lens)

    )

    return focal_length





def object_distance(

    focal_length_of_lens: float, image_distance_from_lens: float

) -> float:

    """

    Doctests:

    >>> from math import isclose

    >>> isclose(object_distance(10,40), -13.333333333333332)

    True



    >>> from math import isclose

    >>> isclose(object_distance(6.2,1.5), 1.9787234042553192)

    True



    >>> object_distance(0, 20)  # doctest: +NORMALIZE_WHITESPACE

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter non zero values with respect

    to the sign convention.

    """



    if image_distance_from_lens == 0 or focal_length_of_lens == 0:

        raise ValueError(

            "Invalid inputs. Enter non zero values with respect to the sign convention."

        )



    object_distance = 1 / ((1 / image_distance_from_lens) - (1 / focal_length_of_lens))

    return object_distance





def image_distance(

    focal_length_of_lens: float, object_distance_from_lens: float

) -> float:

    """

    Doctests:

    >>> from math import isclose

    >>> isclose(image_distance(50,40), 22.22222222222222)

    True

    >>> from math import isclose

    >>> isclose(image_distance(5.3,7.9), 3.1719696969696973)

    True



    >>> object_distance(0, 20)  # doctest: +NORMALIZE_WHITESPACE

    Traceback (most recent call last):

        ...

    ValueError: Invalid inputs. Enter non zero values with respect

    to the sign convention.

    """

    if object_distance_from_lens == 0 or focal_length_of_lens == 0:

        raise ValueError(

            "Invalid inputs. Enter non zero values with respect to the sign convention."

        )

    image_distance = 1 / ((1 / object_distance_from_lens) + (1 / focal_length_of_lens))

    return image_distance





if __name__ == "__main__":

    print("=== 透镜成像公式测试 ===\n")



    # 凸透镜成像测试

    print("1. 凸透镜成像（物距10cm，像距40cm）:")

    f = focal_length_of_lens(10, 40)

    print(f"   焦距 = {f:.4f} cm")



    # 凹透镜成像测试

    print("\n2. 凹透镜成像（物距2.7m，像距5.8m）:")

    f = focal_length_of_lens(2.7, 5.8)

    print(f"   焦距 = {f:.4f} m（负值表示凹透镜）")



    # 已知焦距求物距

    print("\n3. 已知焦距10cm，像距40cm，求物距:")

    u = object_distance(10, 40)

    print(f"   物距 = {u:.4f} cm")



    # 已知焦距求像距

    print("\n4. 已知焦距50cm，物距40cm，求像距:")

    v = image_distance(50, 40)

    print(f"   像距 = {v:.4f} cm")



    print("\n=== 透镜公式 ===")

    print("1/f = 1/v + 1/u")

    print("f: 焦距, v: 像距, u: 物距")

    print("符号约定：实为正，虚为负")

