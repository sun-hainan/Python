# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / query_rewrite_rules



本文件实现 query_rewrite_rules 相关的算法功能。

"""



from typing import List, Dict, Tuple, Optional, Set

from dataclasses import dataclass, field

from enum import Enum, auto





class RewriteRuleType(Enum):

    """重写规则类型"""

    PREDICATE_PUSH_DOWN = "predicate_push_down"  # 谓词下推

    PROJECTION_PUSH_DOWN = "projection_push_down"  # 投影下推

    SUBQUERY_UNNESTING = "subquery_unnesting"  # 子查询解嵌套

    VIEW_MERGING = "view_merging"  # 视图合并

    JOIN_REORDERING = "join_reordering"  # 连接重排

    CONSTANT_FOLDING = "constant_folding"  # 常量折叠

    DISTINCT_REMOVAL = "distinct_removal"  # 去重消除





@dataclass

class RelationalExpression:

    """关系表达式"""

    expr_type: str  # 类型: scan, join, project, filter, union, etc.

    children: List['RelationalExpression'] = field(default_factory=list)

    predicates: List['Predicate'] = field(default_factory=list)  # 谓词条件

    projections: List[str] = field(default_factory=list)  # 投影列

    aliases: Dict[str, str] = field(default_factory=dict)  # 别名映射

    cost: float = 0.0  # 代价估计





@dataclass

class Predicate:

    """谓词"""

    column: str  # 列名

    operator: str  # 操作符: =, <, >, <=, >=, !=, IN, LIKE, BETWEEN

    value: any  # 值

    logical_op: str = None  # 逻辑连接: AND, OR, NOT



    def __str__(self):

        return f"{self.column} {self.operator} {self.value}"





@dataclass

class RewriteResult:

    """重写结果"""

    rule_applied: RewriteRuleType  # 应用的规则

    original_expr: RelationalExpression  # 原始表达式

    rewritten_expr: RelationalExpression  # 重写后表达式

    improvement: float = 0.0  # 改进程度





class QueryRewriter:

    """

    查询重写引擎



    功能:

    1. 应用启发式重写规则

    2. 代价模型评估

    3. 规则执行顺序优化

    """



    def __init__(self):

        self.rules_applied: List[RewriteResult] = []

        self.max_iterations = 10



    def rewrite(self, expr: RelationalExpression,

                rules: List[RewriteRuleType] = None) -> RelationalExpression:

        """

        应用重写规则



        参数:

            expr: 原始查询表达式

            rules: 要应用的规则列表,None表示全部



        返回:

            重写后的表达式

        """

        current_expr = expr



        for iteration in range(self.max_iterations):

            improved = False



            # 1. 谓词下推

            if rules is None or RewriteRuleType.PREDICATE_PUSH_DOWN in rules:

                new_expr = self._predicate_push_down(current_expr)

                if new_expr != current_expr:

                    current_expr = new_expr

                    improved = True



            # 2. 投影下推

            if rules is None or RewriteRuleType.PROJECTION_PUSH_DOWN in rules:

                new_expr = self._projection_push_down(current_expr)

                if new_expr != current_expr:

                    current_expr = new_expr

                    improved = True



            # 3. 子查询解嵌套

            if rules is None or RewriteRuleType.SUBQUERY_UNNESTING in rules:

                new_expr = self._unnest_subqueries(current_expr)

                if new_expr != current_expr:

                    current_expr = new_expr

                    improved = True



            # 4. 常量折叠

            if rules is None or RewriteRuleType.CONSTANT_FOLDING in rules:

                new_expr = self._constant_folding(current_expr)

                if new_expr != current_expr:

                    current_expr = new_expr

                    improved = True



            if not improved:

                break



        return current_expr



    def _predicate_push_down(self, expr: RelationalExpression) -> RelationalExpression:

        """

        谓词下推



        原理: 将过滤条件尽可能下推到数据源端执行,减少中间结果大小



        示例:

        SELECT * FROM (SELECT * FROM R WHERE c>10) WHERE c>20

        =>

        SELECT * FROM (SELECT * FROM R WHERE c>20) WHERE c>10

        (实际上: SELECT * FROM R WHERE c>10 AND c>20)

        """

        if not expr.children:

            return expr



        # 如果是Filter操作,尝试下推到子节点

        if expr.expr_type == "filter":

            filter_predicates = expr.predicates.copy()



            new_children = []

            for child in expr.children:

                # 尝试将谓词下推到子节点

                new_child, pushed_preds = self._push_predicates_to_child(child, filter_predicates)

                new_children.append(new_child)



                # 移除已下推的谓词

                filter_predicates = [p for p in filter_predicates

                                     if not self._can_push_to_child(p, child)]



            # 如果还有未下推的谓词,保留Filter

            if filter_predicates:

                return RelationalExpression(

                    expr_type="filter",

                    children=new_children,

                    predicates=filter_predicates

                )

            else:

                # 所有谓词都已下推

                if len(new_children) == 1:

                    return new_children[0]

                else:

                    return RelationalExpression(

                        expr_type="join" if len(new_children) > 1 else "cross",

                        children=new_children

                    )



        # 递归处理子节点

        new_expr = RelationalExpression(

            expr_type=expr.expr_type,

            children=[self._predicate_push_down(child) for child in expr.children],

            predicates=expr.predicates.copy(),

            projections=expr.projections.copy(),

            aliases=expr.aliases.copy()

        )

        return new_expr



    def _push_predicates_to_child(self, child: RelationalExpression,

                                  predicates: List[Predicate]) -> Tuple[RelationalExpression, List[Predicate]]:

        """尝试将谓词下推到子节点"""

        pushed = []

        remaining = []



        for pred in predicates:

            if self._can_push_to_child(pred, child):

                pushed.append(pred)

            else:

                remaining.append(pred)



        # 构建新的子节点

        if pushed:

            new_child = RelationalExpression(

                expr_type="filter",

                children=[child],

                predicates=pushed,

                projections=child.projections.copy(),

                aliases=child.aliases.copy()

            )

        else:

            new_child = child



        return new_child, remaining



    def _can_push_to_child(self, pred: Predicate, child: RelationalExpression) -> bool:

        """判断谓词是否可以下推到子节点"""

        # 简单实现:假设谓词可以下推

        # 实际需要检查列是否存在于子节点中

        return True



    def _projection_push_down(self, expr: RelationalExpression) -> RelationalExpression:

        """

        投影下推



        原理: 将投影操作尽可能下推,减少数据传输量



        示例:

        SELECT c FROM (SELECT a, b, c FROM R)

        =>

        SELECT c FROM (SELECT c FROM R)

        """

        if not expr.children:

            return expr



        # 如果当前有投影,确定需要保留的列

        needed_columns = set(expr.projections) if expr.projections else None



        new_children = []

        for child in expr.children:

            if needed_columns:

                # 尝试将需要的列下推到子节点

                child.projections = list(set(child.projections) | needed_columns)

            new_children.append(self._projection_push_down(child))



        return RelationalExpression(

            expr_type=expr.expr_type,

            children=new_children,

            predicates=expr.predicates.copy(),

            projections=expr.projections.copy() if needed_columns else [],

            aliases=expr.aliases.copy()

        )



    def _unnest_subqueries(self, expr: RelationalExpression) -> RelationalExpression:

        """

        子查询解嵌套



        将相关子查询转换为连接操作



        示例:

        SELECT * FROM R WHERE EXISTS (SELECT 1 FROM S WHERE S.a = R.a)

        =>

        SELECT DISTINCT R.* FROM R JOIN S ON S.a = R.a

        """

        # 简化实现

        return expr



    def _constant_folding(self, expr: RelationalExpression) -> RelationalExpression:

        """

        常量折叠



        原理: 在编译时计算常量表达式



        示例:

        WHERE age > 10 + 5

        =>

        WHERE age > 15

        """

        new_predicates = []

        for pred in expr.predicates:

            new_pred = self._fold_predicate(pred)

            new_predicates.append(new_pred)



        return RelationalExpression(

            expr_type=expr.expr_type,

            children=[self._constant_folding(child) for child in expr.children],

            predicates=new_predicates,

            projections=expr.projections.copy(),

            aliases=expr.aliases.copy()

        )



    def _fold_predicate(self, pred: Predicate) -> Predicate:

        """折叠谓词中的常量表达式"""

        # 简化:直接返回原谓词

        # 实际需要解析和计算常量表达式

        return pred



    def get_statistics(self) -> Dict:

        """获取重写统计"""

        return {

            "rules_applied": len(self.rules_applied),

            "total_iterations": sum(1 for _ in self.rules_applied)

        }





def print_expression(expr: RelationalExpression, indent: int = 0):

    """打印表达式树"""

    prefix = "  " * indent

    print(f"{prefix}{expr.expr_type}")

    if expr.predicates:

        for pred in expr.predicates:

            print(f"{prefix}  predicate: {pred}")

    if expr.projections:

        print(f"{prefix}  projections: {expr.projections}")

    for child in expr.children:

        print_expression(child, indent + 1)





if __name__ == "__main__":

    rewriter = QueryRewriter()



    # 构建测试查询

    # SELECT c FROM (SELECT a, b, c FROM R WHERE a > 10) WHERE c > 5



    r_scan = RelationalExpression(expr_type="scan", projections=["a", "b", "c"], aliases={"table": "R"})



    inner_filter = RelationalExpression(

        expr_type="filter",

        children=[r_scan],

        predicates=[Predicate(column="a", operator=">", value=10)]

    )



    inner_project = RelationalExpression(

        expr_type="project",

        children=[inner_filter],

        projections=["a", "b", "c"]

    )



    outer_filter = RelationalExpression(

        expr_type="filter",

        children=[inner_project],

        predicates=[Predicate(column="c", operator=">", value=5)]

    )



    outer_project = RelationalExpression(

        expr_type="project",

        children=[outer_filter],

        projections=["c"]

    )



    print("=== 原始查询 ===")

    print_expression(outer_project)



    # 应用重写

    print("\n=== 重写后查询 ===")

    rewritten = rewriter.rewrite(outer_project)

    print_expression(rewritten)



    print(f"\n统计: {rewriter.get_statistics()}")

