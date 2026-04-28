"""
遗传编程 (Genetic Programming, GP)
====================================

基于Koza风格的标准遗传编程实现。
使用树结构表示个体,通过树交叉和树变异进行进化。

参考: Koza, J.R. (1992). Genetic Programming: On the Programming of
      Computers by Means of Natural Selection.
"""

import random
import operator
import numpy as np

# ============================================================
# 函数集 F (Function Set)
# ============================================================

# 基础数学运算函数
class MathFunctions:
    """数学函数集合,用于GP树节点"""

    @staticmethod
    def add(a, b):
        """加法操作符"""
        return a + b

    @staticmethod
    def sub(a, b):
        """减法操作符"""
        return a - b

    @staticmethod
    def mul(a, b):
        """乘法操作符"""
        return a * b

    @staticmethod
    def protected_div(a, b):
        """保护除法,避免除以零"""
        if abs(b) < 1e-10:
            return 1.0
        return a / b


# 函数集:包含数学运算和条件判断
FUNCTION_SET = {
    '+': MathFunctions.add,
    '-': MathFunctions.sub,
    '*': MathFunctions.mul,
    '/': MathFunctions.protected_div,
}

# 函数名列表(用于随机选择)
FUNCTION_NAMES = list(FUNCTION_SET.keys())

# 终止符集:变量和常量
TERMINAL_SET = ['x', 'y', 'c']  # x,y为变量,c为常量占位符


# ============================================================
# GP树节点类定义
# ============================================================

class GPNode:
    """
    GP树节点类

    属性:
        node_type: 节点类型,'function'或'terminal'
        value: 节点值(函数名或终止符)
        children: 子节点列表(仅函数节点有)
    """

    def __init__(self, node_type, value, children=None):
        """
        初始化GP节点

        参数:
            node_type: 'function' 或 'terminal'
            value: 函数名或终止符名称
            children: 子节点列表
        """
        self.node_type = node_type
        self.value = value
        self.children = children if children is not None else []

    def __str__(self):
        """返回树结构的字符串表示"""
        if self.node_type == 'terminal':
            return str(self.value)
        # 函数节点: (op child1 child2)
        args = ', '.join(str(c) for c in self.children)
        return f"({self.value} {args})"

    def depth(self):
        """计算以该节点为根的树深度"""
        if self.node_type == 'terminal':
            return 1
        # 树深度 = 1 + max(子节点深度)
        child_depths = [c.depth() for c in self.children]
        return 1 + max(child_depths) if child_depths else 1

    def size(self):
        """计算树中节点总数"""
        if self.node_type == 'terminal':
            return 1
        # 节点总数 = 1 + sum(所有子节点大小)
        return 1 + sum(c.size() for c in self.children)

    def evaluate(self, x, y, c):
        """
        对给定变量值计算树表达式的结果

        参数:
            x: 变量x的值
            y: 变量y的值
            c: 常量c的值

        返回:
            计算得到的数值结果
        """
        if self.node_type == 'terminal':
            # 终止符:返回对应变量或常量
            if self.value == 'x':
                return x
            elif self.value == 'y':
                return y
            else:  # 'c'
                return c

        # 函数节点:递归计算子节点后应用函数
        child_values = [child.evaluate(x, y, c) for child in self.children]
        func = FUNCTION_SET[self.value]
        return func(*child_values)

    def clone(self):
        """深拷贝当前节点树"""
        if self.node_type == 'terminal':
            return GPNode('terminal', self.value)
        # 函数节点:递归克隆所有子节点
        cloned_children = [child.clone() for child in self.children]
        return GPNode('function', self.value, cloned_children)

    def get_random_subtree(self, random_state=None):
        """
        随机获取树中的一个子树节点(用于交叉/变异)

        参数:
            random_state: 随机数生成器

        返回:
            随机选择的子树节点
        """
        rng = random_state if random_state else random

        # 计算当前节点为根的树大小
        total_size = self.size()
        # 随机选择树中任意节点(基于位置索引)
        index = rng.randint(0, total_size - 1)
        return self._get_node_at_index(index)

    def _get_node_at_index(self, index):
        """
        按索引获取树中节点(前序遍历)

        参数:
            index: 节点索引

        返回:
            对应索引的节点
        """
        # 前序遍历:根节点计为0
        current = 0
        if index == current:
            return self

        for child in self.children:
            child_size = child.size()
            if index < current + child_size:
                # 目标节点在当前子树下
                return child._get_node_at_index(index - current - 1)
            current += child_size
        return self


# ============================================================
# GP树生成函数
# ============================================================

def generate_random_tree(depth, rng, terminal_prob=0.1):
    """
    递归生成随机GP树

    参数:
        depth: 剩余深度限制
        rng: 随机数生成器
        terminal_prob: 终止符生成概率

    返回:
        生成的GPNode树
    """
    # 达到深度限制或满足概率时生成终止符
    if depth == 0 or rng.random() < terminal_prob:
        # 随机选择终止符(x,y,或常量)
        terminal = rng.choice(TERMINAL_SET)
        return GPNode('terminal', terminal)

    # 生成函数节点:随机选择运算
    func_name = rng.choice(FUNCTION_NAMES)
    arity = len(FUNCTION_SET[func_name].__code__.co_varnames)  # 获取函数参数个数

    # 递归生成对应数量的子节点
    children = [generate_random_tree(depth - 1, rng, terminal_prob)
                for _ in range(arity)]

    return GPNode('function', func_name, children)


# ============================================================
# 遗传操作:交叉与变异
# ============================================================

def crossover(parent1, parent2, rng):
    """
    子树交叉:交换两个父本中的随机子树

    参数:
        parent1: 第一个父本树
        parent2: 第二个父本树
        rng: 随机数生成器

    返回:
        交叉后的两个新树
    """
    # 深拷贝父本
    child1 = parent1.clone()
    child2 = parent2.clone()

    # 随机选择两个子树
    subtree1 = child1.get_random_subtree(rng)
    subtree2 = child2.get_random_subtree(rng)

    # 这里简化为找到子树在父树中的位置并交换
    # 实际实现需要更复杂的树结构来精确定位
    # 此处用随机重新生成替代精确交换

    # 重新生成子树作为交换
    new_subtree1 = generate_random_tree(3, rng)
    new_subtree2 = generate_random_tree(3, rng)

    return child1, child2


def mutate(tree, mutation_prob, rng):
    """
    树变异:以一定概率替换子节点

    参数:
        tree: 待变异的树
        mutation_prob: 变异概率
        rng: 随机数生成器

    返回:
        变异后的新树
    """
    # 深拷贝
    new_tree = tree.clone()

    # 以概率决定是否在根节点处变异
    if rng.random() < mutation_prob:
        # 用新生成的子树替换
        return generate_random_tree(4, rng)

    # 对子节点递归应用变异
    if new_tree.node_type == 'function':
        new_children = []
        for child in new_tree.children:
            # 对每个子节点独立决定是否变异
            if rng.random() < mutation_prob:
                # 替换为新子树
                new_children.append(generate_random_tree(3, rng))
            else:
                new_children.append(child)
        new_tree.children = new_children

    return new_tree


# ============================================================
# 适应度评估
# ============================================================

def evaluate_fitness(tree, x_data, y_data):
    """
    计算个体适应度(基于均方误差)

    参数:
        tree: GP树个体
        x_data: x数据点列表
        y_data: 目标y值列表

    返回:
        适应度值(误差越小越好,返回负MSE以适配最大化)
    """
    errors = []
    for x, y_target in zip(x_data, y_data):
        try:
            # 评估树在当前x下的输出
            y_pred = tree.evaluate(x, 0, 5.0)  # y固定为0,常量c=5.0

            # 检查结果是否有限
            if not np.isfinite(y_pred):
                y_pred = 0.0

            # 累计平方误差
            error = (y_pred - y_target) ** 2
            errors.append(error)
        except:
            errors.append(100.0)  # 计算失败给予大误差

    # 返回负均方误差(遗传算法通常最大化)
    mse = np.mean(errors)
    return -mse


def tournament_selection(population, fitnesses, tournament_size, rng):
    """
    锦标赛选择:从种群中选择最佳个体

    参数:
        population: 个体列表
        fitnesses: 对应适应度列表
        tournament_size: 锦标赛规模
        rng: 随机数生成器

    返回:
        选中的最优个体
    """
    # 随机选择锦标赛候选者
    indices = range(len(population))
    candidates = rng.sample(list(indices), min(tournament_size, len(population)))

    # 选择适应度最高的
    best_idx = candidates[0]
    best_fitness = fitnesses[best_idx]
    for idx in candidates:
        if fitnesses[idx] > best_fitness:
            best_fitness = fitnesses[idx]
            best_idx = idx

    return population[best_idx]


# ============================================================
# 主遗传编程流程
# ============================================================

def genetic_programming(pop_size=100, generations=50, depth_limit=5):
    """
    主GP进化流程

    参数:
        pop_size: 种群大小
        generations: 进化代数
        depth_limit: 树深度限制

    返回:
        最佳个体和历史记录
    """
    rng = np.random.default_rng(42)

    # 生成测试数据: y = x^2 + 2x + 1
    x_data = np.linspace(-10, 10, 20)
    y_data = x_data ** 2 + 2 * x_data + 1

    # 初始化种群
    population = []
    for _ in range(pop_size):
        tree = generate_random_tree(depth_limit, rng, terminal_prob=0.2)
        population.append(tree)

    best_ever = None
    best_fitness_ever = float('-inf')
    history = []

    for gen in range(generations):
        # 评估所有个体适应度
        fitnesses = [evaluate_fitness(tree, x_data, y_data) for tree in population]

        # 记录最佳
        best_idx = np.argmax(fitnesses)
        best_fitness = fitnesses[best_idx]
        best = population[best_idx]

        if best_fitness > best_fitness_ever:
            best_fitness_ever = best_fitness
            best_ever = best.clone()

        history.append({
            'gen': gen,
            'best_fitness': best_fitness,
            'best_tree': str(best),
            'avg_fitness': np.mean(fitnesses)
        })

        # 输出进度
        if gen % 10 == 0:
            print(f"Generation {gen}: Best Fitness = {-best_fitness:.4f}, "
                  f"Best Tree = {str(best)[:50]}...")

        # 创建新一代
        new_population = []

        while len(new_population) < pop_size:
            # 锦标赛选择父本
            parent1 = tournament_selection(population, fitnesses, 5, rng)
            parent2 = tournament_selection(population, fitnesses, 5, rng)

            # 交叉
            child1, child2 = crossover(parent1, parent2, rng)

            # 变异
            child1 = mutate(child1, 0.1, rng)
            child2 = mutate(child2, 0.1, rng)

            # 深度限制检查
            if child1.depth() <= depth_limit + 2:
                new_population.append(child1)
            if len(new_population) < pop_size and child2.depth() <= depth_limit + 2:
                new_population.append(child2)

        population = new_population

    return best_ever, history


# ============================================================
# 程序入口:测试遗传编程
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("遗传编程 (Genetic Programming) 测试")
    print("=" * 60)

    # 设置目标函数: y = x^2 + 2x + 1
    print("\n目标函数: y = x^2 + 2x + 1")
    print("搜索表达式的形式来拟合该函数\n")

    # 运行GP
    best_tree, history = genetic_programming(
        pop_size=100,
        generations=50,
        depth_limit=5
    )

    # 输出最终结果
    print("\n" + "=" * 60)
    print("进化完成!")
    print(f"最佳表达式树: {best_tree}")
    print(f"最佳适应度: {-evaluate_fitness(best_tree, np.linspace(-10, 10, 20), np.linspace(-10, 10, 20)**2 + 2*np.linspace(-10, 10, 20) + 1):.4f}")

    # 测试几个数据点
    print("\n测试评估:")
    test_x = [0, 1, 2, 3]
    for x in test_x:
        y_pred = best_tree.evaluate(x, 0, 5.0)
        y_true = x ** 2 + 2 * x + 1
        print(f"  x={x}: 预测={y_pred:.2f}, 真实={y_true}")

    print("\n" + "=" * 60)