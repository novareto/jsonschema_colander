import hamcrest
import colander
import jsonschema_colander.types

"""
We handle object-typed schema.
They can be fields in a form or just a plain form.
They are created just like any other field.
"""


def test_standalone_schema(person_schema):

    schema = jsonschema_colander.types.Object.from_json(person_schema)

    hamcrest.assert_that(schema.fields, hamcrest.has_entries({
        "firstName": hamcrest.instance_of(
            jsonschema_colander.types.String),
        "lastName": hamcrest.instance_of(
            jsonschema_colander.types.String),
        "age": hamcrest.instance_of(
            jsonschema_colander.types.Number),
        "homepage": hamcrest.instance_of(
            jsonschema_colander.types.String
        )
    }))

    assert schema.fields["firstName"].required is True
    assert schema.fields["lastName"].required is True
    assert schema.fields["age"].required is False


# def test_schema_as_field(person_schema):

#     schema = jsonschema_colander.types.Object.from_json(
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
