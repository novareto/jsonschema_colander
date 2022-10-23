import pytest
import hamcrest
import colander
from jsonschema_colander.types import String


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


# def test_uri_format():
#     field = String.from_json('test', True, {
#         "minLength": 1,
#         "maxLength": 2083,
#         "format": "uri",
#         "type": "string"
#     })
#     assert field.get_factory() == 1
#     form = wtforms.form.BaseForm({"test": field()})
#     form.process()
#     assert form._fields['test']() == (
#         '<input id="test" maxlength="2083" minlength="1" '
#         'name="test" required type="url" value="">'
#     )


# def test_password_format():
#     field = String.from_json('test', True, {
#         "title": "Password",
#         "type": "string",
#         "writeOnly": True,
#         "format": "password"
#     })
#     assert field.get_factory() == 1
#     form = wtforms.form.BaseForm({"test": field()})
#     form.process()
#     assert form._fields['test']() == (
#         '<input id="test" '
#         'name="test" required type="password" value="">'
#     )


# def test_binary():
#     field = String.from_json('test', True, {
#         "type": "string",
#         "format": "binary",
#         "contentMediaType": [
#             ".pdf",
#             "image/png"
#         ]
#     })
#     assert field.get_factory() == wtforms.fields.simple.FileField
#     form = wtforms.form.BaseForm({"test": field()})
#     assert form._fields['test']() == (
#         '<input accept=".pdf,image/png" id="test" name="test" '
#         'required type="file">'
#     )


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
