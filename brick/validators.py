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


def get_precision_quantize(precision):
        if precision > 0:
            return Decimal('0.{}'.format('0' * precision))
        else:
            return Decimal('0')


class IntegerValidator:
    def __init__(self, name='value', min_value=None, max_value=None):
        self.name = name
        precision_quantize = get_precision_quantize(6)
        self.min_value = min_value
        if self.min_value:
            self.min_value = Decimal(min_value).quantize(precision_quantize)
        self.max_value = max_value
        if self.max_value:
            self.max_value = Decimal(max_value).quantize(precision_quantize)

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
        self.precision_quantize = get_precision_quantize(precision)

    def __call__(self, value):
        if isinstance(value, Decimal):
            value = value.quantize(self.precision_quantize)
        else:
            try:
                value = round(float(value), self.precision)
            except ValueError:
                msg = 'Ensure {} is a number.'.format(self.name)
                raise ValidationError(msg)
            value =  Decimal(value).quantize(self.precision_quantize)
        self.check_min_value(value)
        self.check_max_value(value)
        if value == 0:
            value = abs(value)
        return value


class OnOffValidator:
    def __init__(self, name='value', null=False):
        self.name = name
        self.null = null

    def __call__(self, value):
        if self.null and value is None:
            return None
        if value == 'on' or value is True:
            return 'on'
        if value == 'off' or value is False:
            return 'off'
        msg = "Ensure {} is 'on' or 'off'.".format(self.name)
        raise ValidationError(msg)
