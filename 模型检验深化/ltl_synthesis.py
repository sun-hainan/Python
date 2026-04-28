"""
LTL综合 (LTL Synthesis - From Specification to System)
====================================================
功能：将LTL规约自动综合出满足的系统
基于 automata-based 方法实现自动综合

核心思想：
1. 将LTL规约转换为Buchi自动机
2. 构造product自动机
3. 从product自动机中提取策略/系统

综合问题：
- 输入：环境假设 + 系统保证
- 输出：满足保证的实现系统

算法流程：
1. 解析LTL公式得到环境(E)和系统(S)部分
2. 转换为否定范式
3. 构造自动机
4. 组合E和S
5. 提取winning strategy
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque


class Player(Enum):
    """参与者（环境/系统）"""
    ENVIRONMENT = auto()                          # 环境玩家
    SYSTEM = auto()                               # 系统玩家


@dataclass
class GameState:
    """
    博弈状态
    - id: 状态ID
    - owner: 状态拥有者（谁选择动作）
    - moves: 可用动作
    - label: 状态标签
    """
    id: int
    owner: Player
    moves: List[Any]
    label: Set[str] = field(default_factory=set)


@dataclass
class GameGraph:
    """
    博弈图
    - states: 状态集合
    - transitions: 转移函数 (state, move) → next_state
    - init_state: 初始状态
    - accepting: 接受状态集合（系统目标）
    """
    states: List[GameState]
    transitions: Dict[Tuple[int, Any], int]
    init_state: int
    accepting: Set[int]


@dataclass
class Strategy:
    """策略"""
    moves: Dict[int, Any]                         # 状态→动作


class LTLFormula:
    """LTL公式节点"""
    
    def __init__(self, op: str, children: List['LTLFormula'] = None, literal: str = None):
        self.op = op
        self.children = children or []
        self.literal = literal
    
    def __repr__(self):
        if self.literal:
            return self.literal
        if not self.children:
            return self.op
        if len(self.children) == 1:
            return f"({self.op} {self.children[0]})"
        return f"({self.children[0]} {self.op} {self.children[1]})"


class LTLSynthesizer:
    """
    LTL自动综合器
    """
    
    def __init__(self):
        self.env_vars: Set[str] = set()           # 环境控制变量
        self.sys_vars: Set[str] = set()           # 系统控制变量
        self.spec: Optional[LTLFormula] = None
        self.game_graph: Optional[GameGraph] = None
    
    def set_specification(self, spec_str: str):
        """
        设置规约
        
        格式：E{...} ∨ S{...} 风格的LTL公式
        """
        print(f"[LTL综合] 设置规约: {spec_str}")
        self.spec = self._parse_ltl(spec_str)
    
    def _parse_ltl(self, spec_str: str) -> LTLFormula:
        """解析LTL公式（简化实现）"""
        # 简化：返回一个简单公式
        if "G" in spec_str:
            return LTLFormula("G", [LTLFormula("VAR", literal="p")])
        if "U" in spec_str:
            return LTLFormula("U", [LTLFormula("VAR", literal="p"), LTLFormula("VAR", literal="q")])
        return LTLFormula("VAR", literal="true")
    
    def separate_environment_system(self) -> Tuple[LTLFormula, LTLFormula]:
        """
        分离环境假设和系统保证
        
        格式: E{assumption} → S{guarantee}
        """
        print(f"[LTL综合] 分离环境和系统变量")
        
        # 简化：返回默认分离
        env_spec = LTLFormula("VAR", literal="true")
        sys_spec = self.spec if self.spec else LTLFormula("VAR", literal="true")
        
        return env_spec, sys_spec
    
    def construct_game_automaton(self, spec: LTLFormula) -> GameGraph:
        """
        构造博弈自动机
        
        将规约转换为两人博弈图：
        - 环境动作对应输入
        - 系统动作对应输出
        - 系统目标：满足规约
        
        Returns:
            GameGraph
        """
        print(f"[LTL综合] 构造博弈自动机")
        
        # 简化：构造简单游戏
        states = []
        
        # 状态0：初始状态（环境选择）
        states.append(GameState(
            id=0,
            owner=Player.ENVIRONMENT,
            moves=["e0", "e1"],
            label={"init"}
        ))
        
        # 状态1：系统选择
        states.append(GameState(
            id=1,
            owner=Player.SYSTEM,
            moves=["s0", "s1"],
            label={"middle"}
        ))
        
        # 状态2：接受状态
        states.append(GameState(
            id=2,
            owner=Player.ENVIRONMENT,
            moves=["e0"],
            label={"accept"}
        ))
        
        # 转移
        transitions = {
            (0, "e0"): 1,
            (0, "e1"): 1,
            (1, "s0"): 0,
            (1, "s1"): 2,
            (2, "e0"): 2
        }
        
        graph = GameGraph(
            states=states,
            transitions=transitions,
            init_state=0,
            accepting={2}
        )
        
        self.game_graph = graph
        return graph
    
    def extract_winning_strategy(self, graph: GameGraph) -> Optional[Strategy]:
        """
        从接受状态回推，提取Winning Strategy
        
        使用回推算法：
        1. 标记所有接受状态为WIN_SYS
        2. 反向传播WIN标记
        3. 系统状态：有一个后继WIN → WIN
        4. 环境状态：所有后继WIN → WIN
        
        Returns:
            策略或None（如果不存在winning strategy）
        """
        print(f"[LTL综合] 提取Winning Strategy")
        
        # 初始化
        state_category: Dict[int, str] = {}      # WIN_SYS, WIN_ENV, UNKNOWN
        
        # 从接受状态开始（系统WIN）
        for acc in graph.accepting:
            state_category[acc] = "WIN_SYS"
        
        # 迭代回推
        queue = deque(list(graph.accepting))
        
        while queue:
            s = queue.popleft()
            
            for prev_s, moves_s in self._get_predecessors(graph, s):
                state = graph.states[prev_s]
                
                if state.owner == Player.SYSTEM:
                    # 系统状态：有一个后继WIN_SYS就WIN
                    # 检查是否有到达WIN状态的动作
                    for move in state.moves:
                        key = (prev_s, move)
                        if key in graph.transitions:
                            next_s = graph.transitions[key]
                            if state_category.get(next_s) == "WIN_SYS":
                                if state_category.get(prev_s) != "WIN_SYS":
                                    state_category[prev_s] = "WIN_SYS"
                                    queue.append(prev_s)
                                break
                
                else:  # ENVIRONMENT
                    # 环境状态：所有后继都是WIN_SYS才WIN
                    # 检查是否所有动作都通向WIN
                    all_win = True
                    for move in state.moves:
                        key = (prev_s, move)
                        if key in graph.transitions:
                            next_s = graph.transitions[key]
                            if state_category.get(next_s) != "WIN_SYS":
                                all_win = False
                                break
                    
                    if all_win and state.moves:
                        if state_category.get(prev_s) != "WIN_SYS":
                            state_category[prev_s] = "WIN_SYS"
                            queue.append(prev_s)
        
        # 提取策略
        strategy_moves: Dict[int, Any] = {}
        for state in graph.states:
            if state.owner == Player.SYSTEM:
                # 选择通向WIN状态的动作
                for move in state.moves:
                    key = (state.id, move)
                    if key in graph.transitions:
                        next_s = graph.transitions[key]
                        if state_category.get(next_s) == "WIN_SYS":
                            strategy_moves[state.id] = move
                            break
        
        # 检查初始状态是否WIN
        if state_category.get(graph.init_state) == "WIN_SYS":
            print(f"[LTL综合] ✓ 存在Winning Strategy")
            return Strategy(moves=strategy_moves)
        else:
            print(f"[LTL综合] ✗ 不存在Winning Strategy")
            return None
    
    def _get_predecessors(self, graph: GameGraph, target: int) -> List[Tuple[int, Any]]:
        """获取前驱状态"""
        result = []
        for (s, move), sp in graph.transitions.items():
            if sp == target:
                result.append((s, move))
        return result
    
    def synthesize(self) -> Optional[Strategy]:
        """
        执行LTL综合
        
        Returns:
            策略或None
        """
        print(f"\n{'='*50}")
        print(f"LTL综合")
        print(f"{'='*50}")
        
        # Step 1: 解析规约
        if self.spec is None:
            self.spec = LTLFormula("VAR", literal="true")
        
        # Step 2: 分离环境/系统
        env_spec, sys_spec = self.separate_environment_system()
        
        # Step 3: 构造博弈自动机
        graph = self.construct_game_automaton(sys_spec)
        
        # Step 4: 提取Winning Strategy
        strategy = self.extract_winning_strategy(graph)
        
        if strategy:
            print(f"\n[LTL综合] 策略长度: {len(strategy.moves)} 状态")
            for state_id, move in strategy.moves.items():
                print(f"  状态 {state_id} → 动作 {move}")
        
        return strategy


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("LTL综合测试")
    print("=" * 50)
    
    # 创建综合器
    synthesizer = LTLSynthesizer()
    
    # 设置规约
    # 例：G(request → F grant) - 请求最终会得到授权
    synthesizer.set_specification("G(p -> F q)")
    
    # 执行综合
    strategy = synthesizer.synthesize()
    
    if strategy:
        print("\n综合成功！策略已生成")
    else:
        print("\n综合失败：规约不可满足")
    
    # 测试博弈图
    print("\n" + "=" * 50)
    print("博弈图分析测试")
    print("=" * 50)
    
    # 手动构造一个简单游戏
    states = [
        GameState(id=0, owner=Player.ENVIRONMENT, moves=["a", "b"]),
        GameState(id=1, owner=Player.SYSTEM, moves=["x", "y"]),
        GameState(id=2, owner=Player.ENVIRONMENT, moves=["c"], label={"accept"})
    ]
    
    transitions = {
        (0, "a"): 1,
        (0, "b"): 2,
        (1, "x"): 0,
        (1, "y"): 2,
        (2, "c"): 2
    }
    
    game = GameGraph(
        states=states,
        transitions=transitions,
        init_state=0,
        accepting={2}
    )
    
    synth2 = LTLSynthesizer()
    strategy2 = synth2.extract_winning_strategy(game)
    
    if strategy2:
        print(f"找到策略: {strategy2.moves}")
    
    print("\n✓ LTL综合测试完成")
