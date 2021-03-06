import unittest
from decimal import Decimal
from brick import validators
from brick.exceptions import ValidationError


class BooleanValidatorTest(unittest.TestCase):
    def test_simple(self):
        validator = validators.BooleanValidator(name='config_mode')
        self.assertEqual(validator(True), True)
        self.assertEqual(validator('True'), True)
        self.assertEqual(validator('true'), True)
        self.assertEqual(validator('Yes'), True)
        self.assertEqual(validator('yes'), True)
        self.assertEqual(validator(False), False)
        self.assertEqual(validator('False'), False)
        self.assertEqual(validator('false'), False)
        self.assertEqual(validator('No'), False)
        self.assertEqual(validator('no'), False)
        with self.assertRaises(ValidationError) as ctx:
            validator(1)
        self.assertEqual(ctx.exception.message, 'Ensure config_mode is true or false.')
        with self.assertRaises(ValidationError) as ctx:
            validator(1.0)
        self.assertEqual(ctx.exception.message, 'Ensure config_mode is true or false.')
        with self.assertRaises(ValidationError) as ctx:
            validator(None)
        self.assertEqual(ctx.exception.message, 'Ensure config_mode is true or false.')
        with self.assertRaises(ValidationError) as ctx:
            validator('Maybe')
        self.assertEqual(ctx.exception.message, 'Ensure config_mode is true or false.')


class IntegerValidatorTest(unittest.TestCase):
    def test_simple(self):
        validator = validators.IntegerValidator(name='max_delay')
        self.assertEqual(validator(0), 0)
        self.assertEqual(validator(-0), 0)
        self.assertEqual(validator(123), 123)
        self.assertEqual(validator(-45), -45)
        self.assertEqual(validator(1.1), 1)
        self.assertEqual(validator('0'), 0)
        self.assertEqual(validator('-0'), 0)
        self.assertEqual(validator('123'), 123)
        self.assertEqual(validator('-45'), -45)
        with self.assertRaises(ValidationError) as ctx:
            validator('1.1')
        self.assertEqual(ctx.exception.message, 'Ensure max_delay is an integer number.')
        with self.assertRaises(ValidationError) as ctx:
            validator('text')
        self.assertEqual(ctx.exception.message, 'Ensure max_delay is an integer number.')

    def test_min_value(self):
        validator = validators.IntegerValidator(name='max_delay', min_value=2)
        self.assertEqual(validator(2), 2)
        with self.assertRaises(ValidationError) as ctx:
            validator(1)
        self.assertEqual(ctx.exception.message, 'Ensure max_delay is greater than or equal to 2.000000')

    def test_max_value(self):
        validator = validators.IntegerValidator(name='max_delay', max_value=2)
        self.assertEqual(validator(2), Decimal('2'))
        with self.assertRaises(ValidationError) as ctx:
            validator(3)
        self.assertEqual(ctx.exception.message, 'Ensure max_delay is less than or equal to 2.000000')


class DecimalValidatorTest(unittest.TestCase):
    def test_simple(self):
        validator = validators.DecimalValidator(name='delay')
        self.assertEqual(validator(0), Decimal('0'))
        self.assertEqual(validator(-0), Decimal('0'))
        self.assertEqual(validator(0.1), Decimal('0.1'))
        self.assertEqual(validator(1), Decimal('1'))
        self.assertEqual(validator(1.2), Decimal('1.2'))
        self.assertEqual(validator(-1.2), Decimal('-1.2'))
        self.assertEqual(validator('0'), Decimal('0'))
        self.assertEqual(validator('-0'), Decimal('0'))
        self.assertEqual(validator('0.1'), Decimal('0.1'))
        self.assertEqual(validator('1'), Decimal('1'))
        self.assertEqual(validator('1.2'), Decimal('1.2'))
        self.assertEqual(validator('-1.2'), Decimal('-1.2'))
        self.assertEqual(validator(Decimal('0')), Decimal('0'))
        self.assertEqual(validator(Decimal('-0')), Decimal('0'))
        self.assertEqual(validator(Decimal('-0.0000001')), Decimal('0'))
        self.assertEqual(validator(Decimal('-0.000001')), Decimal('-0.000001'))
        self.assertEqual(validator(Decimal('0.1')), Decimal('0.1'))
        self.assertEqual(validator(Decimal('-1.2')), Decimal('-1.2'))
        with self.assertRaises(ValidationError) as ctx:
            validator('text')
        self.assertEqual(ctx.exception.message, 'Ensure delay is a number.')

    def test_precision(self):
        validator = validators.DecimalValidator(name='delay', precision=2)
        self.assertEqual(validator(1.2), Decimal('1.2'))
        self.assertEqual(validator(1.23), Decimal('1.23'))
        self.assertEqual(validator(1.234), Decimal('1.23'))
        validator = validators.DecimalValidator(name='delay', precision=0)
        self.assertEqual(validator(-0.125), Decimal('0'))
        self.assertEqual(validator(Decimal('-0.125')), Decimal('0'))
        self.assertEqual(str(validator(-0.125)),'0')
        self.assertEqual(str(validator('-0.125')),'0')
        self.assertEqual(str(validator(Decimal('-0.125'))),'0')
        self.assertEqual(validator(54321.2), Decimal('54321'))
        self.assertEqual(validator(54321.23), Decimal('54321'))
        self.assertEqual(validator(54321.234), Decimal('54321'))
        validator = validators.DecimalValidator(name='delay', precision=-2)
        self.assertEqual(validator(1550), Decimal('1600'))
        self.assertEqual(validator(54321.2), Decimal('54300'))
        self.assertEqual(validator(54321.23), Decimal('54300'))
        self.assertEqual(validator(54321.234), Decimal('54300'))

    def test_min_value(self):
        validator = validators.DecimalValidator(name='delay', min_value=2)
        self.assertEqual(validator(2), Decimal('2'))
        with self.assertRaises(ValidationError) as ctx:
            validator(1.99)
        self.assertEqual(ctx.exception.message, 'Ensure delay is greater than or equal to 2.000000')
        validator = validators.DecimalValidator(name='delay', min_value=0.2)
        self.assertEqual(validator(0.2), Decimal('0.2'))
        with self.assertRaises(ValidationError) as ctx:
            validator(0.199)
        self.assertEqual(ctx.exception.message, 'Ensure delay is greater than or equal to 0.200000')

    def test_max_value(self):
        validator = validators.DecimalValidator(name='delay', max_value=2)
        self.assertEqual(validator(2), Decimal('2'))
        with self.assertRaises(ValidationError) as ctx:
            validator(2.01)
        self.assertEqual(ctx.exception.message, 'Ensure delay is less than or equal to 2.000000')


class OnOffValidatorTest(unittest.TestCase):
    def test_simple(self):
        validator = validators.OnOffValidator(name='initial')
        self.assertEqual(validator('on'), 'on')
        self.assertEqual(validator('off'), 'off')
        with self.assertRaises(ValidationError) as ctx:
            validator(None)
        self.assertEqual(ctx.exception.message, "Ensure initial is 'on' or 'off'.")
        with self.assertRaises(ValidationError) as ctx:
            validator('offf')
        self.assertEqual(ctx.exception.message, "Ensure initial is 'on' or 'off'.")

    def test_null(self):
        validator = validators.OnOffValidator(name='initial', null=True)
        self.assertEqual(validator('on'), 'on')
        self.assertEqual(validator('off'), 'off')
        self.assertEqual(validator(None), None)
        with self.assertRaises(ValidationError) as ctx:
            validator('offf')
        self.assertEqual(ctx.exception.message, "Ensure initial is 'on' or 'off'.")
