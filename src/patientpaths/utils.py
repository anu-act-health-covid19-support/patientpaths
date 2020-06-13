def enumerate_all_sublists(l):
    a = []
    if isinstance(l, list):
        for ll in l:
            a += enumerate_all_sublists(ll)
        return a
    else:
        return [l]
