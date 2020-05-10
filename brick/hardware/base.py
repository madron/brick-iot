from brick.exceptions import ValidationError


class DigitalInput:
    def __init__(self, device=None, name='', delay=200):
        self.device = device
        self.name = name
        self.delay = delay

    async def setup(self):
        pass

    async def is_pressed(self):
        state = await self.get_state()
        return True if state == 'on' else False

    async def get_state(self):
        raise NotImplementedError()


class DigitalOutput:
    def __init__(self, device=None, contact='no', name=''):
        self.device = device
        self.name = name
        self.delay = 0
        self.contact = self.validate_contact(contact)

    def validate_contact(self, contact):
        if contact is False:
            contact = 'no'
        if contact not in ('no', 'nc'):
            msg = "contact '{}' not supported. Choices: 'no' (normally open) or 'nc' (normally closed)".format(contact)
            raise ValidationError(msg)
        return contact

    def get_contact_value(self, value):
        if self.contact == 'no':
            return value
        else:
            return 'on' if value == 'off' else 'off'

    async def setup(self):
        pass

    async def on(self):
        await self.set_state('on')

    async def off(self):
        await self.set_state('off')

    async def get_state(self):
        raise NotImplementedError()

    async def set_state(self, state):
        raise NotImplementedError()
