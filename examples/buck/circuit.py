from msdsl.circuit import Circuit
from msdsl.format import dump_model

# ref: http://www.simonbramble.co.uk/dc_dc_converter_design/buck_converter/buck_converter_design.htm

# create new circuit
cir = Circuit()

# create nodes
v_in, v_sw, v_out = cir.nodes('v_in', 'v_sw', 'v_out')

# input voltage
input_ = cir.input_('input')
cir.voltage_source(v_in, 0, expr=input_)

# switches
cir.mosfet(v_in, v_sw)
diode = cir.diode(0, v_sw)

# filter
ind = cir.inductor(v_sw, v_out, value=4.7e-6)
cir.capacitor(v_out, 0, value=150e-6)

# output load
cir.resistor(v_out, 0, value=2)

# define outputs
cir.output(v_out)

# solve the circuit
cir.solve(20e-9)

# dump the model
dump_model(cir.model)