import network
import ubinascii


def start_networking(mode, config):
    if mode == 'config':
        network_interface = config.get('config_interface', 'hostspot')
        config = config.get(network_interface, dict())
        if network_interface == 'hostspot':
            start_hotspot(config)
        elif network_interface == 'wifi':
            start_wifi(config)


def start_hotspot(config):
    print('Starting hotspot...')
    ssid = config.get('ssid', None)
    password = config.get('password', None)
    if not ssid:
        ssid = 'brick-{}'.format(ubinascii.hexlify(network.WLAN().config('mac'),'').decode())

    ap = network.WLAN(network.AP_IF)
    kwargs = dict(essid=ssid, dhcp_hostname='brick')
    if password:
        kwargs['authmode'] = network.AUTH_WPA2_PSK
        kwargs['password'] = password
    ap.config(**kwargs)
    ap.active(True)

    ip = ap.ifconfig()[0]
    print('Hotspot ip: {}'.format(ip))


def start_wifi(config):
    print('Starting wifi...')
    ssid = config['ssid']
    password = config['password']

    wifi = network.WLAN(network.STA_IF)
    if not wifi.isconnected():
        wifi.active(True)
        wifi.connect(ssid, password)
        while not wifi.isconnected():
            pass

    ip = wifi.ifconfig()[0]
    print('Wifi ip: {}'.format(ip))
