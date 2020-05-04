from decimal import Decimal
from brick.exceptions import ValidationError


class BooleanValidator:
    def __init__(self, name='value'):
        self.name = name

    def __call__(self, value):
        if not isinstance(value, bool):
            value = str(value).lower()
            if value in ['true', 'yes']:
                return True
            elif value in ['false', 'no']:
                return False
            msg = 'Ensure {} is true or false.'.format(self.name)
            raise ValidationError(msg)
        return value


class IntegerValidator:
    def __init__(self, name='value', min_value=None, max_value=None):
        self.name = name
        self.min_value = min_value
        self.max_value = max_value

    def __call__(self, value):
        if not isinstance(value, int):
            try:
                value = int(value)
            except ValueError:
                msg = 'Ensure {} is an integer number.'.format(self.name)
                raise ValidationError(msg)
            if value == 0:
                value = abs(value)
        self.check_min_value(value)
        self.check_max_value(value)
        return value

    def check_min_value(self, value):
        if self.min_value is not None and value < self.min_value:
            msg = 'Ensure {} is greater than or equal to {}'.format(self.name, self.min_value)
            raise ValidationError(msg)

    def check_max_value(self, value):
        if self.max_value is not None and value > self.max_value:
            msg = 'Ensure {} is less than or equal to {}'.format(self.name, self.max_value)
            raise ValidationError(msg)


class DecimalValidator(IntegerValidator):
    def __init__(self, name='value', precision=6, min_value=None, max_value=None):
        super().__init__(name=name, min_value=min_value, max_value=max_value)
        self.precision = precision
        if precision > 0:
            self.precision_quantize = Decimal('0.{}'.format('0' * precision))
        else:
            self.precision_quantize = Decimal('0')

    def __call__(self, value):
        if isinstance(value, Decimal):
            value = value.quantize(self.precision_quantize)
        else:
            try:
                value = round(float(value), self.precision)
            except ValueError:
                msg = 'Ensure {} is a number.'.format(self.name)
                raise ValidationError(msg)
            if value == 0:
                value = abs(value)
            value =  Decimal(value).quantize(self.precision_quantize)
        self.check_min_value(value)
        self.check_max_value(value)
        return value