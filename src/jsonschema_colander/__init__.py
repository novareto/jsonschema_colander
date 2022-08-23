from jsonschema_colander.types import ObjectParameters
from typing import Dict, Iterable, Optional


JSONSchema = Dict


def schema_fields(schema: JSONSchema,
                  include: Optional[Iterable[str]] = None,
                  exclude: Optional[Iterable[str]] = None):
    root = ObjectParameters.from_json_field(
        None, False, schema,
        include=include, exclude=exclude)
    return root.fields
