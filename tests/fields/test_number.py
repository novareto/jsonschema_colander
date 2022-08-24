import pytest
import hamcrest
import colander
import jsonschema_colander.validators
from jsonschema_colander.types import Number


def test_max():
    field = Number.from_json('test', True, {
        "type": "integer",
        "maximum": 20
    })

    constraints = field.get_options()
    hamcrest.assert_that(constraints, hamcrest.has_entries({
        'validator': hamcrest.instance_of(
            jsonschema_colander.validators.NumberRange
        )
    }))

    assert field.required is True
    assert field.get_factory() == colander.Integer
    schema = field()

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize(21)
    assert exc.value.asdict() == {
        'test': '21 is greater than maximum value 20'}

    assert schema.deserialize(12) == 12


def test_min():
    field = Number.from_json('test', True, {
        "type": "number",
        "minimum": 2.99,
        "default": 5.0
    })
    constraints = field.get_options()
    hamcrest.assert_that(constraints, hamcrest.has_entries({
        'validator': hamcrest.instance_of(
            jsonschema_colander.validators.NumberRange
        )
    }))
    assert field.required is True
    assert field.attributes['default']
    assert field.get_factory() == colander.Float

    schema = field()
    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize(2.10)
    assert exc.value.asdict() == {
        'test': '2.1 is less than minimum value 2.99'}

    assert schema.deserialize(12) == 12


def test_exclusive_minmax():

    field = Number.from_json('test', True, {
        "type": "integer",
        "exclusiveMinimum": 2,
        "exclusiveMaximum": 15
    })
    constraints = field.get_options()
    hamcrest.assert_that(constraints, hamcrest.has_entries({
        'validator': hamcrest.instance_of(
            jsonschema_colander.validators.NumberRange
        )
    }))
    assert field.required is True
    assert field.get_factory() == colander.Integer

    schema = field()
    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize(1)
    assert exc.value.asdict() == {
        'test': '1 is less than minimum value 2'}

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize(2)
    assert exc.value.asdict() == {
        'test': '2 is less than minimum value 2'}

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize(16)
    assert exc.value.asdict() == {
        'test': '16 is greater than maximum value 15'}

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize(15)
    assert exc.value.asdict() == {
        'test': '15 is greater than maximum value 15'}

    assert schema.deserialize(10) == 10


# def test_enum():
#     field = Number.from_json('test', True, {
#         "type": "integer",
#         "enum": [1, 2]
#     })

#     assert field.required is True
#     assert field.get_factory() == wtforms.fields.SelectField
#     form = wtforms.form.BaseForm({"test": field()})
#     form.process(data={'test': 9})
#     assert form.validate() is False
#     assert form.errors == {'test': ['Not a valid choice.']}

#     form.process(data={'test': 1})
#     assert form.validate() is True
#     assert not form.errors
