# -*- coding: utf-8 -*-

"""

算法实现：自然语言处理 / beam_search



本文件实现 beam_search 相关的算法功能。

"""



import numpy as np





class BeamSearch:

    """Beam Search 解码器"""



    def __init__(self, beam_width=5):

        """

        beam_width: beam 宽度（每步保留的候选数量）

        """

        self.beam_width = beam_width



    def beam_search(self, start_token, is_end_token, get_next_token_probs, max_len=50):

        """Beam Search 主算法

        start_token: 起始 token

        is_end_token: 判断是否为结束 token 的函数

        get_next_token_probs: 给定当前序列，返回下一 token 的概率分布函数

            输入: List[token]，输出: Dict[token] -> float 或 np.ndarray

        max_len: 最大生成长度

        返回: List[best_sequences]（按概率排序）

        """

        # 每个 beam 的结构: (序列: List, 对数概率: float)

        # 初始化：从 start_token 开始

        beams = [([start_token], 0.0)]



        for step in range(max_len):

            all_candidates = []



            for seq, score in beams:

                # 如果已经结束，跳过扩展

                if is_end_token(seq[-1]):

                    all_candidates.append((seq, score))

                    continue



                # 获取下一步的概率分布

                probs = get_next_token_probs(seq)

                # 转为 numpy 便于处理

                if isinstance(probs, dict):

                    tokens = list(probs.keys())

                    log_probs = np.array([probs[t] for t in tokens])

                    # 概率 -> 对数概率

                    log_probs = np.log(log_probs + 1e-10)

                else:

                    log_probs = np.log(probs + 1e-10)

                    tokens = np.arange(len(probs))



                # Top-k 扩展（限制扩展数量避免爆炸）

                top_k = min(self.beam_width * 2, len(tokens))

                top_indices = np.argsort(log_probs)[::-1][:top_k]



                for idx in top_indices:

                    token = tokens[idx]

                    new_seq = seq + [token]

                    new_score = score + log_probs[idx]

                    all_candidates.append((new_seq, new_score))



            # 按对数概率排序，取 top beam_width

            all_candidates.sort(key=lambda x: x[1], reverse=True)

            beams = all_candidates[:self.beam_width]



            # 所有 beam 都已结束

            if all(is_end_token(b[0][-1]) for b in beams):

                break



        # 如果 beam 提前结束，补充 unfinished

        return beams



    def decode(self, start_token, is_end_token, get_next_token_probs, max_len=50):

        """解码接口：返回最佳序列"""

        beams = self.beam_search(start_token, is_end_token, get_next_token_probs, max_len)

        best_seq, best_score = beams[0]

        return best_seq, best_score





def demo():

    """Beam Search 演示：简单序列生成"""



    # 词汇表

    vocab = ["<EOS>", "我", "爱", "你", "她", "机器", "学习", "深度", "是", "好", "玩", "棒"]

    idx_to_word = {i: w for i, w in enumerate(vocab)}

    word_to_idx = {w: i for i, w in enumerate(vocab)}

    vocab_size = len(vocab)



    # 简单的语法约束模拟

    grammar_rules = {

        ("我",): ["爱", "是"],

        ("爱",): ["你", "她"],

        ("你",): ["<EOS>"],

        ("她",): ["<EOS>"],

        ("机器",): ["学习", "是"],

        ("学习",): ["深度", "<EOS>"],

        ("深度",): ["学习"],

        ("是",): ["好", "棒", "<EOS>"],

        ("好",): ["<EOS>"],

        ("棒",): ["<EOS>"],

    }



    # 简单概率分布

    def get_probs(seq):

        last = seq[-1] if seq else "<BOS>"

        if last in grammar_rules:

            candidates = grammar_rules[last]

        else:

            candidates = list(set(word for rule in grammar_rules.values() for word in rule))

        probs = np.zeros(vocab_size)

        for w in candidates:

            idx = word_to_idx.get(w, 0)

            probs[idx] = 1.0 / len(candidates)

        return probs



    def is_end(token):

        return token == "<EOS>"



    # 测试

    print("=== Beam Search 演示 ===")

    for beam_width in [1, 3, 5]:

        searcher = BeamSearch(beam_width=beam_width)

        beams = searcher.beam_search(

            start_token="我",

            is_end_token=is_end,

            get_next_token_probs=get_probs,

            max_len=10

        )

        print(f"\nBeam Width = {beam_width}:")

        for i, (seq, score) in enumerate(beames[:3] if beam_width > 0 else [(beams[0] if beams else None, None)]):

            seq_str = " -> ".join(seq)

            print(f"  [{i}] {seq_str}  (score: {score:.4f})")



    # 带神经网络的模拟演示

    print("\n=== 神经网络模拟 Beam Search ===")



    # 模拟一个简单的语言模型概率

    np.random.seed(42)



    class DummyLM:

        """模拟语言模型"""



        def __init__(self):

            self.vocab = vocab



        def probs(self, seq):

            # 简单转移概率模拟

            transition = {

                "我": {"爱": 0.5, "是": 0.3, "机器": 0.2},

                "爱": {"你": 0.6, "她": 0.4},

                "你": {"<EOS>": 1.0},

                "她": {"<EOS>": 1.0},

                "机器": {"学习": 0.7, "是": 0.3},

                "学习": {"深度": 0.5, "<EOS>": 0.5},

                "深度": {"学习": 0.9, "是": 0.1},

                "是": {"好": 0.5, "棒": 0.5},

                "好": {"<EOS>": 1.0},

                "棒": {"<EOS>": 1.0},

                "<BOS>": {"我": 0.8, "机器": 0.2},

            }

            next_words = transition.get(seq[-1], {})

            probs = np.zeros(len(self.vocab))

            for w, p in next_words.items():

                if w in word_to_idx:

                    probs[word_to_idx[w]] = p

            if probs.sum() == 0:

                probs[0] = 1.0  # 默认 EOS

            return probs



    lm = DummyLM()

    searcher = BeamSearch(beam_width=5)

    beams = searcher.beam_search(

        start_token="我",

        is_end_token=is_end,

        get_next_token_probs=lm.probs,

        max_len=15

    )

    print("Beam Search (beam=5) 候选序列:")

    for i, (seq, score) in enumerate(beams):

        print(f"  [{i}] {' -> '.join(seq)}  (log_prob: {score:.4f})")





if __name__ == "__main__":

    demo()

