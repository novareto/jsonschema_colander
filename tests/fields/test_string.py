import pytest
import hamcrest
import colander
from jsonschema_colander.types import String


def test_string_config():
    field = String.from_json({
        "type": "string",
    }, config={
        '': {
            'validators': [colander.url]
        }
    })
    assert field.get_factory() == colander.String
    assert field.validators == [colander.url]


def test_string_format():
    field = String.from_json({
        "type": "string",
        "format": "email"
    }, required=True, name='test')
    assert field.get_factory() == colander.String


def test_email_format():
    field = String.from_json({
        "type": "string",
        "format": "email"
    }, required=True, name='test')
    assert field.get_factory() == colander.String


def test_date_format():
    field = String.from_json({
        "type": "string",
        "format": "date"
    }, name='test', required=True)
    assert field.get_factory() == colander.Date


def test_time_format():
    field = String.from_json({
        "type": "string",
        "format": "time"
    }, name='test', required=True)
    assert field.get_factory() == colander.Time


def test_datetime_format():
    field = String.from_json({
        "type": "string",
        "format": "date-time"
    }, name='test', required=True)
    assert field.get_factory() == colander.DateTime


def test_uuid_format():
     field = String.from_json({
         "format": "uuid",
         "type": "string"
     }, name='test', required=True)

     schema = field()
     schema.deserialize('3e4666bf-d5e5-4aa7-b8ce-cefe41c7568a')

     with pytest.raises(colander.Invalid) as exc:
         schema.deserialize('test')


def test_length():
    field = String.from_json({
        "type": "string",
        "minLength": 1,
        "maxLength": 5
    }, name='test', required=True)

    constraints = field.get_options()
    hamcrest.assert_that(constraints, hamcrest.has_entries({
        'validator': hamcrest.instance_of(colander.Length)
    }))

    assert field.required is True
    assert field.get_factory() == colander.String

    schema = field()
    schema.deserialize('admin')

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize('administrator')
    assert exc.value.asdict() == {'test': 'Longer than maximum length 5'}


def test_pattern():
    field = String.from_json({
        "type": "string",
        "pattern": "^The",
        "default": "The "
    }, name='test', required=True)

    constraints = field.get_options()
    hamcrest.assert_that(constraints, hamcrest.has_entries({
        'validator': hamcrest.instance_of(colander.Regex)
    }))

    assert field.required is True
    assert field.attributes['default']
    assert field.get_factory() == colander.String

    schema = field()
    schema.deserialize('The dagger')

    with pytest.raises(colander.Invalid) as exc:
        schema.deserialize('Dagger')
    assert exc.value.asdict() == {
        'test': 'String does not match expected pattern'
    }


def test_enum():
    field = String.from_json({
        "type": "string",
        "enum": ['foo', 'bar']
    }, name='test', required=True)

    assert field.required is True
    assert field.get_factory() == colander.String

    schema = field()
    schema.deserialize('Dagger')
    schema.deserialize('foo')


def test_unhandled_attribute():
    with pytest.raises(NotImplementedError) as exc:
        String.from_json({
            "type": "string",
            "unknown": ['foo', 'bar'],
            "pattern": "^f"
        }, name='test', required=True)

    assert str(exc.value) == (
        "Unsupported attributes: {'unknown'} for "
        "<class 'jsonschema_colander.types.String'>."
    )
