import abc
import colander
from functools import cached_property
from types import MappingProxyType
import typing as t

try:
    from deform.schema import default_widget_makers

    READONLY_WIDGET = True
except ImportError:
    default_widget_makers = {}
    READONLY_WIDGET = False


class Path(str):

    fragments: t.Sequence[str]

    def __new__(cls, value: t.Union[str, "Path"]):
        if isinstance(value, Path):
            return value  # idempotency
        string = super().__new__(cls, value)
        string.fragments = string.split(".")
        return string

    def resolve(self, node: t.Mapping[str, t.Any]) -> t.Any:
        for stub in self.fragments:
            node = node[stub]
        return node

    def missing(self):
        @colander.deferred
        def deferred_missing(node, kw):
            """in order to work, you need to bind the schema with 'data'.
            'data' being the equivalent of the appstruct.
            """
            if data := kw.get("data"):
                try:
                    return self.resolve(data)
                except KeyError:
                    return None

        return deferred_missing

    @classmethod
    def create(cls, parent, name: str):
        if parent is None:
            return cls(name or "")
        if name:
            if parent.__path__:
                return cls(f"{parent.__path__}.{name}")
            return cls(name)
        if parent.__path__:
            return cls(parent.__path__)
        raise NameError("Unnamed field with no parent.")


class DefinitionsHolder:
    definitions: t.Optional[t.Mapping]


class JSONField(abc.ABC):
    supported: t.ClassVar[set]
    ignore: t.ClassVar[set] = {
        "name",
        "type",
        "title",
        "description",
        "anyOf",
        "if",
        "then",
        "dependentSchemas",
        "allOf",
    }
    allowed: t.ClassVar[set] = {"default"}

    type: str
    name: str
    label: str
    description: str
    validators: t.List
    attributes: t.Dict
    required: bool
    readonly: bool
    __path__: str
    parent: t.Optional["JSONField"] = None
    factory: t.Optional[t.Callable] = None
    config: t.Optional[t.Mapping] = None

    def __init__(
        self,
        type: str,
        name: str,
        required: bool,
        validators: t.List,
        attributes: t.Dict,
        *,
        label: str = "",
        description: str = "",
        config: t.Optional[t.Mapping] = None,
        parent: t.Optional["JSONField"] = None,
    ):
        if type not in self.supported:
            raise TypeError(f"{self.__class__} does not support the {type} type.")

        self.__path__ = Path.create(parent, name)

        if config is None:
            config = MappingProxyType({})
        elif not isinstance(config, MappingProxyType):
            config = MappingProxyType(config)

        self.config = config
        self.fieldconf = MappingProxyType(self.config.get(self.__path__, {}))

        self.type = type
        self.name = name
        self.label = label or name
        self.description = description
        self.required = required
        self.readonly = self.fieldconf.get("readonly", False)
        self.validators = validators
        if validators := self.fieldconf.get("validators"):
            self.validators.extend(validators)
        self.attributes = attributes
        self.parent = parent

    def get_definitions(self, node):
        while node is not None:
            if isinstance(node, DefinitionsHolder):
                return node.definitions
        return {}

    def get_options(self):
        if not self.required:
            if self.readonly:
                missing = self.__path__.missing()
            else:
                missing = colander.drop
        else:
            missing = colander.required

        options = {
            **self.attributes,
            "name": self.name,
            "title": self.label,
            "description": self.description,
            "missing": missing,
        }
        if len(self.validators) > 1:
            options["validator"] = colander.All(*self.validators)
        elif len(self.validators) == 1:
            options["validator"] = self.validators[0]
        return options

    @abc.abstractmethod
    def get_factory(self):
        """Returns the colander type needed for the schema node."""
        pass

    def get_widget(self, factory, options):
        if widget := default_widget_makers.get(factory):
            if READONLY_WIDGET:
                return widget(readonly=self.readonly)
            return widget()
        return None

    def __call__(self):
        factory = self.get_factory()
        options = self.get_options()
        widget = self.get_widget(factory, options)
        return colander.SchemaNode(factory(), widget=widget, **options)

    @classmethod
    def extract(cls, params: dict, available: set) -> t.Tuple[t.List, t.Dict]:
        return [], {}

    @classmethod
    def from_json(
        cls,
        params: dict,
        *,
        parent: t.Optional["JSONField"] = None,
        name: t.Optional[str] = None,
        config: t.Optional[dict] = None,
        required: bool = False,
    ):
        available = set(params.keys())
        if illegal := ((available - cls.ignore) - cls.allowed):
            raise NotImplementedError(f"Unsupported attributes: {illegal} for {cls}.")
        validators, attributes = cls.extract(params, available)

        if dependentSchemas := params.get('dependentSchemas'):
            from .validators import JS_Schema_Validator
            validators.append(JS_Schema_Validator('dependentSchemas', dependentSchemas))

        if allOf := params.get('allOf'):
            from .validators import JS_Schema_Validator
            validators.append(JS_Schema_Validator('allOf', allOf))

        return cls(
            params["type"],
            name,
            required,
            validators,
            attributes,
            parent=parent,
            config=config,
            label=params.get("title"),
            description=params.get("description"),
        )
