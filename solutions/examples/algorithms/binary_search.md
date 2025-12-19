# Binary Search

**Time:** O(log n)  |  **Space:** O(1)

## How It Works

Search a sorted array by repeatedly halving the search space:
1. Compare target with middle element
2. If equal, found; if less, search left half; if greater, search right half
3. Repeat until found or space exhausted

**Invariant:** Target, if present, is always within [lo, hi].

## Implementation

```python
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

## When to Use

- Sorted array or sequence
- Need O(log n) search
- Finding insertion point, bounds, or threshold
