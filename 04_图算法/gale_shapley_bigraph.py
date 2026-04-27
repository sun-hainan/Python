# -*- coding: utf-8 -*-

"""

算法实现：04_图算法 / gale_shapley_bigraph



本文件实现 gale_shapley_bigraph 相关的算法功能。

"""



from __future__ import annotations





def stable_matching(

    donor_pref: list[list[int]], recipient_pref: list[list[int]]

) -> list[int]:

    """

    计算 Gale-Shapley 稳定匹配。



    在稳定匹配中，不存在任何一对个体互相更喜欢对方。



    Args:

        donor_pref: 每个捐赠者（proposer）的偏好列表

                    donor_pref[i] 表示第 i 个捐赠者对所有接收者的排序

        recipient_pref: 每个接收者的偏好列表

                        recipient_pref[j] 表示第 j 个接收者对所有捐赠者的排序



    Returns:

        长度为 n 的列表，其中第 i 个元素表示与第 i 个捐赠者匹配的接收者



    示例:

        >>> donor_pref = [[0, 1, 3, 2], [0, 2, 3, 1], [1, 0, 2, 3], [0, 3, 1, 2]]

        >>> recipient_pref = [[3, 1, 2, 0], [3, 1, 0, 2], [0, 3, 1, 2], [1, 0, 3, 2]]

        >>> stable_matching(donor_pref, recipient_pref)

        [1, 2, 3, 0]

    """

    assert len(donor_pref) == len(recipient_pref)



    n = len(donor_pref)

    # 未匹配的捐赠者队列

    unmatched_donors = list(range(n))

    # donor_record[i]: 捐赠者 i 当前匹配到的接收者（-1 表示未匹配）

    donor_record = [-1] * n

    # rec_record[j]: 接收者 j 当前匹配到的捐赠者（-1 表示未匹配）

    rec_record = [-1] * n

    # num_donations[i]: 捐赠者 i 已拒绝的接收者数（用于遍历偏好）

    num_donations = [0] * n



    while unmatched_donors:

        # 取出一个未匹配捐赠者

        donor = unmatched_donors[0]

        # 获取当前偏好的接收者

        donor_preference = donor_pref[donor]

        recipient = donor_preference[num_donations[donor]]

        num_donations[donor] += 1



        # 获取该接收者的偏好

        rec_preference = recipient_pref[recipient]

        # 获取该接收者当前的匹配者

        prev_donor = rec_record[recipient]



        if prev_donor != -1:

            # 接收者已有匹配，比较两个捐赠者的优先级

            if rec_preference.index(prev_donor) > rec_preference.index(donor):

                # 当前捐赠者更优：替换匹配，原匹配者变为未匹配

                rec_record[recipient] = donor

                donor_record[donor] = recipient

                unmatched_donors.append(prev_donor)

                unmatched_donors.remove(donor)

            else:

                # 原匹配者更优：拒绝当前捐赠者，继续等待

                pass

        else:

            # 接收者未匹配：直接接受

            rec_record[recipient] = donor

            donor_record[donor] = recipient

            unmatched_donors.remove(donor)



    return donor_record





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    # 示例：4对捐赠者-接收者的稳定匹配

    # 捐赠者 0 偏好顺序: 0 > 1 > 3 > 2

    # 接收者 0 偏好顺序: 3 > 1 > 2 > 0

    donor_pref = [

        [0, 1, 3, 2],

        [0, 2, 3, 1],

        [1, 0, 2, 3],

        [0, 3, 1, 2]

    ]

    recipient_pref = [

        [3, 1, 2, 0],

        [3, 1, 0, 2],

        [0, 3, 1, 2],

        [1, 0, 3, 2]

    ]

    result = stable_matching(donor_pref, recipient_pref)

    print("稳定匹配结果（捐赠者 -> 接收者）:", result)

    print("每个捐赠者 i 的匹配接收者为 result[i]")

