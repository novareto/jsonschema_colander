import abc
from .meta import JSONFieldParameters
from typing import Dict


class Converter:

    converter: Dict[str, JSONFieldParameters]

    def __init__(self):
        self.converters = {}

    def register(self, type: str):
        def type_registration(converter: JSONFieldParameters):
            self.converters[type] = converter
            return converter
        return type_registration

    def lookup(self, type: str, defs: dict = None):
        return self.converters[type]


converter = Converter()
