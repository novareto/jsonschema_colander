import abc
import colander
from typing import List, Dict, Type, ClassVar, Tuple, Optional, Callable


class JSONField(abc.ABC):
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
        """Returns the colander type needed for the schema node.
        """

    def get_widget(self, factory, options):
        return None

    def __call__(self):
        factory = self.get_factory()
        options = self.get_options()
        widget = self.get_widget(factory, options)
        return colander.SchemaNode(factory(), widget=widget, **options)

    @classmethod
    def extract(cls, params: dict, available: set) -> Tuple[List, Dict]:
        return [], {}

    @classmethod
    def from_json(cls, params: dict,
                  name: Optional[str] = None, required: bool = False):
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
