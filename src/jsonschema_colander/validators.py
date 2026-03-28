import math
import colander


class NumberRange(colander.Range):

    def __init__(self,
                 min=None,
                 max=None,
                 exclusive_min=None,
                 exclusive_max=None,
                 min_err=colander.Range._MIN_ERR,
                 max_err=colander.Range._MAX_ERR):
        self.exclusive_min = exclusive_min
        self.exclusive_max = exclusive_max
        super().__init__(min=min, max=max, min_err=min_err, max_err=max_err)

    def __call__(self, node, value):
        if value is not None and not math.isnan(value):
            if self.min is not None and value < self.min:
                raise colander.Invalid(node, colander._(
                    self.min_err, mapping={
                        'val': value, 'min': self.min
                    }
                ))
            elif self.exclusive_min is not None and \
                 value <= self.exclusive_min:
                raise colander.Invalid(node, colander._(
                    self.min_err, mapping={
                        'val': value, 'min': self.exclusive_min
                    }
                ))
            if self.max is not None and value > self.max:
                raise colander.Invalid(node, colander._(
                    self.max_err, mapping={
                        'val': value, 'max': self.max
                    }
                ))
            elif self.exclusive_max is not None and \
                 value >= self.exclusive_max:
                raise colander.Invalid(node, colander._(
                    self.max_err, mapping={
                        'val': value, 'max': self.exclusive_max
                    }
                ))


class MultipleOf:

    def __init__(self, multiple_of):
        self.multiple_of = multiple_of

    def __call__(self, node, value):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return
        remainder = abs(value % self.multiple_of)
        if remainder > 1e-9 and abs(remainder - self.multiple_of) > 1e-9:
            raise colander.Invalid(
                node,
                f"Wert muss ein Vielfaches von {self.multiple_of} sein",
            )
