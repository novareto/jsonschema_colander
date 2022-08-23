import pytest
import colander
from jsonschema_colander.types import ObjectParameters


def test_object():

    with pytest.raises(NotImplementedError):
        field = ObjectParameters.from_json_field('test', True, {
            "type": "object",
        })

    field = ObjectParameters.from_json_field('test', True, {
        "type": "object",
        "properties": {
            "fruits": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        }
    })

    factory = field.get_factory()
    assert factory == colander.Schema


def test_ref_object():
    root_field = ObjectParameters.from_json_field('test', True, {
        "type": "object",
        "properties": {
            "name": {
                "title": "Name",
                "type": "string"
            },
            "address": {
                "$ref": "#/definitions/Address"
            },
            "devices": {
                "title": "Devices",
                "type": "array",
                "items": {
                    "$ref": "#/definitions/Device"
                }
            }
        },
        "required": [
            "name",
        ],
        "definitions": {
            "Address": {
                "title": "Address",
                "type": "object",
                "properties": {
                    "street": {
                        "title": "Street",
                        "type": "string"
                    },
                    "city": {
                        "title": "City",
                        "type": "string"
                    },
                    "phone": {
                        "title": "Phone",
                        "type": "string"
                    }
                },
                "required": [
                    "street",
                    "city",
                    "phone"
                ]
            },
            "Device": {
                "title": "Device",
                "type": "object",
                "properties": {
                    "kind": {
                        "title": "Kind",
                        "enum": [
                            "PC",
                            "Laptop"
                        ],
                        "type": "string"
                    }
                },
                "required": [
                    "kind"
                ]
            }
        }
    })
    assert root_field.label == 'test'
    assert not root_field.description
    addr = root_field.fields['address']
    assert addr.label == 'Address'
    assert not addr.required

    schema = addr()
    schema.deserialize({
        'city': 'Boppelsen',
        'phone': '666',
        'street': 'A'
    })

    devices = root_field.fields['devices']
    assert devices.label == 'Devices'
    assert devices.name == 'devices'
    assert not devices.required
