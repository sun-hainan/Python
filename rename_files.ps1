# Rename script for 计算机算法 Python files
# Format: 中文名(EnglishName).py
# EnglishName keeps original filename without underscores

$base = "D:\openclaw-home\.openclaw\workspace\计算机算法"
$dirs = @("greedy","greedy_methods","backtracking","divide_and_conquer","search_algorithms","searches","hashes","bit_manipulation","sorting_algorithms")

# Mapping: EnglishName = Chinese translation
$nameMap = @{
    # greedy
    "activity_selection" = "活动选择问题"
    "dijkstra_heap" = "Dijkstra算法堆优化版"
    "gas_station" = "加油站问题"
    "huffman_coding" = "Huffman编码"

    # greedy_methods
    "best_time_to_buy_and_sell_stock" = "股票最佳买卖时机"
    "fractional_cover_problem" = "集合覆盖问题"
    "fractional_knapsack" = "分数背包问题"
    "fractional_knapsack_2" = "分数背包问题2"
    "minimum_coin_change" = "最少硬币找零"
    "minimum_waiting_time" = "最少等待时间"
    "optimal_merge_pattern" = "最优归并模式"
    "smallest_range" = "最小范围"

    # backtracking
    "all_combinations" = "全组合"
    "all_permutations" = "全排列"
    "all_subsequences" = "全子集"
    "coloring" = "图染色问题"
    "combination_sum" = "组合总和"
    "crossword_puzzle_solver" = "纵横字谜求解器"
    "generate_parentheses" = "生成括号"
    "generate_parentheses_iterative" = "生成括号迭代版"
    "hamiltonian_cycle" = "哈密顿回路"
    "knight_tour" = "骑士周游问题"
    "match_word_pattern" = "单词模式匹配"
    "minimax" = "极大极小算法"
    "n_queens" = "N皇后问题"
    "n_queens_math" = "N皇后问题数学版"
    "power_sum" = "幂次之和"
    "rat_in_maze" = "老鼠走迷宫"
    "sudoku" = "数独求解器"
    "sum_of_subsets" = "子集和问题"
    "word_break" = "单词拆分"
    "word_ladder" = "单词阶梯"
    "word_search" = "单词搜索"

    # divide_and_conquer
    "closest_pair_of_points" = "最近点对问题"
    "convex_hull" = "凸包问题"
    "heaps_algorithm" = "堆排列算法"
    "heaps_algorithm_iterative" = "堆排列算法迭代版"
    "inversions" = "逆序对统计"
    "kth_order_statistic" = "第K顺序统计量"
    "max_difference_pair" = "最大差值对"
    "max_subarray" = "最大子数组"
    "mergesort" = "归并排序"
    "peak" = "峰值查找"
    "power" = "幂运算"
    "strassen_matrix_multiplication" = "Strassen矩阵乘法"

    # search_algorithms
    "ida_star" = "IDA星算法"
    "uniform_cost_search" = "统一代价搜索"

    # searches
    "binary_search" = "二分搜索"
    "binary_tree_traversal" = "二叉树遍历"
    "double_linear_search" = "双向线性搜索"
    "double_linear_search_recursion" = "双向线性搜索递归版"
    "exponential_search" = "指数搜索"
    "fibonacci_search" = "斐波那契搜索"
    "hill_climbing" = "爬山算法"
    "interpolation_search" = "插值搜索"
    "jump_search" = "跳跃搜索"
    "linear_search" = "线性搜索"
    "median_of_medians" = "中位数的中位数"
    "quick_select" = "快速选择"
    "sentinel_linear_search" = "哨兵线性搜索"
    "simple_binary_search" = "简单二分搜索"
    "simulated_annealing" = "模拟退火算法"
    "tabu_search" = "禁忌搜索算法"
    "ternary_search" = "三分搜索"

    # hashes
    "adler32" = "Adler32校验算法"
    "chaos_machine" = "混沌机器"
    "djb2" = "DJB2哈希算法"
    "elf" = "ELF哈希算法"
    "enigma_machine" = "恩尼格玛密码机"
    "fletcher16" = "Fletcher16校验算法"
    "hamming_code" = "汉明码"
    "luhn" = "Luhn算法"
    "md5" = "MD5哈希算法"
    "sdbm" = "SDBM哈希算法"
    "sha1" = "SHA1哈希算法"
    "sha256" = "SHA256哈希算法"

    # bit_manipulation
    "binary_and_operator" = "二进制与运算"
    "binary_coded_decimal" = "二进制编码的十进制"
    "binary_count_setbits" = "统计二进制1的个数"
    "binary_count_trailing_zeros" = "统计二进制末尾零的个数"
    "binary_or_operator" = "二进制或运算"
    "binary_shifts" = "二进制移位操作"
    "binary_twos_complement" = "二进制补码"
    "binary_xor_operator" = "二进制异或运算"
    "bitwise_addition_recursive" = "二进制加法递归版"
    "bit_mask" = "位掩码"
    "count_1s_brian_kernighan_method" = "BrianKernighan方法统计1的个数"
    "count_number_of_one_bits" = "统计位1的个数"
    "excess_3_code" = "余3码"
    "find_previous_power_of_two" = "找前一个2的幂"
    "find_unique_number" = "找唯一数"
    "gray_code_sequence" = "格雷码序列"
    "highest_set_bit" = "最高位1的位置"
    "index_of_rightmost_set_bit" = "最低位1的位置"
    "is_even" = "判断偶数"
    "is_power_of_two" = "判断2的幂"
    "largest_pow_of_two_le_num" = "不超过num的最大2的幂"
    "missing_number" = "寻找缺失数字"
    "numbers_different_signs" = "符号不同判断"
    "power_of_4" = "判断4的幂"
    "reverse_bits" = "反转比特位"
    "single_bit_manipulation_operations" = "单比特操作"
    "state_compression" = "状态压缩"
    "swap_all_odd_and_even_bits" = "奇偶位交换"
}

$results = @()
$errors = @()

foreach ($dir in $dirs) {
    $path = Join-Path $base $dir
    if (-not (Test-Path $path)) { continue }

    $files = Get-ChildItem -Path $path -Filter "*.py" | Where-Object { $_.Name -ne "__init__.py" }
    foreach ($file in $files) {
        $stem = $file.BaseName  # filename without extension

        if (-not $nameMap.ContainsKey($stem)) {
            Write-Host "[SKIP] No mapping for: $stem"
            continue
        }

        $chinese = $nameMap[$stem]
        # Convert stem to EnglishName: remove underscores, keep camelCase style
        $english = $stem -replace '_', ''
        $newName = "${chinese}(${english}).py"
        $newPath = Join-Path $file.DirectoryName $newName

        if (Test-Path $newPath) {
            Write-Host "[SKIP] Already exists: $newName"
            continue
        }

        # Validate syntax before rename
        $syntaxOk = $true
        try {
            $null = python -m py_compile $file.FullName 2>&1
        } catch {
            $syntaxOk = $false
        }

        if (-not $syntaxOk) {
            Write-Host "[ERROR] Syntax error in: $($file.Name)"
            $errors += $file.FullName
            continue
        }

        Rename-Item -Path $file.FullName -NewName $newName -ErrorAction Stop
        $results += @{ old = $file.Name; new = $newName; dir = $dir }
        Write-Host "[OK] $($file.Name) -> $newName"
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "Total renamed: $($results.Count)"
Write-Host "Errors: $($errors.Count)"
Write-Host ""
Write-Host "Details:"
foreach ($r in $results) {
    Write-Host "  $($r.old) -> $($r.new) [$($r.dir)]"
}
