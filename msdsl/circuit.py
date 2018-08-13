from sympy import symbols, solve, linear_eq_to_matrix
from itertools import count, combinations

from msdsl.components import *

def expr_to_dict(expr):
    syms = list(expr.free_symbols)
    sym_names = [sym.name for sym in syms]

    A, b = linear_eq_to_matrix([expr], syms)

    vars  = [float(x) for x in A]
    const = -float(b[0])

    return {'vars': dict(zip(sym_names, vars)), 'const': const}

class NodalAnalysis:
    def __init__(self):
        self.kcl = {}
        self.other_equations = []

    @property
    def equations(self):
        return list(self.kcl.values()) + self.other_equations

    def set_equal(self, lhs, rhs):
        self.other_equations.append(lhs - rhs)

    def add_current(self, p, n, expr):
        self.kcl[p] = self.kcl.get(p, 0) - expr
        self.kcl[n] = self.kcl.get(n, 0) + expr


class StateVariable:
    def __init__(self, variable, derivative):
        self.variable = variable
        self.derivative = derivative


class ComponentNamer:
    def __init__(self):
        self.prefixes = {}

    def make(self, prefix):
        if prefix not in self.prefixes:
            self.prefixes[prefix] = count()

        return prefix + str(next(self.prefixes[prefix]))


class SymbolNamespace:
    def __init__(self):
        self.sym_names = set()

    def define(self, *args):
        # check that variable names are unique
        for arg in args:
            assert arg not in self.sym_names, 'Variable already defined: ' + arg
            self.sym_names.add(arg)

        # return new symbol(s)
        return symbols(args)


class Circuit:
    def __init__(self):
        self.namespace = SymbolNamespace()
        self.namer = ComponentNamer()

        self.ext_syms = []
        self.int_syms = []

        self.state_vars = []

        self.static_comps = []
        self.diode_comps = []
        self.mosfet_comps = []

        self.inductor_state_vars = []
        self.capacitor_state_vars = []

    def external(self, *args):
        retval = self.namespace.define(*args)

        self.ext_syms.extend(retval)

        if len(args) == 1:
            return retval[0]
        else:
            return retval

    def internal(self, *args):
        retval = self.namespace.define(*args)

        self.int_syms.extend(retval)

        if len(args) == 1:
            return retval[0]
        else:
            return retval

    def state(self, variable, derivative):
        retval = StateVariable(variable=variable, derivative=derivative)

        self.state_vars.append(retval)

        return retval

    def voltage_source(self, p, n, expr=None, name=None):
        name = name if name is not None else self.namer.make(VoltageSource.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = VoltageSource(port=Port(p=p, n=n, v=v, i=i), expr=expr, name=name)

        self.static_comps.append(retval)

        return retval

    def current_source(self, p, n, expr=None, name=None):
        name = name if name is not None else self.namer.make(CurrentSource.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = CurrentSource(port=Port(p=p, n=n, v=v, i=i), expr=expr, name=name)

        self.static_comps.append(retval)

        return retval

    def resistor(self, p, n, value, name=None):
        name = name if name is not None else self.namer.make(Resistor.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = Resistor(port=Port(p=p, n=n, v=v, i=i), value=value, name=name)

        self.static_comps.append(retval)

        return retval

    def inductor(self, p, n, value, name=None):
        name = name if name is not None else self.namer.make(Inductor.prefix)
        v, i, di_dt = self.internal('v_' + name, 'i_' + name, 'di_dt_' + name)

        state = self.state(variable=i, derivative=di_dt)
        self.inductor_state_vars.append(state)

        retval = Inductor(port=Port(p=p, n=n, v=v, i=i), state=state, value=value, name=name)

        self.static_comps.append(retval)

        return retval

    def capacitor(self, p, n, value, name=None):
        name = name if name is not None else self.namer.make(Capacitor.prefix)
        v, i, dv_dt = self.internal('v_' + name, 'i_' + name, 'dv_dt_' + name)

        state = self.state(variable=v, derivative=dv_dt)
        self.capacitor_state_vars.append(state)

        retval = Capacitor(port=Port(p=p, n=n, v=v, i=i), state=state, value=value, name=name)
        self.static_comps.append(retval)

        return retval

    def transformer(self, p1, n1, p2, n2, n, name=None):
        name = name if name is not None else self.namer.make(Transformer.prefix)
        v1, i1, v2, i2 = self.internal('v1_' + name, 'i1_' + name, 'v2_' + name, 'i2_' + name)

        retval = Transformer(port1=Port(p=p1, n=n1, v=v1, i=i1), port2=Port(p=p2, n=n2, v=v2, i=i2), n=n, name=name)
        self.static_comps.append(retval)

        return retval

    def mosfet(self, p, n, name=None):
        name = name if name is not None else self.namer.make(MOSFET.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = MOSFET(port=Port(p=p, n=n, v=v, i=i), name=name)
        self.mosfet_comps.append(retval)

        return retval

    def diode(self, p, n, vf=0, name=None):
        name = name if name is not None else self.namer.make(Diode.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = Diode(port=Port(p=p, n=n, v=v, i=i), vf=vf, name=name)
        self.diode_comps.append(retval)

        return retval

    def solve(self, dt, output_vars=None):
        if output_vars is None:
            output_vars = []

        circuit = {
            'dt': dt,
            'diodes': {diode.name: {'v': diode.port.v.name,
                                    'i': diode.port.i.name,
                                    'vf': diode.vf}
                       for diode in self.diode_comps},
            'mosfets': [mosfet.name for mosfet in self.mosfet_comps],
            'states': [state.variable.name for state in self.state_vars],
            'outputs': [output.name for output in output_vars],
            'ext_syms': [sym.name for sym in self.ext_syms]
        }

        cases = []
        dyn_comps = self.mosfet_comps + self.diode_comps

        for i in range(2**(len(dyn_comps))):
            # determine modes of dynamic components
            dyn_modes = [bool((i >> j) & 1) for j in range(len(dyn_comps))]
            dyn_modes = {comp.name: ('on' if mode else 'off')
                         for comp, mode in zip(dyn_comps, dyn_modes)}

            # append the result if it exists
            case = self.solve_case(dt=dt, output_vars=output_vars, dyn_modes=dyn_modes)

            if case is not None:
                cases.append(case)

        circuit['cases'] = cases

        return circuit

    def solve_case(self, dt, output_vars=None, dyn_modes=None, max_attempts=10):
        # set defaults

        if output_vars is None:
            output_vars = []
        if dyn_modes is None:
            dyn_modes = {}

        # create new analysis object

        analysis = NodalAnalysis()

        # handle static components

        for comp in self.static_comps:
            comp.add_to_analysis(analysis)

        # handle dynamic components

        dyn_comps = self.mosfet_comps + self.diode_comps
        dyn_comps = {value.name: value for value in dyn_comps}

        for name, state in dyn_modes.items():
            dyn_comps[name].add_to_analysis(state, analysis)

        # generate a list of different configurations to try, in which different combinations of
        # inductors are effectively disabled

        configs = []
        for k in range(len(self.inductor_state_vars)+1):
            done = False
            for combo in combinations(self.inductor_state_vars, k):
                if len(configs) < max_attempts:
                    configs.append(set(combo))
                else:
                    done = True
                    break
            if done:
                break

        # loop through the configs until a solution is found

        for disabled_state_vars in configs:

            # make copies of the variables to solve for
            solve_vars = self.int_syms[:]
            eqns = analysis.equations[:]

            # configure the system of equations
            for state_var in self.state_vars:
                if state_var not in disabled_state_vars:
                    solve_vars.remove(state_var.variable)
                else:
                    eqns.append(state_var.derivative)

            # use sympy solve to solve the system of equations
            soln = solve(eqns, solve_vars)
            if not soln:
                continue

            # construct the output
            case = {}

            already_solved = set()

            # compute state update equations
            case['states'] = {}
            for state_var in self.state_vars:
                if state_var not in disabled_state_vars:
                    expr = state_var.variable + dt*soln[state_var.derivative]
                else:
                    expr = soln[state_var.variable]

                case['states'][state_var.variable.name] = expr_to_dict(expr)

                already_solved.add(state_var.variable)

            # compute diode update equations
            case['diodes'] = {}
            for diode in self.diode_comps:
                case['diodes'][diode.name] = {
                    diode.port.i.name: expr_to_dict(soln[diode.port.i]),
                    diode.port.v.name: expr_to_dict(soln[diode.port.v])
                }

                already_solved.add(diode.port.v)
                already_solved.add(diode.port.i)

            # list all output variables
            case['outputs'] = {}
            for output in output_vars:
                if output not in already_solved:
                    expr = soln[output]
                else:
                    expr = output

                case['outputs'][output.name] = expr_to_dict(expr)

            # add the modes of dynamic components to the dictionary
            case['dyn_modes'] = dyn_modes

            return case

        return None