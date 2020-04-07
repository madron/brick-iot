from umqtt.robust import MQTTClient


def get_mqtt_client(name='brick', config=dict()):
    return MQTTClient(
        client_id=config.get('client_id', name),
        server=config.get('host', 'localhost'),
        port=config.get('port', 1883),
        user=config.get('username', None),
        password=config.get('password', None),
        keepalive=config.get('keepalive', 5),
        ssl=config.get('ssl', False),
        ssl_params=config.get('ssl_params', dict()),
    )
