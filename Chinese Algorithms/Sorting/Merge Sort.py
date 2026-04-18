Merge Sort - 归并排序

原理: 分治法, O(n log n), 稳定

def merge_sort(arr):
    if len(arr) < 2:
        return arr
    mid = len(arr)//2
    return merge(merge_sort(arr[:mid]), merge_sort(arr[mid:]))

def merge(a, b):
    r = []
    while a and b:
        r.append(a.pop(0) if a[0]<=b[0] else b.pop(0))
    return r + a + b
