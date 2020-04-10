## Coverage
```sh
coverage run -m unittest && coverage report --skip-covered
coverage html
```

## Install required libraries

### Mqtt
```sh
export REV=ad8c9f6c0f016222efa29189b872107e5cf797c4
wget -P src https://raw.githubusercontent.com/peterhinch/micropython-mqtt/$REV/mqtt_as/mqtt_as.py
```
