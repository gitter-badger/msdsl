import numpy as np
from math import ceil, log2
from .expr.table import RealTable
from .expr.expr import clamp_op, to_uint, to_sint

class Function:
    def __init__(self, func, domain, name='real_func', dir='.',
                 numel=512, order=0, clamp=True, coeff_widths=None,
                 coeff_exps=None):
        # set defaults
        if coeff_widths is None:
            coeff_widths = [18]*(order+1)
        if coeff_exps is None:
            coeff_exps = [None]*(order+1)

        # save settings
        self.func = func
        self.domain = domain
        self.name = name
        self.dir = dir
        self.numel = numel
        self.order = order
        self.clamp = clamp
        self.coeff_widths = coeff_widths
        self.coeff_exps = coeff_exps

        # initialize variables
        self.tables = None
        self.create_tables()

    @property
    def addr_bits(self):
        return int(ceil(log2(self.numel)))

    def create_tables(self):
        self.tables = []
        samp = np.linspace(self.domain[0], self.domain[1], self.numel)
        vals = self.func(samp)
        name = f'{self.name}_0'
        table = RealTable(vals=vals, width=self.coeff_widths[0],
                          exp=self.coeff_exps[0], name=name,
                          dir=self.dir)
        self.tables.append(table)

    def eval_on(self, samp):
        addr = (samp - self.domain[0])*((self.numel-1)/(self.domain[1]-self.domain[0]))
        if self.clamp:
            addr = np.clip(addr, 0, self.numel-1)
        addr = addr.astype(np.int)
        return self.tables[0].vals[addr]

    def get_addr_expr(self, in_):
        # calculate result as a real number
        expr = (in_ - self.domain[0])*((self.numel-1)/(self.domain[1]-self.domain[0]))
        # convert to a signed integer
        expr = to_sint(expr, width=self.addr_bits+1)
        # clamp if needed
        if self.clamp:
            expr = clamp_op(expr, 0, self.numel-1)
        # convert to an unsigned integer
        return to_uint(expr, width=self.addr_bits)