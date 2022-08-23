import abc
import colander
from typing import List, Dict, Type, ClassVar, Tuple, Optional, Callable


class JSONFieldParameters(abc.ABC):
    supported: ClassVar[set]
    ignore: ClassVar[set] = {
        'name', 'type', 'title', 'description', 'anyOf', 'if', 'then'
    }
    allowed: ClassVar[set] = frozenset(('default',))

    type: str
    name: str
    label: str
    description: str
    validators: List
    attributes: Dict
    required: bool
    factory: Callable = None

    def __init__(self,
                 type: str,
                 name: str,
                 required: bool,
                 validators: List,
                 attributes: Dict,
                 label: str = '',
                 description: str = ''):
        if type not in self.supported:
            raise TypeError(
                f'{self.__class__} does not support the {type} type.')
        self.type = type
        self.name = name
        self.label = label or name
        self.description = description
        self.required = required
        self.validators = validators
        self.attributes = attributes

    def get_options(self):
        options = {
            **self.attributes,
            'name': self.name,
            'title': self.label,
            'description': self.description,
            'missing': self.required and colander.required or colander.drop
       }
        if len(self.validators) > 1:
            options['validator'] = colander.All(*self.validators)
        elif len(self.validators) == 1:
            options['validator'] = self.validators[0]
        return options

    @abc.abstractmethod
    def get_factory(self):
        return self.factory

    def __call__(self):
        factory = self.get_factory()
        options = self.get_options()
        return colander.SchemaNode(factory(), **options)

    @classmethod
    def extract(cls, params: dict, available: set) -> Tuple[List, Dict]:
        return [], {}

    @classmethod
    def from_json_field(cls, name: str, required: bool, params: dict):
        available = set(params.keys())
        if illegal := ((available - cls.ignore) - cls.allowed):
            raise NotImplementedError(
                f'Unsupported attributes: {illegal} for {cls}.')
        validators, attributes = cls.extract(params, available)
        return cls(
            params['type'],
            name,
            required,
            validators,
            attributes,
            label=params.get('title'),
            description=params.get('description')
        )


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
