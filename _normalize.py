# -*- coding: utf-8 -*-
"""
算法实现：_normalize.py / _normalize

本文件实现 _normalize 相关的算法功能。
"""

import os
import re
import glob

BASE = r"D:\openclaw-home\.openclaw\workspace\计算机算法"
DIRS = ["05_动态规划", "07_贪心与分治", "18_信号与图像", "26_网页与编程", "08_位运算"]

# 分类映射
CAT_MAP = {
    "05_动态规划": "动态规划",
    "07_贪心与分治": "贪心与分治",
    "18_信号与图像": "信号与图像处理",
    "26_网页与编程": "网页与编程",
    "08_位运算": "位运算",
}

# 函数/类 → 中文描述 映射表
COMMENT_MAP = {
    # 动态规划
    "abbr": "单词缩写问题（动态规划）",
    "all_construct": "所有构造方式（DP）",
    "bitmask": "状态压缩动态规划",
    "catalan_numbers": "卡特兰数计算",
    "climbing_stairs": "爬楼梯问题",
    "combination_sum_iv": "组合和 IV",
    "dp_bitmask_optimization": "状态压缩DP优化",
    "dp_segment_optimization": "DP线段树优化",
    "dp_tree_optimization": "树形DP优化",
    "edit_distance": "编辑距离（Levenshtein）",
    "factorial": "阶乘计算",
    "fast_fibonacci": "快速斐波那契（矩阵幂）",
    "fibonacci": "斐波那契数列",
    "fizz_buzz": "FizzBuzz问题",
    "floyd_warshall": "弗洛伊德最短路算法",
    "integer_partition": "整数划分",
    "iterating_through_submasks": "遍历子掩码",
    "knapsack": "0-1背包问题",
    "k_means_clustering_tensorflow": "K-means聚类（TensorFlow）",
    "largest_divisible_subset": "最大可整除子集",
    "longest_common_subsequence": "最长公共子序列（LCS）",
    "longest_common_substring": "最长公共子串",
    "longest_increasing_subsequence": "最长递增子序列（DP）",
    "longest_increasing_subsequence_iterative": "最长递增子序列（迭代）",
    "longest_increasing_subsequence_o_nlogn": "最长递增子序列（O(nlogn)）",
    "longest_palindromic_subsequence": "最长回文子序列",
    "matrix_chain_multiplication": "矩阵链乘法",
    "matrix_chain_order": "矩阵链最优乘法次序",
    "max_non_adjacent_sum": "非相邻最大和",
    "max_product_subarray": "最大子数组乘积",
    "max_subarray_sum": "最大子数组和（Kadane算法）",
    "min_distance_up_bottom": "最小路径（自底向上）",
    "minimum_coin_change": "零钱兑换（最少硬币）",
    "minimum_cost_path": "最小代价路径",
    "minimum_partition": "最小分割差",
    "minimum_size_subarray_sum": "最小长度子数组和",
    "minimum_squares_to_represent_a_number": "最少完全平方数表示",
    "minimum_steps_to_one": "最少步数归一",
    "minimum_tickets_cost": "最少票价成本",
    "narcissistic_number": "水仙花数判断",
    "optimal_binary_search_tree": "最优二叉搜索树",
    "palindrome_partitioning": "回文分割",
    "range_sum_query": "区域和查询（线段树）",
    "regex_match": "正则表达式匹配",
    "rod_cutting": "切钢筋问题",
    "smith_waterman": "Smith-Waterman局部序列比对",
    "subset_generation": "子集生成",
    "sum_of_subset": "子集和问题",
    "trapped_water": "接雨水问题",
    "tribonacci": "Tribonacci数列",
    "viterbi": "维特比算法",
    "wildcard_matching": "通配符匹配",
    "word_break": "单词拆分",
    # 贪心与分治
    "all_combinations": "所有组合",
    "all_permutations": "全排列",
    "all_subsequences": "所有子序列",
    "best_time_to_buy_and_sell_stock": "买卖股票最佳时机",
    "closest_pair_of_points": "最近点对（分治）",
    "coloring": "图着色问题",
    "combination_sum": "组合和",
    "convex_hull": "凸包算法（Graham扫描）",
    "crossword_puzzle_solver": "填字游戏求解",
    "fractional_cover_problem": "集合覆盖（贪心近似）",
    "fractional_knapsack": "分数背包（贪心）",
    "fractional_knapsack_2": "分数背包变体",
    "gas_station": "加油站问题",
    "generate_parentheses": "括号生成",
    "generate_parentheses_iterative": "括号生成（迭代）",
    "hamiltonian_cycle": "哈密顿回路",
    "heaps_algorithm": "Heap算法（全排列）",
    "heaps_algorithm_iterative": "Heap算法（迭代）",
    "inversions": "逆序对统计（归并排序）",
    "knight_tour": "骑士周游问题",
    "kth_order_statistic": "第K顺序统计量",
    "match_word_pattern": "单词模式匹配",
    "max_difference_pair": "最大差值",
    "max_subarray": "最大子数组（分治）",
    "mergesort": "归并排序",
    "minimax": "极小化极大算法",
    "minimum_coin_change": "最少硬币找零",
    "minimum_waiting_time": "最少等待时间",
    "n_queens": "N皇后问题",
    "n_queens_math": "N皇后（数学解法）",
    "optimal_merge_pattern": "最优合并模式（哈夫曼）",
    "peak": "峰值元素查找",
    "power": "快速幂",
    "power_sum": "幂和分解",
    "rat_in_maze": "老鼠走迷宫",
    "smallest_range": "最小范围",
    "strassen_matrix_multiplication": "Strassen矩阵乘法",
    "sudoku": "数独求解",
    "sum_of_subsets": "子集和",
    "word_break": "单词拆分",
    "word_ladder": "单词阶梯",
    "word_search": "单词搜索",
    # 信号与图像
    "adaptive_filter": "自适应滤波器",
    "anomaly_detection": "异常检测",
    "audio_features": "音频特征提取",
    "bilateral_filter": "双边滤波器",
    "blind_source_separation": "盲源分离",
    "butterworth_filter": "巴特沃斯滤波器",
    "change_brightness": "亮度调整",
    "change_contrast": "对比度调整",
    "chebyshev_filter": "切比雪夫滤波器",
    "cnn_classification": "CNN图像分类",
    "color_space": "色彩空间转换",
    "color_transfer": "颜色迁移",
    "complexity_measures": "复杂度度量",
    "contrast_enhancement": "对比度增强",
    "convert_to_negative": "图像反转",
    "corner_detection": "角点检测",
    "curve_fitting": "曲线拟合",
    "dft": "离散傅里叶变换",
    "dimensionality_reduction": "降维处理",
    "discrete_cosine_transform": "离散余弦变换",
    "edge_detection": "边缘检测",
    "extended_kalman": "扩展卡尔曼滤波器",
    "feature_descriptors": "特征描述符",
    "feature_extraction": "特征提取",
    "fft_convolution": "FFT卷积",
    "filter_bank": "滤波器组",
    "finite_differences": "有限差分",
    "fir_filter": "FIR滤波器",
    "flip_augmentation": "翻转数据增强",
    "fourier_descriptors": "傅里叶描述符",
    "frequency_analysis": "频率分析",
    "frequency_filtering": "频域滤波",
    "gabor_filter": "Gabor滤波器",
    "haralick_descriptors": "Haralick纹理描述符",
    "harris_corner": "Harris角点检测",
    "histogram_equalization": "直方图均衡化",
    "horn_schunck": "Horn-Schunck光流",
    "hough_transform": "霍夫变换",
    "iir_filter": "IIR滤波器",
    "image_inpainting": "图像修复",
    "image_registration": "图像配准",
    "image_warp": "图像变形",
    "index_calculation": "图像指标计算",
    "intensity_based_segmentation": "强度分割",
    "interpolation": "插值",
    "interpolation_methods": "插值方法",
    "jpeg_dct": "JPEG DCT压缩",
    "kalman_filter": "卡尔曼滤波器",
    "kmeans_clustering": "K-means聚类",
    "lifting_scheme": "提升格式小波变换",
    "linear_filters": "线性滤波器",
    "mean_threshold": "均值阈值分割",
    "morphological_ops": "形态学操作",
    "mosaic_augmentation": "马赛克数据增强",
    "noise_generation": "噪声生成",
    "non_local_means": "非局部均值去噪",
    "object_detection": "目标检测",
    "optimization": "信号优化",
    "particle_filter": "粒子滤波器",
    "phase_correlation": "相位相关",
    "polynomial_fitting": "多项式拟合",
    "polynomial_roots": "多项式求根",
    "pooling_functions": "池化函数",
    "power_spectrum": "功率谱",
    "region_growing": "区域生长",
    "regression": "回归分析",
    "sepia": "棕褐色滤镜",
    "show_response": "滤波器响应可视化",
    "sift_feature": "SIFT特征",
    "signal_decomposition": "信号分解",
    "signal_decomposition_analysis": "信号分解分析",
    "signal_filtering": "信号滤波",
    "signal_resampling": "信号重采样",
    "signal_similarity": "信号相似度",
    "signal_transforms": "信号变换",
    "sparse_coding": "稀疏编码",
    "spectral_clustering": "谱聚类",
    "statistical_analysis": "统计分析",
    "stft": "短时傅里叶变换",
    "template_matching": "模板匹配",
    "test_digital_image_processing": "数字图像处理测试",
    "texture_analysis": "纹理分析",
    "thresholding": "阈值分割",
    "time_frequency": "时频分析",
    "time_series_analysis": "时间序列分析",
    "video_compression": "视频压缩",
    "watershed_segmentation": "分水岭分割",
    "wavelet_denoising": "小波去噪",
    "wavelet_transform": "小波变换",
    # 网页与编程
    "co2_emission": "CO2排放数据获取",
    "covid_stats_via_xpath": "COVID统计（XPath）",
    "crawl_google_results": "抓取Google搜索结果",
    "crawl_google_scholar_citation": "Google Scholar引用抓取",
    "currency_converter": "货币换算",
    "current_stock_price": "实时股价查询",
    "current_weather": "当前天气查询",
    "daily_horoscope": "每日星座运势",
    "download_images_from_google_query": "下载Google图片",
    "emails_from_url": "从URL提取邮箱",
    "fetch_anime_and_play": "获取动漫信息",
    "fetch_bbc_news": "获取BBC新闻",
    "fetch_github_info": "获取GitHub信息",
    "fetch_jobs": "获取职位信息",
    "fetch_quotes": "获取名人名言",
    "fetch_well_rx_price": "获取药品价格",
    "get_amazon_product_data": "获取Amazon产品数据",
    "get_imdb_top_250_movies_csv": "获取IMDb Top250电影",
    "get_ip_geolocation": "IP地理位置查询",
    "get_top_billionaires": "获取顶级富豪榜",
    "get_top_hn_posts": "获取HackerNews热门帖子",
    "giphy": "GIF搜索（Giphy）",
    "instagram_crawler": "Instagram爬虫",
    "instagram_pic": "Instagram图片下载",
    "instagram_video": "Instagram视频下载",
    "nasa_data": "NASA数据获取",
    "open_google_results": "打开Google搜索结果",
    "random_anime_character": "随机动漫角色",
    "recaptcha_verification": "reCAPTCHA验证",
    "reddit": "Reddit数据获取",
    "search_books_by_isbn": "按ISBN搜索书籍",
    "slack_message": "发送Slack消息",
    "test_fetch_github_info": "GitHub信息获取测试",
    "world_covid19_stats": "全球COVID19统计",
    # 位运算
    "binary_and_operator": "二进制AND运算",
    "binary_coded_decimal": "BCD编码",
    "binary_count_setbits": "统计二进制位数",
    "binary_count_trailing_zeros": "统计尾随零",
    "binary_gcd": "二进制GCD（Stein算法）",
    "binary_or_operator": "二进制OR运算",
    "binary_shifts": "二进制移位",
    "binary_twos_complement": "二进制补码",
    "binary_xor_operator": "二进制XOR运算",
    "bit_encoding": "位编码",
    "bit_manipulation_tricks": "位操作技巧",
    "bit_optimization": "位运算优化",
    "bit_scan_reverse": "位扫描反转",
    "bitmap_index": "位图索引",
    "bitwise_addition_recursive": "位运算递归加法",
    "bloom_filter": "布隆过滤器",
    "chudnovsky_multiplication": "Chudnovsky乘法（π计算）",
    "count_1s_brian_kernighan_method": "Brian Kernighan法统计1的个数",
    "count_number_of_one_bits": "统计位1的个数",
    "crc_checksum": "CRC校验和",
    "excess_3_code": "余3码",
    "find_previous_power_of_two": "找前一个2的幂",
    "find_unique_number": "找唯一数",
    "gray_code": "格雷码",
    "gray_code_sequence": "格雷码序列",
    "hamming_distance": "汉明距离",
    "highest_set_bit": "最高设置位",
    "index_of_rightmost_set_bit": "最右设置位索引",
    "is_even": "判断偶数",
    "is_power_of_two": "判断2的幂",
    "largest_pow_of_two_le_num": "不大于数的最大2的幂",
    "missing_number": "缺失数字",
    "numbers_different_signs": "符号不同判断",
    "power_of_4": "判断4的幂",
    "reverse_bits": "反转二进制位",
    "segment_tree_bit": "位运算线段树",
    "single_bit_manipulation_operations": "单比特操作",
    "solinas_reduction": "Solinas约简",
    "swap_all_odd_and_even_bits": "交换奇偶位",
}

CLASS_MAP = {
    "KalmanFilter": "卡尔曼滤波器",
    "ParticleFilter": "粒子滤波器",
    "AdaptiveFilter": "自适应滤波器",
    "ButterworthFilter": "巴特沃斯滤波器",
    "ChebyshevFilter": "切比雪夫滤波器",
    "FIRFilter": "FIR滤波器",
    "IIRFilter": "IIR滤波器",
}


def is_cjk(char):
    return '\u4e00' <= char <= '\u9fff'


def has_real_chinese(text):
    """判断是否有实际中文注释（跳过docstring中的中文）"""
    lines = text.split('\n')
    in_multiline = False
    multiline_delim = None
    result_lines = []
    for line in lines:
        if not in_multiline:
            if '"""' in line:
                parts = line.split('"""', 2)
                if len(parts) == 3 and parts[0] == '':
                    # 单行 docstring: """内容"""
                    continue
                # 开始多行docstring
                in_multiline = True
                multiline_delim = '"""'
                remaining = parts[1] if len(parts) > 1 else ''
                if len(parts) == 3 and parts[2]:
                    in_multiline = False
                    if remaining:
                        result_lines.append(remaining)
                    if parts[2].strip():
                        result_lines.append(parts[2])
            elif "'''" in line:
                parts = line.split("'''", 2)
                if len(parts) == 3 and parts[0] == '':
                    continue
                in_multiline = True
                multiline_delim = "'''"
                remaining = parts[1] if len(parts) > 1 else ''
                if len(parts) == 3 and parts[2]:
                    in_multiline = False
                    if remaining:
                        result_lines.append(remaining)
                    if parts[2].strip():
                        result_lines.append(parts[2])
            else:
                result_lines.append(line)
        else:
            if multiline_delim and multiline_delim in line:
                in_multiline = False
    clean_text = '\n'.join(result_lines)
    for ch in clean_text:
        if is_cjk(ch):
            return True
    return False


def has_main_guard(text):
    return bool(re.search(r'if\s+__name__\s*==\s*["\']__main__["\']:', text))


def get_module_name(filepath):
    name = os.path.basename(filepath)
    if name.endswith('.py'):
        name = name[:-3]
    return name


def build_top_docstring(module_name, category_cn):
    return f'''# -*- coding: utf-8 -*-
"""
{module_name}

算法分类：{category_cn}
描述：实现 {module_name} 算法的核心逻辑。
"""


'''


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 判断是否已有中文注释（跳过已有中文注释的文件）
    if has_real_chinese(content):
        return 'skip', '已有中文注释'

    if has_main_guard(content):
        needs_main = False
    else:
        needs_main = True

    module_name = get_module_name(filepath)
    dirname = os.path.basename(os.path.dirname(filepath))
    category_cn = CAT_MAP.get(dirname, dirname)

    lines = content.split('\n')

    # --- 1. 处理顶部 docstring ---
    # 判断第一行是否是 # -*- coding: utf-8 -*- 或类似
    first_line = lines[0].strip() if lines else ''
    has_coding = first_line.startswith('#') and 'coding' in first_line

    # 找现有 docstring 起始位置
    docstring_start = -1
    docstring_end = -1
    search_start = 1 if has_coding else 0
    if search_start < len(lines):
        second_line = lines[search_start].strip()
        if second_line.startswith('"""') or second_line.startswith("'''"):
            docstring_start = search_start
            delim = second_line[:3]
            # 单行docstring
            if delim in second_line[3:]:
                docstring_end = search_start
            else:
                for i in range(search_start + 1, len(lines)):
                    if delim in lines[i]:
                        docstring_end = i
                        break

    # 构建新 header
    new_header_lines = []
    if docstring_start == -1:
        # 需要添加 docstring
        new_header_lines = build_top_docstring(module_name, category_cn).split('\n')[:-1]  # 去掉末尾空行

    # --- 2. 在函数/类定义前插入中文注释 ---
    output_lines = []
    inserted_defs = set()  # 防止重复
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 检测函数定义
        fn_m = re.match(r'^(def\s+(\w+)\s*\(.*?\):)', stripped)
        if fn_m:
            fn_name = fn_m.group(2)
            if fn_name not in inserted_defs:
                desc = COMMENT_MAP.get(fn_name, f'{fn_name} 算法')
                output_lines.append(f'# {desc}')
                inserted_defs.add(fn_name)
            output_lines.append(line)
            i += 1
            continue

        # 检测类定义
        cls_m = re.match(r'^(class\s+(\w+))', stripped)
        if cls_m:
            cls_name = cls_m.group(2)
            if cls_name not in inserted_defs:
                desc = CLASS_MAP.get(cls_name, f'{cls_name} 类')
                output_lines.append(f'# {desc}')
                inserted_defs.add(cls_name)
            output_lines.append(line)
            i += 1
            continue

        output_lines.append(line)
        i += 1

    # 合并回去
    if new_header_lines:
        output_lines = new_header_lines + output_lines

    final_content = '\n'.join(output_lines)

    # --- 3. 添加 if __name__ block ---
    if needs_main:
        # 提取模块中第一个函数名（用于测试提示）
        fn_match = re.search(r'def\s+(\w+)\s*\(', final_content)
        first_fn = fn_match.group(1) if fn_match else 'main'
        test_block = f'''

if __name__ == '__main__':
    # 测试 {module_name}
    print(f'Testing {{__name__}}...')
    # TODO: 添加测试用例
    print('测试完成')
'''
        final_content = final_content.rstrip() + test_block

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)

    if needs_main:
        return 'fix', '已添加中文docstring、函数注释、main guard'
    else:
        return 'fix', '已添加中文docstring和函数注释'


def main():
    fixed = 0
    skipped = 0
    fix_log = []
    skip_log = []

    for dirname in DIRS:
        dirpath = os.path.join(BASE, dirname)
        pattern = os.path.join(dirpath, '*.py')
        files = glob.glob(pattern)

        for filepath in sorted(files):
            if filepath.endswith('__init__.py'):
                skipped += 1
                skip_log.append((filepath, '__init__.py'))
                continue

            result, reason = process_file(filepath)
            if result == 'fix':
                fixed += 1
                fix_log.append((filepath, reason))
            else:
                skipped += 1
                skip_log.append((filepath, reason))

    print(f"[FIX] {fixed} files")
    print(f"[SKIP] {skipped} files")
    print()
    print("=== FIXED ===")
    for fp, reason in fix_log:
        print(f"  [+] {os.path.relpath(fp, BASE)} | {reason}")
    print()
    print("[SKIP]")
    for fp, reason in skip_log:
        print(f"      {os.path.relpath(fp, BASE)} | {reason}")

if __name__ == '__main__':
    main()
