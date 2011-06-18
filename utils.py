def sort_with_elem_as_first(first, lst):
    lst.sort()
    lst.remove(first)
    lst.insert(0, first)
    return lst
