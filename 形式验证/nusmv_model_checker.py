# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / nusmv_model_checker

本文件实现 nusmv_model_checker 相关的算法功能。
"""

import numpy as np
from collections import defaultdict, deque


class SMVState:
    """SMV状态"""
    def __init__(self, values=None):
        self.values = values if values else {}
    
    def __hash__(self):
        return hash(tuple(sorted(self.values.items())))
    
    def __eq__(self, other):
        return self.values == other.values
    
    def __repr__(self):
        return f"State({self.values})"
    
    def copy(self):
        return SMVState(self.values.copy())


class SMVModel:
    """
    NuSMV风格模型
    
    包含：
    - 变量声明
    - 初始化条件
    - 转换关系
    - 不变量约束
    """
    
    def __init__(self):
        self.variables = {}      # var_name -> {type, range, init}
        self.transitions = []    # [(from_cond, to_cond), ...]
        self.definitions = {}    # DEFINE: 宏定义
        self.specs = []          # SPEC: 属性规格
    
    def add_variable(self, name, var_type='boolean', init=None, range_vals=None):
        """
        添加变量
        
        参数:
            name: 变量名
            var_type: 类型 (boolean, enum, range)
            init: 初始值
            range_vals: 枚举值或范围
        """
        self.variables[name] = {
            'type': var_type,
            'init': init,
            'range': range_vals
        }
    
    def add_init(self, condition):
        """添加初始化条件"""
        self.transitions.append(('init', condition))
    
    def add_transition(self, from_cond, to_assign):
        """
        添加转换
        
        参数:
            from_cond: 源状态条件
            to_assign: 目标赋值
        """
        self.transitions.append(('next', (from_cond, to_assign)))
    
    def add_define(self, name, expression):
        """添加宏定义"""
        self.definitions[name] = expression
    
    def add_spec(self, spec):
        """添加属性规格"""
        self.specs.append(spec)
    
    def enumerate_states(self, max_states=10000):
        """
        枚举所有可能状态
        
        返回:
            状态列表
        """
        if not self.variables:
            return [SMVState()]
        
        # 简化：假设都是布尔变量
        var_names = list(self.variables.keys())
        n = len(var_names)
        
        states = []
        for i in range(2 ** n):
            values = {}
            for j, var in enumerate(var_names):
                values[var] = bool((i >> j) & 1)
            states.append(SMVState(values))
            
            if len(states) >= max_states:
                break
        
        return states
    
    def get_initial_states(self):
        """获取初始状态集合"""
        init_conds = [t for t in self.transitions if t[0] == 'init']
        
        if not init_conds:
            return self.enumerate_states()
        
        all_states = self.enumerate_states()
        result = []
        
        for state in all_states:
            for _, cond in init_conds:
                if self._check_condition(state, cond):
                    result.append(state)
                    break
        
        return result
    
    def get_successors(self, state):
        """获取后继状态"""
        next_trans = [t for t in self.transitions if t[0] == 'next']
        
        result = []
        
        for _, (from_cond, to_assign) in next_trans:
            if self._check_condition(state, from_cond):
                new_state = state.copy()
                self._apply_assign(new_state, to_assign)
                result.append(new_state)
        
        return result
    
    def _check_condition(self, state, cond):
        """检查条件是否满足"""
        if isinstance(cond, dict):
            for var, val in cond.items():
                if state.values.get(var) != val:
                    return False
            return True
        
        if isinstance(cond, tuple):
            op = cond[0]
            
            if op == 'and':
                return (self._check_condition(state, cond[1]) and
                        self._check_condition(state, cond[2]))
            
            if op == 'or':
                return (self._check_condition(state, cond[1]) or
                        self._check_condition(state, cond[2]))
            
            if op == 'not':
                return not self._check_condition(state, cond[1])
            
            if op == '==':
                left = state.values.get(cond[1], cond[1])
                right = state.values.get(cond[2], cond[2])
                return left == right
            
            if op == '!=':
                return state.values.get(cond[1]) != cond[2]
            
            if op == '<':
                return state.values.get(cond[1], 0) < cond[2]
            
            if op == '>':
                return state.values.get(cond[1], 0) > cond[2]
        
        return True
    
    def _apply_assign(self, state, assign):
        """应用赋值"""
        if isinstance(assign, dict):
            state.values.update(assign)
        elif isinstance(assign, tuple):
            op = assign[0]
            if op == 'case':
                for cond, val in assign[1:]:
                    if self._check_condition(state, cond):
                        state.values[assign[-1]] = val
                        break


class SMVModelChecker:
    """
    NuSMV风格模型检查器
    
    支持:
    - CTL: AG, EG, AF, EF, AX, EX, AU, EU
    - LTL: G, F, X, U, R
    - INVAR: 不变式
    """
    
    def __init__(self, model):
        self.model = model
        self.cache = {}
    
    def check(self, spec):
        """
        检查属性
        
        参数:
            spec: CTL/LTL公式
        
        返回:
            (是否满足, 满足状态集合)
        """
        parsed = self._parse_spec(spec)
        result = self._eval(parsed)
        return result
    
    def _parse_spec(self, spec):
        """解析规格字符串"""
        spec = spec.strip()
        
        if spec.startswith('AG '):
            return ('ag', self._parse_spec(spec[3:]))
        if spec.startswith('EG '):
            return ('eg', self._parse_spec(spec[3:]))
        if spec.startswith('AF '):
            return ('af', self._parse_spec(spec[3:]))
        if spec.startswith('EF '):
            return ('ef', self._parse_spec(spec[3:]))
        if spec.startswith('AX '):
            return ('ax', self._parse_spec(spec[3:]))
        if spec.startswith('EX '):
            return ('ex', self._parse_spec(spec[3:]))
        if spec.startswith('A '):
            # A [ ... U ... ]
            inner = spec[2:].strip()
            if ' U ' in inner:
                parts = inner.split(' U ', 1)
                return ('au', self._parse_spec(parts[0]), self._parse_spec(parts[1]))
        if spec.startswith('E '):
            inner = spec[2:].strip()
            if ' U ' in inner:
                parts = inner.split(' U ', 1)
                return ('eu', self._parse_spec(parts[0]), self._parse_spec(parts[1]))
        
        if spec.startswith('G '):
            return ('g', self._parse_spec(spec[2:]))
        if spec.startswith('F '):
            return ('f', self._parse_spec(spec[2:]))
        if spec.startswith('X '):
            return ('x', self._parse_spec(spec[2:]))
        
        if spec.startswith('(') and spec.endswith(')'):
            return self._parse_spec(spec[1:-1])
        
        if ' & ' in spec:
            parts = spec.split(' & ')
            return ('and', self._parse_spec(parts[0]), self._parse_spec(parts[1]))
        
        if ' | ' in spec:
            parts = spec.split(' | ')
            return ('or', self._parse_spec(parts[0]), self._parse_spec(parts[1]))
        
        if ' ! ' in spec or spec.startswith('!'):
            inner = spec[2:].strip() if ' ! ' in spec else spec[1:]
            return ('not', self._parse_spec(inner))
        
        # 原子命题
        return ('ap', spec.strip())
    
    def _eval(self, parsed):
        """计算满足状态集合"""
        op = parsed[0]
        
        if op == 'ap':
            prop = parsed[1]
            return self._eval_ap(prop)
        
        if op == 'not':
            sub = self._eval(parsed[1])
            return self._eval_not(sub)
        
        if op == 'and':
            left = self._eval(parsed[1])
            right = self._eval(parsed[2])
            return self._eval_and(left, right)
        
        if op == 'or':
            left = self._eval(parsed[1])
            right = self._eval(parsed[2])
            return self._eval_or(left, right)
        
        if op == 'ax':
            sub = self._eval(parsed[1])
            return self._eval_ax(sub)
        
        if op == 'ex':
            sub = self._eval(parsed[1])
            return self._eval_ex(sub)
        
        if op == 'af':
            sub = self._eval(parsed[1])
            return self._eval_af(sub)
        
        if op == 'ef':
            sub = self._eval(parsed[1])
            return self._eval_ef(sub)
        
        if op == 'ag':
            sub = self._eval(parsed[1])
            return self._eval_ag(sub)
        
        if op == 'eg':
            sub = self._eval(parsed[1])
            return self._eval_eg(sub)
        
        if op == 'au':
            p = self._eval(parsed[1])
            q = self._eval(parsed[2])
            return self._eval_au(p, q)
        
        if op == 'eu':
            p = self._eval(parsed[1])
            q = self._eval(parsed[2])
            return self._eval_eu(p, q)
        
        return set()
    
    def _eval_ap(self, prop):
        """原子命题"""
        result = set()
        all_states = self.model.enumerate_states()
        
        for state in all_states:
            if prop in self.model.definitions:
                # 宏定义
                if self.model.definitions[prop](state):
                    result.add(state)
            else:
                # 简单变量检查
                if state.values.get(prop, False):
                    result.add(state)
        
        return result
    
    def _eval_not(self, S):
        """NOT"""
        all_states = set(self.model.enumerate_states())
        return all_states - S
    
    def _eval_and(self, A, B):
        """AND"""
        return A & B
    
    def _eval_or(self, A, B):
        """OR"""
        return A | B
    
    def _eval_ex(self, Q):
        """EX Q: 存在后继满足Q"""
        result = set()
        all_states = self.model.enumerate_states()
        
        for s in all_states:
            for succ in self.model.get_successors(s):
                if succ in Q:
                    result.add(s)
                    break
        
        return result
    
    def _eval_ax(self, Q):
        """AX Q: 所有后继满足Q"""
        result = set()
        all_states = self.model.enumerate_states()
        
        for s in all_states:
            successors = self.model.get_successors(s)
            if successors and all(succ in Q for succ in successors):
                result.add(s)
        
        return result
    
    def _eval_ef(self, Q):
        """EF Q: 存在路径最终到达Q"""
        Y = set(Q)
        W = set(self.model.enumerate_states()) - Y
        
        changed = True
        while changed:
            changed = False
            to_add = set()
            
            for s in W:
                for succ in self.model.get_successors(s):
                    if succ in Y:
                        to_add.add(s)
                        break
            
            if to_add:
                Y.update(to_add)
                W -= to_add
                changed = True
        
        return Y
    
    def _eval_af(self, Q):
        """AF Q: 所有路径最终到达Q"""
        # AF Q = NOT EF NOT Q
        not_Q = self._eval_not(Q)
        ef_not_Q = self._eval_ef(not_Q)
        return self._eval_not(ef_not_Q)
    
    def _eval_eg(self, Q):
        """EG Q: 存在路径上Q始终成立"""
        Y = set(Q)
        
        changed = True
        while changed:
            changed = False
            to_remove = set()
            
            for s in Y:
                successors = self.model.get_successors(s)
                if successors and not any(succ in Y for succ in successors):
                    to_remove.add(s)
            
            if to_remove:
                Y -= to_remove
                changed = True
        
        return Y
    
    def _eval_ag(self, Q):
        """AG Q: 所有路径上Q始终成立"""
        # AG Q = NOT EF NOT Q
        not_Q = self._eval_not(Q)
        ef_not_Q = self._eval_ef(not_Q)
        return self._eval_not(ef_not_Q)
    
    def _eval_eu(self, P, Q):
        """E P U Q: 存在路径P直到Q"""
        Y = set(Q)
        W = set(self.model.enumerate_states()) - Y
        
        while True:
            new_Y = Y.copy()
            for s in W:
                if s not in P:
                    continue
                successors = self.model.get_successors(s)
                if successors and any(succ in new_Y for succ in successors):
                    new_Y.add(s)
            
            if new_Y == Y:
                break
            Y = new_Y
            W -= Y
        
        return Y
    
    def _eval_au(self, P, Q):
        """A P U Q: 所有路径P直到Q"""
        # A U Q P = NOT (E NOT Q U NOT P AND NOT Q)
        not_P = self._eval_not(P)
        not_Q = self._eval_not(Q)
        
        # E NOT Q U NOT P AND NOT Q
        temp = self._eval_eu(not_Q, not_P & not_Q)
        
        return self._eval_not(temp)
    
    def check_all_initial(self, spec):
        """检查所有初始状态是否满足"""
        parsed = self._parse_spec(spec)
        sat_states = self._eval(parsed)
        init_states = set(self.model.get_initial_states())
        return init_states <= sat_states


class SMVParser:
    """简化的SMV文件解析器"""
    
    def __init__(self):
        self.model = None
    
    def parse(self, text):
        """
        解析SMV文本
        
        返回:
            SMVModel
        """
        self.model = SMVModel()
        
        lines = text.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('--'):
                continue
            
            if line.startswith('VAR'):
                current_section = 'VAR'
            elif line.startswith('INIT'):
                current_section = 'INIT'
            elif line.startswith('TRANS'):
                current_section = 'TRANS'
            elif line.startswith('DEFINE'):
                current_section = 'DEFINE'
            elif line.startswith('SPEC'):
                current_section = 'SPEC'
            elif line.startswith('INVAR'):
                current_section = 'INVAR'
            else:
                self._process_line(line, current_section)
        
        return self.model
    
    def _process_line(self, line, section):
        """处理一行"""
        if section == 'VAR':
            self._parse_var(line)
        elif section == 'INIT':
            self._parse_init(line)
        elif section == 'TRANS':
            self._parse_trans(line)
        elif section == 'SPEC':
            self._parse_spec(line)
    
    def _parse_var(self, line):
        """解析变量声明"""
        if ':' in line:
            name, rest = line.split(':', 1)
            name = name.strip()
            rest = rest.rstrip(';').strip()
            
            var_type = 'boolean'
            if 'boolean' in rest:
                var_type = 'boolean'
            elif 'enum' in rest:
                var_type = 'enum'
            
            self.model.add_variable(name, var_type)
    
    def _parse_init(self, line):
        """解析初始条件"""
        line = line.rstrip(';')
        # 简化：假设格式为 x = value
        if '=' in line:
            var, val = line.split('=', 1)
            self.model.add_init({var.strip(): val.strip() == 'TRUE'})
    
    def _parse_trans(self, line):
        """解析转换关系"""
        line = line.rstrip(';')
        # 简化处理
        self.model.add_transition({}, {})
    
    def _parse_spec(self, line):
        """解析属性规格"""
        line = line.rstrip(';')
        # 移除 "SPEC "
        if line.startswith('SPEC'):
            spec = line[4:].strip()
            if spec.startswith('!'):
                spec = '! ' + spec[1:]
            self.model.add_spec(spec)


def smv_example():
    """SMV模型示例"""
    return """
-- 简单的互斥模型
MODULE main
VAR
  x : boolean;
  y : boolean;

INIT
  x = FALSE & y = FALSE

TRANS
  (x = FALSE & y = FALSE) -> (next(x) = TRUE & next(y) = FALSE)
  (x = TRUE & y = FALSE) -> (next(x) = TRUE & next(y) = TRUE)
  (x = TRUE & y = TRUE) -> (next(x) = FALSE & next(y) = FALSE)
  (x = FALSE & y = TRUE) -> (next(x) = FALSE & next(y) = TRUE)

SPEC
  AG (x -> AF y)
"""


def run_demo():
    """运行NuSMV风格模型检查演示"""
    print("=" * 60)
    print("NuSMV风格模型检查框架")
    print("=" * 60)
    
    # 创建简单模型
    model = SMVModel()
    
    # 变量: x, y
    model.add_variable('x', 'boolean', False)
    model.add_variable('y', 'boolean', False)
    
    # 初始化: x=FALSE, y=FALSE
    model.add_init({'x': False, 'y': False})
    
    # 转换: x变True后，y可以变True
    model.add_transition({'x': False, 'y': False}, {'x': True, 'y': False})
    model.add_transition({'x': True, 'y': False}, {'x': True, 'y': True})
    model.add_transition({'x': True, 'y': True}, {'x': False, 'y': False})
    model.add_transition({'x': False, 'y': True}, {'x': False, 'y': True})
    
    print("\n[模型]")
    print("  变量: x, y (布尔)")
    print("  初始状态: x=FALSE, y=FALSE")
    print("  转换: x变True后y可以变True")
    
    # 创建检查器
    checker = SMVModelChecker(model)
    
    # 检查属性
    print("\n[属性检查]")
    
    # EF x
    result = checker.check('EF x')
    print(f"  EF x (最终x为真): {len(result)}个状态满足")
    
    # AG (x -> AF y)
    result = checker.check('AG (x -> AF y)')
    print(f"  AG (x -> AF y): {len(result)}个状态满足")
    
    # EG y
    result = checker.check('EG y')
    print(f"  EG y (存在路径y始终为真): {len(result)}个状态满足")
    
    # 初始状态检查
    print("\n[初始状态检查]")
    all_init_ok = checker.check_all_initial('EF x')
    print(f"  所有初始状态满足 EF x: {all_init_ok}")
    
    # SMV解析演示
    print("\n[SMV解析器]")
    parser = SMVParser()
    smv_text = smv_example()
    parsed_model = parser.parse(smv_text)
    print(f"  解析变量: {list(parsed_model.variables.keys())}")
    print(f"  解析规格: {parsed_model.specs}")
    
    print("\n" + "=" * 60)
    print("NuSMV框架核心概念:")
    print("  1. SMV: 符号模型检查输入语言")
    print("  2. VAR: 变量声明")
    print("  3. INIT: 初始条件")
    print("  4. TRANS: 转换关系")
    print("  5. SPEC: CTL/LTL属性规格")
    print("  6. DEFINE: 宏定义（简化表达式）")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
