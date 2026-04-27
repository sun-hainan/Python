# -*- coding: utf-8 -*-

"""

算法实现：图神经网络 / graph_query_language



本文件实现 graph_query_language 相关的算法功能。

"""



import numpy as np

import re





# ============================

# 图数据结构

# ============================



class Graph:

    """

    图数据结构

    

    支持：

    - 节点属性（字典）

    - 边属性（字典）

    - 有向/无向边

    """

    

    def __init__(self, directed=False):

        self.directed = directed

        self.nodes = {}  # node_id -> {properties}

        self.edges = {}  # (src, dst) -> {properties}

        self.adjacency = {}  # node_id -> {neighbors}

    

    def add_node(self, node_id, **properties):

        """添加节点"""

        self.nodes[node_id] = properties

        if node_id not in self.adjacency:

            self.adjacency[node_id] = set()

    

    def add_edge(self, src, dst, **properties):

        """添加边"""

        self.edges[(src, dst)] = properties

        self.adjacency.setdefault(src, set()).add(dst)

        

        if not self.directed:

            self.adjacency.setdefault(dst, set()).add(src)

            self.edges[(dst, src)] = properties

    

    def get_neighbors(self, node_id):

        """获取邻居节点"""

        return list(self.adjacency.get(node_id, set()))

    

    def get_edge(self, src, dst):

        """获取边属性"""

        return self.edges.get((src, dst), {})

    

    def node_count(self):

        return len(self.nodes)

    

    def edge_count(self):

        return len(self.edges) // (2 if not self.directed else 1)





# ============================

# 解析器

# ============================



class CypherParser:

    """

    简化Cypher查询解析器

    

    支持的语法：

    - MATCH (n) - 返回所有节点

    - MATCH (n) WHERE n.property = 'value' - 带条件

    - MATCH (a)-[r]->(b) - 关系查询

    - MATCH (a)-[*1..3]->(b) - 路径查询

    """

    

    def __init__(self, graph):

        self.graph = graph

    

    def parse(self, query):

        """

        解析并执行Cypher查询

        

        参数:

            query: Cypher查询字符串

        返回:

            results: 查询结果列表

        """

        query = query.strip()

        

        # MATCH语句

        if query.startswith('MATCH'):

            return self._execute_match(query)

        

        # RETURN语句（简化）

        if query.startswith('RETURN'):

            return self._execute_return(query)

        

        raise ValueError(f"Unsupported query: {query}")

    

    def _execute_match(self, query):

        """执行MATCH语句"""

        # 提取MATCH和WHERE部分

        if 'WHERE' in query:

            match_part, where_part = query.split('WHERE', 1)

            where_part = 'WHERE' + where_part.strip()

        else:

            match_part = query

            where_part = None

        

        match_part = match_part.strip()

        

        # 解析MATCH模式

        if '->' in match_part or '<-' in match_part:

            return self._match_path(match_part, where_part)

        else:

            return self._match_nodes(match_part, where_part)

    

    def _match_nodes(self, match_part, where_part):

        """

        匹配节点模式

        

        MATCH (n) -> 返回所有节点

        MATCH (n:Label) -> 返回特定标签的节点

        MATCH (n {property: value}) -> 返回特定属性的节点

        """

        # 提取节点模式

        node_pattern = re.search(r'\(([^)]+)\)', match_part)

        if not node_pattern:

            raise ValueError(f"Invalid node pattern: {match_part}")

        

        node_expr = node_pattern.group(1)

        

        # 解析节点表达式

        node_id = None

        label = None

        properties = {}

        

        # 变量名

        if ':' in node_expr:

            parts = node_expr.split(':')

            node_id = parts[0].strip() if parts[0].strip() else 'n'

            label = parts[1].strip()

        else:

            node_id = node_expr.strip()

        

        # 属性

        prop_match = re.search(r'\{([^}]+)\}', node_expr)

        if prop_match:

            prop_str = prop_match.group(1)

            for prop in prop_str.split(','):

                key, val = prop.split(':')

                properties[key.strip()] = self._parse_value(val.strip())

        

        # 过滤节点

        results = []

        for nid, props in self.graph.nodes.items():

            # 标签过滤（简化：标签存在即匹配）

            if label and label not in props.get('_labels', set()):

                if not any(label in str(v) for v in props.values()):

                    continue

            

            # 属性过滤

            if where_part:

                if not self._check_where(props, where_part):

                    continue

            

            results.append({node_id: {'id': nid, 'properties': props}})

        

        return results

    

    def _match_path(self, match_part, where_part):

        """

        匹配路径模式

        

        MATCH (a)-[r]->(b) - 匹配边

        MATCH (a)-[*1..3]->(b) - 匹配可变长度路径

        """

        # 解析模式

        direction = '->' if '->' in match_part else '<-'

        

        # 提取节点和关系

        pattern = re.search(r'\(([^)]+)\)-\[([^\]]+)\]->\(', match_part)

        if not pattern:

            pattern = re.search(r'\(([^)]+)\)<-\[([^\]]+)\]-', match_part)

            if pattern:

                direction = '<-'

        

        if pattern:

            src_node = pattern.group(1).split(':')[0].strip() or 'a'

            rel_pattern = pattern.group(2)

            rel_var = rel_pattern.split(':')[0].strip() if ':' in rel_pattern else 'r'

            rel_type = None

            if ':' in rel_pattern:

                rel_type = rel_pattern.split(':')[1].strip()

            

            # 简化：查找所有边

            results = []

            for (src, dst), props in self.graph.edges.items():

                if direction == '<-':

                    src, dst = dst, src

                

                # 关系类型过滤

                if rel_type and rel_type != props.get('type'):

                    continue

                

                # WHERE条件

                src_props = self.graph.nodes.get(src, {})

                dst_props = self.graph.nodes.get(dst, {})

                

                if where_part:

                    if not self._check_where({**src_props, **props}, where_part):

                        continue

                

                results.append({

                    src_node: {'id': src, 'properties': src_props},

                    rel_var: {'src': src, 'dst': dst, 'properties': props},

                    'b': {'id': dst, 'properties': dst_props}

                })

            

            return results

        

        # 可变长度路径

        var_path = re.search(r'\(([^)]+)\)-\[([^\]]+)\*(\d+)\.\.(\d+)\]->\(([^)]+)\)', match_part)

        if var_path:

            src_node = var_path.group(1).split(':')[0].strip() or 'a'

            dst_node = var_path.group(5).split(':')[0].strip() or 'b'

            min_hops = int(var_path.group(3))

            max_hops = int(var_path.group(4))

            

            # BFS查找路径

            return self._find_paths(src_node, dst_node, min_hops, max_hops, where_part)

        

        return []

    

    def _find_paths(self, src_var, dst_var, min_hops, max_hops, where_part):

        """查找可变长度路径"""

        results = []

        

        # 对所有源节点尝试

        for src_id in self.graph.nodes.keys():

            paths = self._bfs_paths(src_id, max_hops)

            

            for path in paths:

                if min_hops <= len(path) - 1 <= max_hops:

                    dst_id = path[-1]

                    if where_part:

                        # 收集路径上的属性

                        path_props = {}

                        for i, node_id in enumerate(path):

                            path_props[f'node_{i}'] = self.graph.nodes.get(node_id, {})

                        if not self._check_where(path_props, where_part):

                            continue

                    

                    results.append({

                        src_var: {'id': path[0], 'properties': self.graph.nodes.get(path[0], {})},

                        'path': path,

                        dst_var: {'id': path[-1], 'properties': self.graph.nodes.get(path[-1], {})}

                    })

        

        return results[:100]  # 限制返回数量

    

    def _bfs_paths(self, start, max_hops):

        """BFS查找路径"""

        paths = []

        queue = [(start, [start])]

        

        while queue:

            node, path = queue.pop(0)

            

            if len(path) - 1 >= max_hops:

                continue

            

            for neighbor in self.graph.get_neighbors(node):

                if neighbor not in path:  # 避免环

                    new_path = path + [neighbor]

                    paths.append(new_path)

                    queue.append((neighbor, new_path))

        

        return paths

    

    def _check_where(self, properties, where_part):

        """检查WHERE条件"""

        # 简化实现：支持简单的等值比较

        # WHERE n.property = 'value'

        # WHERE n.property > 10

        

        conditions = where_part.replace('WHERE', '').strip()

        

        # 解析条件

        match = re.match(r'(\w+)\.(\w+)\s*(=|>|<|>=|<=)\s*(.+)', conditions)

        if match:

            var = match.group(1)

            prop = match.group(2)

            op = match.group(3)

            value = self._parse_value(match.group(4))

            

            prop_value = properties.get(prop)

            

            if op == '=':

                return prop_value == value

            elif op == '>':

                return prop_value > value

            elif op == '<':

                return prop_value < value

            elif op == '>=':

                return prop_value >= value

            elif op == '<=':

                return prop_value <= value

        

        return True

    

    def _parse_value(self, value_str):

        """解析值"""

        value_str = value_str.strip()

        

        if value_str.startswith("'"") and value_str.endswith("'"):

            return value_str[1:-1]

        if value_str.startswith("'") and value_str.endswith("'"):

            return value_str[1:-1]

        if value_str.isdigit():

            return int(value_str)

        try:

            return float(value_str)

        except:

            return value_str

    

    def _execute_return(self, query):

        """执行RETURN语句"""

        # 简化实现

        return []





# ============================

# 关系路径查询

# ============================



def find_shortest_path(graph, src, dst):

    """

    查找最短路径

    

    参数:

        graph: Graph对象

        src: 起始节点

        dst: 目标节点

    返回:

        path: 路径节点列表，如果不存在则返回None

    """

    if src == dst:

        return [src]

    

    visited = {src}

    queue = [(src, [src])]

    

    while queue:

        node, path = queue.pop(0)

        

        for neighbor in graph.get_neighbors(node):

            if neighbor == dst:

                return path + [neighbor]

            

            if neighbor not in visited:

                visited.add(neighbor)

                queue.append((neighbor, path + [neighbor]))

    

    return None





def find_all_paths(graph, src, dst, max_length=10):

    """

    查找所有路径

    

    参数:

        graph: Graph对象

        src: 起始节点

        dst: 目标节点

        max_length: 最大路径长度

    返回:

        paths: 所有路径列表

    """

    paths = []

    

    def dfs(node, path):

        if len(path) > max_length:

            return

        if node == dst:

            paths.append(path[:])

            return

        

        for neighbor in graph.get_neighbors(node):

            if neighbor not in path:

                path.append(neighbor)

                dfs(neighbor, path)

                path.pop()

    

    dfs(src, [src])

    return paths





def find_cycles(graph, node, max_length=5):

    """查找经过指定节点的环"""

    cycles = []

    

    def dfs(current, path):

        if len(path) > max_length:

            return

        for neighbor in graph.get_neighbors(current):

            if neighbor == node and len(path) > 2:

                cycles.append(path[:] + [node])

            elif neighbor not in path:

                path.append(neighbor)

                dfs(neighbor, path)

                path.pop()

    

    dfs(node, [node])

    return cycles





# ============================

# 测试代码

# ============================



if __name__ == "__main__":

    np.random.seed(42)

    

    print("=" * 55)

    print("图查询语言（Cypher简化）测试")

    print("=" * 55)

    

    # 创建测试图

    g = Graph(directed=False)

    

    # 添加节点

    g.add_node(1, name='Alice', age=30, _labels={'Person'})

    g.add_node(2, name='Bob', age=25, _labels={'Person'})

    g.add_node(3, name='Charlie', age=35, _labels={'Person'})

    g.add_node(4, name='David', age=28, _labels={'Person'})

    g.add_node(5, name='Eve', age=32, _labels={'Person'})

    g.add_node(10, name='CompanyA', _labels={'Company'})

    

    # 添加边（关系）

    g.add_edge(1, 2, type='KNOWS', since=2020)

    g.add_edge(2, 3, type='KNOWS', since=2019)

    g.add_edge(3, 4, type='KNOWS', since=2021)

    g.add_edge(4, 5, type='KNOWS', since=2018)

    g.add_edge(1, 5, type='KNOWS', since=2022)

    g.add_edge(1, 10, type='WORKS_AT', since=2020)

    g.add_edge(3, 10, type='WORKS_AT', since=2019)

    

    print(f"节点数: {g.node_count()}")

    print(f"边数: {g.edge_count()}")

    

    parser = CypherParser(g)

    

    # 测试1：简单节点查询

    print("\n--- MATCH (n) ---")

    results = parser.parse("MATCH (n)")

    print(f"结果数量: {len(results)}")

    for r in results[:3]:

        print(f"  {r}")

    

    # 测试2：带WHERE的查询

    print("\n--- MATCH (n) WHERE n.age > 30 ---")

    results = parser.parse("MATCH (n) WHERE n.age > 30")

    print(f"结果数量: {len(results)}")

    for r in results:

        node_data = r.get('n', r.get('m', {}))

        print(f"  节点 {node_data['id']}: {node_data['properties']}")

    

    # 测试3：关系查询

    print("\n--- MATCH (a)-[r]->(b) ---")

    results = parser.parse("MATCH (a)-[r]->(b)")

    print(f"结果数量: {len(results)}")

    for r in results[:3]:

        a_data = r.get('a', {})

        b_data = r.get('b', {})

        r_data = r.get('r', {})

        print(f"  {a_data['id']} --[{r_data['properties'].get('type', 'KNOWS')}]--> {b_data['id']}")

    

    # 测试4：特定关系类型查询

    print("\n--- MATCH (a)-[r:KNOWS]->(b) ---")

    results = parser.parse("MATCH (a)-[r:KNOWS]->(b)")

    print(f"结果数量: {len(results)}")

    for r in results:

        a_data = r.get('a', {})

        b_data = r.get('b', {})

        print(f"  {a_data['properties'].get('name')} -> {b_data['properties'].get('name')}")

    

    # 测试5：最短路径

    print("\n--- 最短路径查询 ---")

    path = find_shortest_path(g, 2, 5)

    if path:

        path_names = [g.nodes[n].get('name', n) for n in path]

        print(f"从Bob到Eve的最短路径: {' -> '.join(path_names)}")

        print(f"路径长度: {len(path) - 1} 跳")

    

    # 测试6：所有路径

    print("\n--- 所有路径查询 ---")

    paths = find_all_paths(g, 1, 4, max_length=5)

    print(f"从Alice到David的路径数量: {len(paths)}")

    for p in paths[:5]:

        path_names = [g.nodes[n].get('name', n) for n in p]

        print(f"  {' -> '.join(path_names)}")

    

    # 测试7：查找环

    print("\n--- 环查找 ---")

    cycles = find_cycles(g, 1, max_length=5)

    print(f"经过Alice的环数量: {len(cycles)}")

    for c in cycles[:3]:

        cycle_names = [g.nodes[n].get('name', n) for n in c]

        print(f"  {' -> '.join(cycle_names[:-1])} -> (回到{cycle_names[-1]})")

    

    # 测试8：邻居查询

    print("\n--- 邻居查询 ---")

    alice_id = 1

    neighbors = g.get_neighbors(alice_id)

    neighbor_names = [g.nodes[n].get('name', n) for n in neighbors]

    print(f"Alice的邻居: {neighbor_names}")

    

    # 测试9：度数统计

    print("\n--- 度数统计 ---")

    print(f"{'节点':>6} | {'姓名':>10} | {'度数':>6}")

    print("-" * 28)

    for node_id in g.nodes:

        name = g.nodes[node_id].get('name', node_id)

        degree = len(g.get_neighbors(node_id))

        print(f"{node_id:6d} | {name:>10} | {degree:6d}")

    

    # 测试10：WHERE条件组合

    print("\n--- 复杂WHERE条件 ---")

    results = parser.parse("MATCH (n) WHERE n.age > 25")

    print(f"年龄大于25的节点: {len(results)}个")

    results = parser.parse("MATCH (n) WHERE n.age > 28 AND n.age < 35")

    print(f"年龄在28-35之间的节点: {len(results)}个")

    

    print("\n图查询语言测试完成！")

