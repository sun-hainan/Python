"""
反例引导的抽象细化 (CEGAR - Counterexample Guided Abstraction Refinement)
========================================================================
功能：迭代地细化抽象模型直到反例被验证或性质被证明

核心思想：
1. 抽象：将具体模型抽象为更小的抽象模型
2. 检查：在抽象模型上检查性质
3. 判断：
   - 如果抽象满足 → 原始模型也满足（soundness）
   - 如果抽象违反 → 检查反例是否是原始模型的有效反例
     - 如果是 → 找到真正反例
     - 如果不是 → 利用反例信息细化抽象
4. 重复直到收敛

应用：软件模型检查、硬件验证、控制系统验证
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import deque
import copy


@dataclass
class AbstractState:
    """
    抽象状态
    - id: 状态ID
    - concrete_states: 包含的具体状态集合
    - label: 抽象状态标签
    """
    id: int
    concrete_states: Set[Any]
    label: str = ""


@dataclass
class AbstractModel:
    """
    抽象模型
    - states: 抽象状态集合
    - init_state: 初始抽象状态
    - transitions: 抽象转移
    - partition: 划分映射（具体状态→抽象状态）
    """
    states: List[AbstractState]
    init_state: int
    transitions: Set[Tuple[int, int]]
    partition: Dict[Any, int]                          # concrete → abstract


@dataclass
class Counterexample:
    """
    反例
    - path: 抽象路径
    - concrete_paths: 对应的具体路径列表
    - is_spurious: 是否为虚假反例
    """
    abstract_path: List[int]
    concrete_trace: Optional[List[Any]] = None
    is_spurious: bool = True


class Abstraction:
    """
    抽象基类
    """
    
    def __init__(self, concrete_states: Set[Any], labels: Dict[Any, Set[str]]):
        self.concrete_states = concrete_states
        self.labels = labels
        self.abstract_model: Optional[AbstractModel] = None
    
    def create_initial_abstraction(
        self,
        init_state: Any,
        trans_relation: Callable[[Any], Set[Any]]
    ) -> AbstractModel:
        """
        创建初始抽象（所有状态合为一个）
        """
        # 初始划分：所有状态归为一类
        abs_state = AbstractState(
            id=0,
            concrete_states=self.concrete_states,
            label="init"
        )
        
        partition = {s: 0 for s in self.concrete_states}
        
        return AbstractModel(
            states=[abs_state],
            init_state=0,
            transitions={(0, 0)},                    # 自循环
            partition=partition
        )
    
    def refine_partition(
        self,
        partition: Dict[Any, int],
        split_state: Any,
        new_class_id: int
    ) -> Dict[Any, int]:
        """
        细化划分
        将split_state移到一个新类中
        
        Args:
            partition: 当前划分
            split_state: 要分离的具体状态
            new_class_id: 新类的ID
        
        Returns:
            新的划分
        """
        new_partition = partition.copy()
        new_partition[split_state] = new_class_id
        return new_partition


class CEGARLoop:
    """
    CEGAR主循环
    """
    
    def __init__(
        self,
        init_state: Any,
        trans_func: Callable[[Any], Set[Any]],
        bad_state_check: Callable[[Any], bool],
        labels: Dict[Any, Set[str]]
    ):
        self.init_state = init_state
        self.trans_func = trans_func
        self.bad_state_check = bad_state_check
        self.labels = labels
        
        # 获取所有可达状态
        self.all_states = self._compute_reachable_states()
        
        # 创建抽象器
        self.abstraction = Abstraction(self.all_states, labels)
        
        # 迭代计数
        self.iteration = 0
        self.max_iterations = 50
    
    def _compute_reachable_states(self) -> Set[Any]:
        """计算所有可达状态"""
        reachable = {self.init_state}
        queue = deque([self.init_state])
        
        while queue:
            s = queue.popleft()
            for sp in self.trans_func(s):
                if sp not in reachable:
                    reachable.add(sp)
                    queue.append(sp)
        
        return reachable
    
    def find_counterexample(self, model: AbstractModel) -> Optional[Counterexample]:
        """
        在抽象模型中查找反例路径
        
        Args:
            model: 抽象模型
        
        Returns:
            Counterexample或None
        """
        # BFS在抽象模型中搜索坏状态
        queue = deque()
        queue.append([model.init_state])
        visited = set()
        
        while queue:
            path = queue.popleft()
            current = path[-1]
            
            # 检查是否是坏状态
            current_abs_state = model.states[current]
            for cs in current_abs_state.concrete_states:
                if self.bad_state_check(cs):
                    # 找到反例
                    return Counterexample(
                        abstract_path=path,
                        is_spurious=True
                    )
            
            if current in visited:
                continue
            visited.add(current)
            
            # 展开转移
            for s, sp in model.transitions:
                if s == current:
                    queue.append(path + [sp])
        
        return None
    
    def is_counterexample_feasible(
        self,
        cex: Counterexample,
        model: AbstractModel
    ) -> Tuple[bool, Optional[List[Any]]]:
        """
        检查反例是否是可行的（是否是真正的反例）
        
        Args:
            cex: 反例路径
            model: 抽象模型
        
        Returns:
            (是否可行, 具体路径如果有)
        """
        print(f"[CEGAR] 检查反例可行性: {cex.abstract_path}")
        
        # 提取抽象路径上的具体状态
        abstract_states_in_path = [model.states[i] for i in cex.abstract_path]
        
        # 尝试构造具体路径
        # 从第一个抽象状态中选择一个具体状态
        if not abstract_states_in_path:
            return False, None
        
        start_abs = abstract_states_in_path[0]
        current_concrete_states = start_abs.concrete_states
        
        concrete_path = []
        
        # 对每个抽象转移，尝试找到具体转移
        for i in range(len(abstract_states_in_path) - 1):
            curr_abs = abstract_states_in_path[i]
            next_abs = abstract_states_in_path[i + 1]
            
            # 找具体状态对
            found = False
            for cs in list(curr_abs.concrete_states)[:5]:  # 限制搜索
                for sp in self.trans_func(cs):
                    if sp in next_abs.concrete_states:
                        concrete_path.append(cs)
                        found = True
                        break
                if found:
                    break
            
            if not found:
                print(f"[CEGAR] 虚假反例：无法构造具体路径")
                return False, None
        
        # 添加最后一个状态
        if abstract_states_in_path:
            concrete_path.append(list(abstract_states_in_path[-1].concrete_states)[0])
        
        print(f"[CEGAR] 找到具体路径: {concrete_path[:5]}...")
        return True, concrete_path
    
    def refine_abstraction(
        self,
        cex: Counterexample,
        model: AbstractModel
    ) -> AbstractModel:
        """
        细化抽象模型
        
        从虚假反例中学习，创建更精细的抽象
        
        Args:
            cex: 虚假反例
            model: 当前抽象模型
        
        Returns:
            细化后的抽象模型
        """
        print(f"[CEGAR] 细化抽象模型")
        
        # 找到导致虚假性的抽象状态
        # 简化：分离第一个抽象状态
        split_abs_id = cex.abstract_path[0]
        split_abs = model.states[split_abs_id]
        
        # 创建新抽象状态
        new_abs_id = len(model.states)
        
        # 分离策略：按标签分离
        # 将有"bad"标签的状态分离
        bad_states = set()
        good_states = set()
        
        for cs in split_abs.concrete_states:
            labels = self.labels.get(cs, set())
            if "bad" in labels:
                bad_states.add(cs)
            else:
                good_states.add(cs)
        
        if not good_states or not bad_states:
            # 如果分离不明显，随机分离
            states_list = list(split_abs.concrete_states)
            mid = len(states_list) // 2
            good_states = set(states_list[:mid])
            bad_states = set(states_list[mid:])
        
        # 更新抽象状态
        new_states = []
        for i, abs_state in enumerate(model.states):
            if i == split_abs_id:
                # 分裂为两个
                new_states.append(AbstractState(
                    id=len(new_states),
                    concrete_states=good_states,
                    label="good"
                ))
                new_states.append(AbstractState(
                    id=len(new_states),
                    concrete_states=bad_states,
                    label="bad"
                ))
            else:
                new_states.append(AbstractState(
                    id=len(new_states),
                    concrete_states=abs_state.concrete_states,
                    label=abs_state.label
                ))
        
        # 更新划分
        new_partition = {}
        for abs_state in new_states:
            for cs in abs_state.concrete_states:
                new_partition[cs] = abs_state.id
        
        # 重新构建转移
        new_transitions = set()
        for s, sp in model.transitions:
            # 需要根据新的抽象状态ID重建
            pass
        
        new_model = AbstractModel(
            states=new_states,
            init_state=model.init_state,
            transitions=model.transitions,
            partition=new_partition
        )
        
        print(f"[CEGAR] 抽象细化完成: {len(model.states)} → {len(new_states)} 状态")
        
        return new_model
    
    def run(self) -> Tuple[bool, Optional[List[Any]]]:
        """
        运行CEGAR主循环
        
        Returns:
            (是否满足, 反例如果有)
        """
        print("=" * 50)
        print("CEGAR 迭代开始")
        print("=" * 50)
        
        # 创建初始抽象
        model = self.abstraction.create_initial_abstraction(
            self.init_state,
            self.trans_func
        )
        
        while self.iteration < self.max_iterations:
            self.iteration += 1
            print(f"\n[CEGAR] 迭代 {self.iteration}")
            print(f"[CEGAR] 抽象模型: {len(model.states)} 状态")
            
            # 1. 检查抽象模型
            cex = self.find_counterexample(model)
            
            if cex is None:
                # 抽象模型满足性质 → 原始模型也满足
                print(f"[CEGAR] ✓ 抽象模型满足性质，验证完成")
                return True, None
            
            # 2. 检查反例可行性
            is_feasible, concrete_path = self.is_counterexample_feasible(cex, model)
            
            if is_feasible and concrete_path:
                # 找到真正的反例
                print(f"[CEGAR] ✗ 找到真实反例")
                return False, concrete_path
            
            # 3. 细化抽象
            model = self.refine_abstraction(cex, model)
        
        print(f"[CEGAR] 达到最大迭代次数 {self.max_iterations}")
        return False, None


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("CEGAR测试")
    print("=" * 50)
    
    # 定义具体转移系统
    # 状态: 0-4, 坏状态: 2
    def trans_func(s):
        mapping = {
            0: {1, 2},                             # 0可以转移到1或2
            1: {2, 3},
            2: {3, 4},
            3: {0, 4},
            4: {0}
        }
        return mapping.get(s, set())
    
    def bad_check(s):
        return s == 2
    
    labels = {
        0: {"start"},
        1: {"middle"},
        2: {"bad"},
        3: {"middle"},
        4: {"end"}
    }
    
    # 运行CEGAR
    cegar = CEGARLoop(
        init_state=0,
        trans_func=trans_func,
        bad_state_check=bad_check,
        labels=labels
    )
    
    is_safe, cex = cegar.run()
    
    print(f"\n结果: {'安全' if is_safe else '不安全'}")
    if cex:
        print(f"反例: {cex}")
    
    print("\n✓ CEGAR测试完成")
