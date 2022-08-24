import hamcrest
import colander
from jsonschema_colander.types import Boolean


def test_boolean():
    field = Boolean.from_json('test', True, {
        "type": "boolean",
        "default": "true"
    })

    constraints = field.get_options()
    hamcrest.assert_that(constraints, hamcrest.has_entries({
        'missing': colander.required
    }))

    assert field.required is True
    assert field.attributes['default']
    assert field.get_factory() == colander.Boolean

    schema = field()
    assert schema.deserialize(1) == 1
