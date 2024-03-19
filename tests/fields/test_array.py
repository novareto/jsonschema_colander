import pytest
import colander
from jsonschema_colander.types import Array


def test_array_without_items():

    field = Array.from_json({
        "type": "array",
    }, name='test', required=True)

    with pytest.raises(NotImplementedError) as exc:
        field.get_factory()

    assert str(exc.value) == (
        "Unsupported array type : 'items' attribute required.")


def test_simple_array():

    field = Array.from_json({
        "type": "array",
        "items": {
            "type": "number"
        }
    }, name='test', required=True)

    factory = field.get_factory()
    assert factory == colander.SequenceSchema


def test_array_enum():

    field = Array.from_json({
        "type": "array",
        "enum": [
            "A",
            "B"
        ]
    }, name='test', required=True)

    factory = field.get_factory()
    assert factory == colander.Set


def test_array_length():

    field = Array.from_json({
        "type": "array",
        "minItems": 2,
        "maxItems": 3,
        "items": {
            "type": "number"
        }
    }, name='test', required=True)

    schema = field()
    schema.deserialize([1, 2, 3])

    with pytest.raises(colander.Invalid):
        schema.deserialize([1, 4, 5, 9])


def test_complex_array():

    field = Array.from_json({
        "type": "array",
        "default": [[1]],
        "items": {
            "type": "array",
            "items": {
                "type": "number"
            }
        }
    }, name='test')

    field.get_factory() == 1
    schema = field()
    schema.deserialize()


def test_complex_array_of_objects():

    field = Array.from_json({
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "creation-date": {
                    "type": "string",
                    "format": "date"
                },
                "files": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "binary",
                        "contentMediaType": [
                            ".pdf",
                            ".jpg",
                            ".png"
                        ]
                    }
                }
            }
        }
    }, name='test', required=True)

    factory = field.get_factory()
    assert factory == colander.SequenceSchema
    schema = field()
    schema.deserialize([{
        "creation-date": '2022-08-24',
        "files": []
    }])


def test_files_array():
    field = Array.from_json( {
        "type": "array",
        "items": {
            "type": "string",
            "format": "binary",
            "contentMediaType": [
                "image/gif",
                ".jpg",
                ".png"
            ]
        },
        "title": "Some images."
    }, name='test', required=True)

    schema = field()
    schema.deserialize([])
