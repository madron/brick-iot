import asyncio
import functools
import os
from w1thermsensor import W1ThermSensor as W1ThermSensorSync


class W1ThermSensor(W1ThermSensorSync):
    def __init__(self, loop=None, executor=None, **kwargs):
        self.loop = loop or asyncio.get_event_loop()
        self.executor = executor

    async def setup(self, sensor_type=None, sensor_id=None, offset=0.0, offset_unit=W1ThermSensorSync.DEGREES_C):
        """
            Initializes a W1ThermSensor.
            If the W1ThermSensor base directory is not found it will automatically load
            the needed kernel modules to make this directory available.
            If the expected directory will not be created after some time an exception is raised.

            If no type and no id are given the first found sensor will be taken for this instance.

            :param int sensor_type: the type of the sensor.
            :param string id: the id of the sensor.
            :param float offset: a calibration offset for the temperature sensor readings
                                 in the unit of ``offset_unit``.
            :param offset_unit: the unit in which the offset is provided.

            :raises KernelModuleLoadError: if the w1 therm kernel modules could not
                                           be loaded correctly
            :raises NoSensorFoundError: if the sensor with the given type and/or id
                                        does not exist or is not connected
        """
        if not sensor_type and not sensor_id:  # take first found sensor
            for _ in range(self.RETRY_ATTEMPTS):
                s = await self.get_available_sensors()
                if s:
                    self.type, self.id = s[0].type, s[0].id
                    break
                asyncio.sleep(self.RETRY_DELAY_SECONDS)
            else:
                raise NoSensorFoundError("Could not find any sensor")
        elif not sensor_id:
            s = await self.get_available_sensors([sensor_type])
            if not s:
                sensor_type_name = self.TYPE_NAMES.get(sensor_type, hex(sensor_type))
                error_msg = "Could not find any sensor of type {}".format(
                    sensor_type_name
                )
                raise NoSensorFoundError(error_msg)
            self.type = sensor_type
            self.id = s[0].id
        elif not sensor_type:  # get sensor by id
            sensor = next(
                (s for s in await self.get_available_sensors() if s.id == sensor_id), None
            )
            if not sensor:
                raise NoSensorFoundError(
                    "Could not find sensor with id {}".format(sensor_id)
                )
            self.type = sensor.type
            self.id = sensor.id
        else:
            self.type = sensor_type
            self.id = sensor_id

        # store path to sensor
        self.sensorpath = os.path.join(
            self.BASE_DIRECTORY, self.slave_prefix + self.id, self.SLAVE_FILE
        )

        if not self.exists():
            raise NoSensorFoundError(
                "Could not find sensor of type {} with id {}".format(
                    self.type_name, self.id
                )
            )

        self.set_offset(offset, offset_unit)


    @classmethod
    async def get_available_sensors(cls, types=None, loop=None, executor=None):
        loop = loop or asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            functools.partial(W1ThermSensorSync.get_available_sensors, types=types),
        )

    async def get_temperature(self, **kawargs):
        return await self.loop.run_in_executor(
            self.executor,
            functools.partial(super().get_temperature, **kawargs),
        )
