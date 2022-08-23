import pytest
import colander
from jsonschema_colander.types import ArrayParameters


def test_array_without_items():

    field = ArrayParameters.from_json_field('test', True, {
        "type": "array",
    })

    with pytest.raises(NotImplementedError) as exc:
        field.get_factory()

    assert str(exc.value) == (
        "Unsupported array type : 'items' attribute required.")


def test_simple_array():

    field = ArrayParameters.from_json_field('test', True, {
        "type": "array",
        "items": {
            "type": "number"
        }
    })

    factory = field.get_factory()
    assert factory == colander.SequenceSchema


def test_array_length():

    field = ArrayParameters.from_json_field('test', True, {
        "type": "array",
        "minItems": 2,
        "maxItems": 3,
        "items": {
            "type": "number"
        }
    })

    schema = field()
    schema.deserialize([1, 2, 3])

    with pytest.raises(colander.Invalid):
        schema.deserialize([1, 4, 5, 9])


def test_complex_array():

    field = ArrayParameters.from_json_field('test', False, {
        "type": "array",
        "default": [[1]],
        "items": {
            "type": "array",
            "items": {
                "type": "number"
            }
        }
    })

    field.get_factory() == 1
    schema = field()
    schema.deserialize()


def test_complex_array_of_objects():

    field = ArrayParameters.from_json_field('test', True, {
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
    })

    factory = field.get_factory()
    assert factory == colander.SequenceSchema
    schema = field()
    schema.deserialize([{
        "creation-date": '2022-08-24',
        "files": []
    }])


def test_files_array():
    field = ArrayParameters.from_json_field('test', True, {
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
    })

    schema = field()
    schema.deserialize([])
