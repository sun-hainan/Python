# -*- coding: utf-8 -*-

"""

算法实现：差分隐私 / privacy_database



本文件实现 privacy_database 相关的算法功能。

"""



import numpy as np

from typing import List, Dict, Tuple





class PrivateDatabase:

    """隐私数据库"""



    def __init__(self, data: Dict[str, List], epsilon: float = 1.0):

        """

        参数：

            data: 数据库（列名 -> 值列表）

            epsilon: 隐私预算

        """

        self.data = data

        self.epsilon = epsilon

        self.n_rows = len(list(data.values())[0])



    def count_query(self, predicate: callable) -> Tuple[int, float]:

        """

        计数查询



        参数：

            predicate: 行过滤条件



        返回：(计数, 添加的噪声)

        """

        true_count = sum(1 for i in range(self.n_rows) if predicate(i))



        # 敏感度 = 1（计数查询）

        sensitivity = 1.0



        # 添加Laplace噪声

        scale = sensitivity / self.epsilon

        noise = np.random.laplace(0, scale)



        noisy_count = int(round(true_count + noise))



        return noisy_count, abs(noise)



    def sum_query(self, column: str, predicate: callable = None) -> Tuple[float, float]:

        """

        求和查询



        参数：

            column: 列名

            predicate: 可选过滤条件



        返回：(和, 添加的噪声)

        """

        values = self.data[column]



        if predicate is None:

            true_sum = sum(values)

        else:

            true_sum = sum(v for i, v in enumerate(values) if predicate(i))



        # 敏感度 = max - min（范围）

        sensitivity = max(values) - min(values)



        scale = sensitivity / self.epsilon

        noise = np.random.laplace(0, scale)



        noisy_sum = true_sum + noise



        return noisy_sum, abs(noise)



    def average_query(self, column: str, predicate: callable = None) -> float:

        """

        平均查询（组合count和sum）



        参数：

            column: 列名

            predicate: 可选过滤条件



        返回：平均值的估计

        """

        # 计数

        if predicate is None:

            count = self.n_rows

        else:

            count = sum(1 for i in range(self.n_rows) if predicate(i))



        # 求和

        sum_val, _ = self.sum_query(column, predicate)



        return sum_val / count if count > 0 else 0.0



    def range_query(self, column: str, low: float, high: float) -> Tuple[int, float]:

        """

        范围查询



        参数：

            column: 列名

            low, high: 范围



        返回：范围内的计数

        """

        def predicate(i):

            return low <= self.data[column][i] <= high



        return self.count_query(predicate)





def database_privacy_applications():

    """数据库隐私应用"""

    print("=== 数据库隐私应用 ===")

    print()

    print("1. 医疗数据")

    print("   - 统计疾病分布")

    print("   - 保护患者隐私")

    print()

    print("2. 位置数据")

    print("   - 人流分析")

    print("   - 不暴露个人轨迹")

    print()

    print("3. 用户行为")

    print("   - 产品推荐")

    print("   - 保护用户隐私")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 隐私数据库查询测试 ===\n")



    # 创建模拟数据库

    data = {

        'age': [25, 30, 35, 40, 45, 50, 55, 60],

        'salary': [50000, 60000, 70000, 80000, 90000, 100000, 110000, 120000],

        'department': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B']

    }



    epsilon = 1.0

    db = PrivateDatabase(data, epsilon)



    print(f"数据库: {len(data)} 列, {db.n_rows} 行")

    print(f"隐私预算: ε = {epsilon}")

    print()



    # 计数查询

    def dept_a(i):

        return data['department'][i] == 'A'



    count, noise = db.count_query(dept_a)

    print(f"部门A人数: {count} (噪声: {noise:.2f})")

    print(f"真实值: 4")



    print()



    # 求和查询

    def age_above_40(i):

        return data['age'][i] > 40



    sum_sal, noise = db.sum_query('salary', age_above_40)

    print(f"40岁以上工资和: {sum_sal:.2f} (噪声: {noise:.2f})")

    print(f"真实值: {80000+90000+100000+110000+120000}")



    print()



    # 范围查询

    range_count, _ = db.range_query('age', 30, 50)

    print(f"30-50岁人数: {range_count}")

    print(f"真实值: 5")



    print()

    database_privacy_applications()



    print()

    print("说明：")

    print("  - 差分隐私保护数据库查询")

    print("  - Laplace机制是基础")

    print("  - 需要合理设置epsilon")

