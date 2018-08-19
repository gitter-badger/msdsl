import json
from marshmallow import Schema, fields, post_load

from msdsl.model import AnalogSignal, DigitalSignal, CaseLinearExpr, MixedSignalModel, CaseCoeffProduct

def load_model(data):
    schema = MixedSignalModelSchema()
    return schema.load(json.loads(data)).data

def dump_model(model, pretty=True):
    schema = MixedSignalModelSchema()

    kwargs = {}
    if pretty:
        kwargs['sort_keys'] = True
        kwargs['indent'] = 2

    data = schema.dump(model).data
    print(json.dumps(data, **kwargs))


class CaseCoeffProductSchema(Schema):
    coeffs = fields.List(fields.Number())
    var = fields.Str(allow_none=True)

    @post_load
    def make_object(self, data):
        return CaseCoeffProduct(**data)


class CaseLinearExprSchema(Schema):
    prods = fields.Nested(CaseCoeffProductSchema(), many=True)
    const = fields.Nested(CaseCoeffProductSchema())

    @post_load
    def make_object(self, data):
        return CaseLinearExpr(**data)


class AnalogSignalSchema(Schema):
    name = fields.Str()
    range_ = fields.List(fields.Number(), allow_none=True)
    rel_tol = fields.Number(allow_none=True)
    abs_tol = fields.Number(allow_none=True)
    expr = fields.Nested(CaseLinearExprSchema(), allow_none=True)
    initial = fields.Number(allow_none=True)

    @post_load
    def make_object(self, data):
        return AnalogSignal(**data)


class DigitalSignalSchema(Schema):
    name = fields.Str()
    signed = fields.Boolean()
    width = fields.Integer()
    expr = fields.Nested(CaseLinearExprSchema(), allow_none=True)
    initial = fields.Integer(allow_none=True)

    @post_load
    def make_object(self, data):
        return DigitalSignal(**data)


class MixedSignalModelSchema(Schema):
    mode = fields.List(fields.String())
    analog_inputs = fields.Nested(AnalogSignalSchema(), many=True)
    digital_inputs = fields.Nested(DigitalSignalSchema(), many=True)
    analog_outputs = fields.Nested(AnalogSignalSchema(), many=True)
    digital_outputs = fields.Nested(DigitalSignalSchema(), many=True)
    analog_states = fields.Nested(AnalogSignalSchema(), many=True)
    digital_states = fields.Nested(DigitalSignalSchema(), many=True)

    @post_load
    def make_object(self, data):
        return MixedSignalModel(**data)