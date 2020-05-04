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
        self.assertEqual(validator(123), 123)
        self.assertEqual(validator(-45), -45)
        self.assertEqual(validator(1.1), 1)
        with self.assertRaises(ValidationError) as ctx:
            validator('text')
        self.assertEqual(ctx.exception.message, 'Ensure max_delay is an integer number.')

    def test_min_value(self):
        validator = validators.IntegerValidator(name='max_delay', min_value=2)
        self.assertEqual(validator(2), 2)
        with self.assertRaises(ValidationError) as ctx:
            validator(1)
        self.assertEqual(ctx.exception.message, 'Ensure max_delay is greater than or equal to 2')

    def test_max_value(self):
        validator = validators.IntegerValidator(name='max_delay', max_value=2)
        self.assertEqual(validator(2), Decimal('2'))
        with self.assertRaises(ValidationError) as ctx:
            validator(3)
        self.assertEqual(ctx.exception.message, 'Ensure max_delay is less than or equal to 2')


class DecimalValidatorTest(unittest.TestCase):
    def test_simple(self):
        validator = validators.DecimalValidator(name='delay')
        self.assertEqual(validator(0), Decimal('0'))
        self.assertEqual(validator(0.1), Decimal('0.1'))
        self.assertEqual(validator(1), Decimal('1'))
        self.assertEqual(validator(1.2), Decimal('1.2'))
        self.assertEqual(validator(-1.2), Decimal('-1.2'))
        self.assertEqual(validator('0'), Decimal('0'))
        self.assertEqual(validator('0.1'), Decimal('0.1'))
        self.assertEqual(validator('1'), Decimal('1'))
        self.assertEqual(validator('1.2'), Decimal('1.2'))
        self.assertEqual(validator('-1.2'), Decimal('-1.2'))
        with self.assertRaises(ValidationError) as ctx:
            validator('text')
        self.assertEqual(ctx.exception.message, 'Ensure delay is a number.')

    def test_precision(self):
        validator = validators.DecimalValidator(name='delay', precision=2)
        self.assertEqual(validator(1.2), Decimal('1.2'))
        self.assertEqual(validator(1.23), Decimal('1.23'))
        self.assertEqual(validator(1.234), Decimal('1.23'))

    def test_min_value(self):
        validator = validators.DecimalValidator(name='delay', min_value=2)
        self.assertEqual(validator(2), Decimal('2'))
        with self.assertRaises(ValidationError) as ctx:
            validator(1.99)
        self.assertEqual(ctx.exception.message, 'Ensure delay is greater than or equal to 2')

    def test_max_value(self):
        validator = validators.DecimalValidator(name='delay', max_value=2)
        self.assertEqual(validator(2), Decimal('2'))
        with self.assertRaises(ValidationError) as ctx:
            validator(2.01)
        self.assertEqual(ctx.exception.message, 'Ensure delay is less than or equal to 2')
