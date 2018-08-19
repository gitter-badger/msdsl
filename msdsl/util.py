from itertools import count, combinations
from interval import interval
from collections import Iterable
from sympy import symbols

def listify(x):
    if not isinstance(x, Iterable):
        return list(x)
    else:
        return x

def to_interval(obj):
    if isinstance(obj, interval):
        return obj
    else:
        return interval[obj[0], obj[1]]

def all_combos(vals):
    for k in range(len(vals) + 1):
        for combo in combinations(vals, k):
            yield(set(combo))

class Namespace:
    def __init__(self):
        self.prefixes = {}
        self.names = set()

    def make(self, name=None, prefix=None, tries=None) :
        # set defaults
        if tries is None:
            tries = 100

        if name is not None:
            assert name not in self.names, 'Name already defined: ' + name
        else:
            assert prefix is not None, "Must provide prefix if name isn't provided."

            if prefix not in self.prefixes:
                self.prefixes[prefix] = count()

            for _ in range(tries):
                name = prefix + str(next(self.prefixes[prefix]))
                if name not in self.names:
                    break
            else:
                raise Exception('Could not define name with prefix: ' + prefix)


        self.names.add(name)

        return name


class SymbolNamespace(Namespace):
    def make(self, name=None, prefix=None, tries=None):
        name = super().make(name=name, prefix=prefix, tries=tries)
        return symbols(name)