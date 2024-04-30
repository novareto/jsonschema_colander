import re
import colander
from functools import partial
from typing import Optional, Dict, ClassVar, Type, Iterable, Mapping
from .meta import JSONField, DefinitionsHolder, READONLY_WIDGET
from .validators import NumberRange
from .converter import converter


try:
    import deform.widget
    string_widgets = {
        "password": deform.widget.PasswordWidget,
        "textarea": deform.widget.TextAreaWidget
    }
    enum_widgets = {
        colander.String: deform.widget.SelectWidget,
        colander.Set: deform.widget.CheckboxChoiceWidget,
    }
except ImportError:
    string_widgets = {}
    enum_widgets = {}


@converter.register('string')
class String(JSONField):

    supported = {'string'}
    allowed = {
        'format', 'pattern', 'enum', 'minLength', 'maxLength',
        'writeOnly', 'default', 'contentMediaType', 'contentEncoding'
    }

    formats = {
        'date': colander.Date,
        'time': colander.Time,
        'date-time': colander.DateTime,
    }

    validators = {
        'email': [colander.Email()],
        'uuid': [colander.uuid],
        'url':  [colander.url]  # non-standard
    }

    widgets = string_widgets

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.format = self.attributes.pop('format', 'default')

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        return self.formats.get(self.format, colander.String)

    def get_widget(self, factory, options):
        """Format superseedes classical node widget.
        """
        if 'choices' in self.attributes:
            if widget := enum_widgets.get(factory):
                if isinstance(widget, colander.deferred):
                    return widget
                return widget(
                    values=self.attributes['choices'],
                    readonly=self.readonly
                )
        elif widget := self.widgets.get(self.format):
            if isinstance(widget, colander.deferred):
                return widget
            if READONLY_WIDGET:
                return widget(readonly=self.readonly)
            return widget()
        return super().get_widget(factory, options)

    @classmethod
    def extract(cls, params: Mapping, available: set):
        validators = []
        attributes = {}
        if {'minLength', 'maxLength'} & available:
            validators.append(colander.Length(
                min=params.get('minLength', -1),
                max=params.get('maxLength', -1)
            ))
            attributes['min_len'] = params.get('minLength', 0)
            if 'maxLength' in params:
                attributes['max_len'] = params.get['maxLength']

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
            elif format_validators := cls.validators.get(format):
                validators.extend(format_validators)
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
    def extract(cls, params: Mapping, available: set):
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
    def extract(cls, params: Mapping, available: set):
        if 'default' in available:
            return [], {'default': params['default']}
        return [], {}

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        return colander.Boolean


@converter.register('array')
class Array(JSONField):

    supported = {'array'}
    allowed = {
        'items', 'minItems', 'maxItems', 'default', 'definitions'
    }
    subfield: Optional[JSONField] = None

    def __init__(self, *args, subfield=None, **kwargs):
        self.subfield = subfield
        super().__init__(*args, **kwargs)

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        elif self.subfield is None:
            if 'choices' in self.attributes:
                return colander.Set
            raise NotImplementedError(
                "Unsupported array type : 'items' attribute required.")
        return colander.SequenceSchema

    def get_widget(self, factory, options):
        if 'choices' in self.attributes:
            if widget := enum_widgets.get(factory):
                if isinstance(widget, colander.deferred):
                    return widget
                return widget(
                    values=self.attributes['choices'],
                    readonly=self.readonly
                )
        return super().get_widget(factory, options)

    def __call__(self):
        factory = self.get_factory()
        options = self.get_options()
        if self.subfield is not None:
            subfield = self.subfield()
            if not subfield.name:
                subfield.name = 'item'
            return factory(subfield, **options)
        widget = self.get_widget(factory, options)
        return colander.SchemaNode(factory(), widget=widget, **options)

    @classmethod
    def extract(cls, params: Mapping, available: set):
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

    def set_items(self, items):
        if not items:
            self.subfield = None
            return

        if ref := items.get('$ref'):
            definitions = self.get_definitions(self.parent)
            if not definitions:
                raise NotImplementedError('Missing definitions.')
            items = definitions[ref.split('/')[-1]]

        if 'enum' in items:
            self.attributes['choices'] = [(v, v) for v in items['enum']]
        else:
            subtype = items['type']
            self.subfield = converter.lookup(subtype).from_json(
                items,
                name='items',
                required=False,
                parent=self.parent,
                config=self.config
            )

    @classmethod
    def from_json(cls, params: Mapping, **kwargs):
        node = super().from_json(params, **kwargs)
        inherited = node.get_definitions(node.parent)
        node.set_items(params.get('items'))
        return node


@converter.register('object')
class Object(JSONField, DefinitionsHolder):

    ignore = JSONField.ignore | {
        '$id', 'id', '$schema', '$comment'
    }
    supported = {'object'}
    allowed = {'required', 'properties', 'definitions'}

    fields: Optional[Dict[str, JSONField]] = None
    definitions: Optional[Dict] = None

    def get_factory(self):
        if self.factory is not None:
            return self.factory
        return colander.Schema

    def __call__(self, **kwargs):
        options = self.get_options()
        factory = self.get_factory()
        return factory(
            *[subfield() for subfield in self.fields.values()],
            **(options | kwargs)
        )

    def set_fields(self, properties, requirements):
        fields = {}
        if includes := self.fieldconf.get('include'):
            include = set(includes)
        else:
            include = set(properties.keys())
        if exclude := self.fieldconf.get('exclude'):
            include = include - set(exclude)
        for property_name, definition in properties.items():
            if property_name not in include:
                continue
            if ref := definition.get('$ref'):
                if not self.definitions:
                    raise NotImplementedError('Missing definitions.')
                definition = self.definitions[ref.split('/')[-1]]
            if type_ := definition.get('type', None):
                field = converter.lookup(type_)
                fields[property_name] = field.from_json(
                    definition,
                    name=property_name,
                    required=property_name in requirements,
                    parent=self,
                    config=self.config,
                )
            else:
                raise NotImplementedError(
                    f'Undefined type for property {property_name}'
                )
        self.fields = fields

    @classmethod
    def from_json(cls, params: Mapping, **kwargs):
        node = super().from_json(params, **kwargs)
        inherited = node.get_definitions(node.parent)
        node.definitions = inherited | params.get('definitions', {})
        node.set_fields(
            params.get('properties', {}),
            params.get('required', []),
        )
        return node
