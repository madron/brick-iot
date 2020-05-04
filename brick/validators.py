from decimal import Decimal
from brick.exceptions import ValidationError


class DecimalValidator:
    def __init__(self, name='value', precision=6, min_value=None, max_value=None):
        self.name = name
        self.precision = precision
        if precision > 0:
            self.precision_quantize = Decimal('0.{}'.format('0' * precision))
        else:
            self.precision_quantize = Decimal('0')
        self.min_value = min_value
        self.max_value = max_value

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
        if self.min_value is not None and value < self.min_value:
            msg = 'Ensure {} is greater than or equal to {}'.format(self.name, self.min_value)
            raise ValidationError(msg)
        if self.max_value is not None and value > self.max_value:
            msg = 'Ensure {} is less than or equal to {}'.format(self.name, self.max_value)
            raise ValidationError(msg)
        return value