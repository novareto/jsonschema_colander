import pytest
import hamcrest
import colander
import jsonschema
import jsonschema_colander.types

"""
We handle object-typed schema.
They can be fields in a form or just a plain form.
They are created just like any other field.
"""


def test_extended_validation(extended_validation_schema):

    schema = jsonschema_colander.types.Object.from_json(extended_validation_schema)

    hamcrest.assert_that(schema.fields, hamcrest.has_entries({
        "grund": hamcrest.instance_of(
            jsonschema_colander.types.String),
        "grund2": hamcrest.instance_of(
            jsonschema_colander.types.String),
    }))

    assert schema.fields["grund"].required is False
    assert schema.fields["grund2"].required is False

    schema = schema()
    assert schema.deserialize({}) == {}
    assert schema.deserialize({'grund': 'test'}) == {'grund': 'test'}
    with pytest.raises(colander.Invalid):
        assert schema.deserialize({'grund': 'AGrund'}) == {'grund': 'AGrund'}
    assert schema.deserialize({'grund': 'AGrund', 'grund2': 'test'}) == {'grund': 'AGrund', 'grund2': 'test'}
