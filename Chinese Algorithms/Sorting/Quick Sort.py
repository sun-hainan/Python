Quick Sort - 快速排序

原理: 分治法, O(n log n), 不稳定

def quick_sort(arr):
    if len(arr) < 2:
        return arr
    pivot = arr[len(arr)//2]
    less = [x for x in arr if x < pivot]
    more = [x for x in arr if x > pivot]
    return quick_sort(less) + [pivot] + quick_sort(more)
