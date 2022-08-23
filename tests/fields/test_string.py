import pytest
import hamcrest
import colander
from jsonschema_colander.types import StringParameters


def test_unknown_format():
    with pytest.raises(NotImplementedError):
        StringParameters.from_json_field('test', True, {
            "type": "string",
            "format": "foobar"
        })


def test_email_format():
    field = StringParameters.from_json_field('test', True, {
        "type": "string",
        "format": "email"
    })
    assert field.get_factory() == colander.String


def test_date_format():
    field = StringParameters.from_json_field('test', True, {
        "type": "string",
        "format": "date"
    })
    assert field.get_factory() == colander.Date


def test_time_format():
    field = StringParameters.from_json_field('test', True, {
        "type": "string",
        "format": "time"
    })
    assert field.get_factory() == colander.Time


def test_datetime_format():
    field = StringParameters.from_json_field('test', True, {
        "type": "string",
        "format": "date-time"
    })
    assert field.get_factory() == colander.DateTime


# def test_uri_format():
#     field = StringParameters.from_json_field('test', True, {
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
#     field = StringParameters.from_json_field('test', True, {
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
#     field = StringParameters.from_json_field('test', True, {
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
    field = StringParameters.from_json_field('test', True, {
        "type": "string",
        "minLength": 1,
        "maxLength": 5
    })

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
    field = StringParameters.from_json_field('test', True, {
        "type": "string",
        "pattern": "^The",
        "default": "The "
    })

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
    field = StringParameters.from_json_field('test', True, {
        "type": "string",
        "enum": ['foo', 'bar']
    })

    # constraints = field.get_options()
    # hamcrest.assert_that(constraints, hamcrest.has_entries({
    #     'validators': hamcrest.contains_exactly(
    #         hamcrest.instance_of(wtforms.validators.DataRequired),
    #     ),
    # }))

    assert field.required is True
    assert field.get_factory() == colander.String

    schema = field()
    schema.deserialize('Dagger')
    schema.deserialize('foo')


def test_unhandled_attribute():
    with pytest.raises(NotImplementedError) as exc:
        StringParameters.from_json_field('test', True, {
            "type": "string",
            "unknown": ['foo', 'bar'],
            "pattern": "^f"
        })

    assert str(exc.value) == (
        "Unsupported attributes: {'unknown'} for "
        "<class 'jsonschema_colander.types.StringParameters'>."
    )
