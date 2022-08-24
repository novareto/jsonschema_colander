import abc
from .meta import JSONField
from typing import Dict


class Converter:

    converter: Dict[str, JSONField]

    def __init__(self):
        self.converters = {}

    def register(self, type: str):
        def type_registration(converter: JSONField):
            self.converters[type] = converter
            return converter
        return type_registration

    def lookup(self, type: str, defs: dict = None):
        return self.converters[type]


converter = Converter()
