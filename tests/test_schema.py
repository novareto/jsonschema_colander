import hamcrest
import colander
import jsonschema_colander.types

"""
We handle object-typed schema.
They can be fields in a form or just a plain form.
They are created just like any other field.
"""


def test_standalone_schema(person_schema):

    schema = jsonschema_colander.types.ObjectParameters.from_json_field(
        None, False, person_schema
    )

    hamcrest.assert_that(schema.fields, hamcrest.has_entries({
        "firstName": hamcrest.instance_of(
            jsonschema_colander.types.StringParameters),
        "lastName": hamcrest.instance_of(
            jsonschema_colander.types.StringParameters),
        "age": hamcrest.instance_of(
            jsonschema_colander.types.NumberParameters),
        "homepage": hamcrest.instance_of(
            jsonschema_colander.types.StringParameters
        )
    }))

    assert schema.fields["firstName"].required is True
    assert schema.fields["lastName"].required is True
    assert schema.fields["age"].required is False


# def test_schema_as_field(person_schema):

#     schema = jsonschema_colander.types.ObjectParameters.from_json_field(
#         'fieldname', True, person_schema
#     )

#     form = wtforms.form.BaseForm({'fieldname': schema})

#     # fields are useable as unbound wtform fields
#     form = wtforms.form.BaseForm(schema.fields)
#     hamcrest.assert_that(form._fields, hamcrest.has_entries({
#         "firstName": hamcrest.instance_of(
#             colander.typess.StringField),
#         "lastName": hamcrest.instance_of(
#             colander.typess.StringField),
#         "age": hamcrest.instance_of(
#             colander.typess.IntegerField),
#     }))
