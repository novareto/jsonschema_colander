import re
import colander
from functools import partial
from typing import Optional, Dict, ClassVar, Type, Iterable
from .meta import JSONField
from .validators import NumberRange
from .converter import converter


string_formats = {
    'date': colander.Date,
    'time': colander.Time,
    'date-time': colander.DateTime,
}


@converter.register('string')
class String(JSONField):

    supported = {'string'}
    allowed = {
        'format', 'pattern', 'enum', 'minLength', 'maxLength',
        'writeOnly', 'default', 'contentMediaType', 'contentEncoding'
    }

    def __init__(self, type, name, required, validators, attributes, **kwargs):
        self.format = attributes.pop('format', 'default')
        super().__init__(
            type, name, required, validators, attributes, **kwargs)

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        return string_formats.get(self.format, colander.String)

    @classmethod
    def extract(cls, params: dict, available: set):
        validators = []
        attributes = {}
        if {'minLength', 'maxLength'} & available:
            validators.append(colander.Length(
                min=params.get('minLength', -1),
                max=params.get('maxLength', -1)
            ))
        if 'default' in available:
            attributes['default'] = params.get('default')
        if 'pattern' in available:
            validators.append(colander.Regex(params['pattern']))
        if 'enum' in available:
            attributes['choices'] = [(v, v) for v in params['enum']]
        if 'format' in available:
            format = attributes['format'] = params['format']
            if format == 'binary':
                if 'contentMediaType' in available:
                    ctype = params['contentMediaType']
                    if isinstance(ctype, (list, tuple, set)):
                        ctype = ','.join(ctype)
                    kw = attributes.get('render_kw', {})
                    kw['accept'] = ctype
                    attributes['render_kw'] = kw

        return validators, attributes


@converter.register('integer')
@converter.register('number')
class Number(JSONField):

    supported = {'integer', 'number'}
    allowed = {
        'enum', 'format',
        'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
        'default'
    }

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        if self.type == 'integer':
            return colander.Integer
        return colander.Float

    @classmethod
    def extract(cls, params: dict, available: set):
        validators = []
        attributes = {}
        if default := params.get('default'):
            attributes['default'] = default
        if {'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum'} \
           & available:
            validators.append(NumberRange(
                min=params.get('minimum', None),
                max=params.get('maximum', None),
                exclusive_min=params.get('exclusiveMinimum', None),
                exclusive_max=params.get('exclusiveMaximum', None)
            ))
        if 'enum' in available:
            attributes['choices'] = [(v, v) for v in params['enum']]
        return validators, attributes


@converter.register('boolean')
class Boolean(JSONField):
    supported = {'boolean'}

    @classmethod
    def extract(cls, params: dict, available: set):
        if 'default' in available:
            return [], {'default': params['default']}
        return [], {}

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        return colander.Boolean


@converter.register('enum')
class EnumParameters(JSONField):
    supported = {'enum'}
    allowed = {'enum'}

    @classmethod
    def extract(cls, params: dict, available: set):
        validators = []
        attributes = {
            'choices': [(v, v) for v in params['enum']]
        }
        if 'default' in available:
            attributes['default'] = params['default']
        return validators, attributes

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        return wtforms.fields.SelectField

    @classmethod
    def from_json(cls, name: str, required: bool, params: dict):
        available = set(params.keys())
        if illegal := ((available - cls.ignore) - cls.allowed):
            raise NotImplementedError(
                f'Unsupported attributes: {illegal} for {cls}.')
        validators, attributes = cls.extract(params, available)
        return cls(
            'enum',
            name,
            required,
            validators,
            attributes,
            label=params.get('title'),
            description=params.get('description')
        )


@converter.register('array')
class Array(JSONField):

    supported = {'array'}
    allowed = {
        'enum', 'items', 'minItems', 'maxItems', 'default', 'definitions'
    }
    subfield: Optional[JSONField] = None

    def __init__(self, *args, subfield=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.subfield = subfield

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        elif self.subfield is None:
            raise NotImplementedError(
                "Unsupported array type : 'items' attribute required.")
        if 'choices' in self.attributes:
            return colander.Set
        return colander.SequenceSchema

    def __call__(self):
        factory = self.get_factory()
        options = self.get_options()
        subfield = self.subfield()
        if not subfield.name:
            subfield.name = 'item'
        return factory(subfield, **options)

    @classmethod
    def extract(cls, params: dict, available: set):
        attributes = {}
        validators = []
        if {'minItems', 'maxItems'} & available:
            validators.append(colander.Length(
                min=params.get('minItems', -1),
                max=params.get('maxItems', -1)
            ))
        if 'default' in available:
            attributes['default'] = params['default']
        return validators, attributes

    @classmethod
    def from_json(cls, params: dict,
                  name: Optional[str] = None, required: bool = False):
        available = set(params.keys())
        if illegal := ((available - cls.ignore) - cls.allowed):
            raise NotImplementedError(
                f'Unsupported attributes for array type: {illegal}')

        validators, attributes = cls.extract(params, available)
        if 'items' in available and (items := params['items']):
            if ref := items.get('$ref'):
                definitions = params.get('definitions')
                if not definitions:
                    raise NotImplementedError('Missing definitions.')
                items = definitions[ref.split('/')[-1]]

            if 'enum' in items:
                subtype = 'enum'
            else:
                subtype = items['type']

            subfield = converter.lookup(items['type']).from_json(
                items, required=False
            )
        else:
            subfield = None
        return cls(
            params['type'],
            name,
            required,
            validators,
            attributes,
            subfield=subfield,
            label=params.get('title'),
            description=params.get('description')
        )


@converter.register('object')
class Object(JSONField):

    ignore = JSONField.ignore | {
        '$id', 'id', '$schema', '$comment'
    }
    supported = {'object'}
    allowed = {'required', 'properties', 'definitions'}
    fields: Dict[str, JSONField]

    def __init__(self, fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = fields

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        return colander.Schema

    def get_options(self):
        # Object-types do not need root validators.
        # Validation is handled at field level.
        return self.attributes

    def __call__(self):
        options = self.get_options()
        factory = self.get_factory()
        return factory(
            *[subfield() for subfield in self.fields.values()],
            **options
        )

    @classmethod
    def from_json(
            cls, params: dict,
            name: Optional[str] = None,
            required: bool = False,
            include: Optional[Iterable] = None,
            exclude: Optional[Iterable] = None
    ):
        available = set(params.keys())
        if illegal := ((available - cls.ignore) - cls.allowed):
            raise NotImplementedError(
                f'Unsupported attributes for string type: {illegal}')

        properties = params.get('properties', None)
        if properties is None:
            raise NotImplementedError(f"{name}: missing properties.")

        if include is None:
            include = set(properties.keys())
        else:
            include = set(include)  # idempotent
        if exclude is not None:
            include = include - set(exclude)

        requirements = params.get('required', [])
        fields = {}
        definitions = params.get('definitions', {})
        for property_name, definition in properties.items():
            if property_name not in include:
                continue
            if ref := definition.get('$ref'):
                if not definitions:
                    raise NotImplementedError('Missing definitions.')
                definition = definitions[ref.split('/')[-1]]
            if type_ := definition.get('type', None):
                field = converter.lookup(type_)
                if 'definitions' in field.allowed:
                    definition['definitions'] = definitions
                fields[property_name] = field.from_json(
                    definition,
                    name=property_name,
                    required=property_name in requirements
                )
            else:
                raise NotImplementedError(
                    f'Undefined type for property {property_name}'
                )
        validators, attributes = cls.extract(params, available)
        if validators:
            raise NotImplementedError(
                "Object-types can't have root validators")
        return cls(
            fields,
            params['type'],
            name,
            required,
            validators,
            attributes,
            label=params.get('title'),
            description=params.get('description')
        )
