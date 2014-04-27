from __future__ import absolute_import


def sort_with_elem_as_first(first, lst):
    lst.sort()
    if first in lst:
        lst.remove(first)
        lst.insert(0, first)
    return lst
