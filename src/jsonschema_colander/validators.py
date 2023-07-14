import math
import colander
from jsonschema import validate, ValidationError


class NumberRange(colander.Range):
    def __init__(
        self,
        min=None,
        max=None,
        exclusive_min=None,
        exclusive_max=None,
        min_err=colander.Range._MIN_ERR,
        max_err=colander.Range._MAX_ERR,
    ):
        self.exclusive_min = exclusive_min
        self.exclusive_max = exclusive_max
        super().__init__(min=min, max=max, min_err=min_err, max_err=max_err)

    def __call__(self, node, value):
        if value is not None and not math.isnan(value):
            if self.min is not None and value < self.min:
                raise colander.Invalid(
                    node,
                    colander._(self.min_err, mapping={"val": value, "min": self.min}),
                )
            elif self.exclusive_min is not None and value <= self.exclusive_min:
                raise colander.Invalid(
                    node,
                    colander._(
                        self.min_err, mapping={"val": value, "min": self.exclusive_min}
                    ),
                )
            if self.max is not None and value > self.max:
                raise colander.Invalid(
                    node,
                    colander._(self.max_err, mapping={"val": value, "max": self.max}),
                )
            elif self.exclusive_max is not None and value >= self.exclusive_max:
                raise colander.Invalid(
                    node,
                    colander._(
                        self.max_err, mapping={"val": value, "max": self.exclusive_max}
                    ),
                )


def node_json_traverser(node, stack):
    if not stack:
        return node
    if children := getattr(node, 'children', None):
        name, stack = stack[0], stack[1:]
        if isinstance(name, str):
            for child in children:
                if child.name == name:
                    return node_json_traverser(child, stack)
        elif isinstance(name, int):
            assert len(children) == 1
            items = children[0]
            assert items.name == 'items'
            if not stack:
                return node
            return node_json_traverser(items, stack)

    raise LookupError('Node not found')


def node_json_error(error, node, stack):
    if not stack:
        return error
    if children := getattr(node, 'children', None):
        name, stack = stack[0], stack[1:]
        if isinstance(name, str):
            for num, child in enumerate(children):
                if child.name == name:
                    suberror = colander.Invalid(child)
                    error.add(suberror, num)
                    return node_json_error(suberror, child, stack)
        elif isinstance(name, int):
            assert len(children) == 1
            items = children[0]
            assert items.name == 'items'
            if not stack:
                return error
            return node_json_error(error, items, stack)

    raise LookupError('Node not found')



class JS_Schema_Validator:

    def __init__(self, key, jsonschema):
        self.jsonschema = {"type": "object", key: jsonschema}

    def __call__(self, node, value, **kwargs):
        """Prevent duplicate usernames."""
        try:
            validate(value, self.jsonschema)
        except ValidationError as e:
            base_error = colander.Invalid(node)
            error = node_json_error(base_error, node, list(e.path))
            error.msg = e.message
            raise base_error
