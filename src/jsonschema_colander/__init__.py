from jsonschema_colander.types import Object
from typing import Dict, Iterable, Optional


JSONSchema = Dict


def schema_fields(schema: JSONSchema,
                  include: Optional[Iterable[str]] = None,
                  exclude: Optional[Iterable[str]] = None):
    root = Object.from_json(
        None, False, schema,
        include=include, exclude=exclude)
    return root.fields
