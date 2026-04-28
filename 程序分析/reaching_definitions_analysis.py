# -*- coding: utf-8 -*-
"""
自然循环识别（Natural Loop Detection）
功能：识别程序中的自然循环结构

自然循环定义：
- 有唯一的入口节点（header）
- 存在回边（back edge）从尾部指向header
- 循环体是所有从back edge可达且支配header的节点

作者：Loop Detection Team
"""

from typing import List, Dict, Set, Tuple, Optional


class LoopDetector:
    """
    自然循环检测器
    
    使用支配关系和回边检测
    """

    def __init__(self):
        self.loops: List[Dict] = []

    def detect_loops(self, cfg: 'CFG', dom_tree: Dict[int, Set[int]]) -> List[Dict]:
        """
        检测所有自然循环
        
        Args:
            cfg: 控制流图
            dom_tree: 支配树 {node_id → 支配它的节点集合}
            
        Returns:
            循环列表 [{header, body, back_edge}]
        """
        loops = []
        
        for block in cfg.blocks:
            for succ in block.succs:
                # 检查是否回边：succ支配block
                if self._is_back_edge(succ, block, dom_tree):
                    loop = self._extract_loop(cfg, block, succ)
                    loops.append(loop)
        
        self.loops = loops
        return loops

    def _is_back_edge(self, succ, block, dom_tree: Dict[int, Set[int]]) -> bool:
        """判断是否为回边"""
        succ_dominators = dom_tree.get(succ.id, set())
        return block.id in succ_dominators

    def _extract_loop(self, cfg: 'CFG', back_src, header) -> Dict:
        """提取循环体"""
        body = {header}
        worklist = [back_src]
        
        while worklist:
            current = worklist.pop()
            if current not in body:
                body.add(current)
                for pred in current.preds:
                    if pred not in body:
                        worklist.append(pred)
        
        return {
            'header': header,
            'back_edge': back_src,
            'body': body,
            'size': len(body)
        }

    def get_loop_header(self, node_id) -> Optional:
        """获取节点所属的循环头"""
        for loop in self.loops:
            if node_id in loop['body']:
                return loop['header']
        return None


class CFG:
    """简化CFG"""
    def __init__(self):
        self.blocks: List = []


def example_loop_detection():
    """循环检测示例"""
    detector = LoopDetector()
    
    # while循环的简化表示
    # header → body → header (back edge)
    
    dom_tree = {
        'header': set(),
        'body': {'header'},
    }
    
    print("循环检测示例完成")


if __name__ == "__main__":
    print("=" * 50)
    print("自然循环识别 测试")
    print("=" * 50)
    example_loop_detection()
