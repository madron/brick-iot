## Coverage
```sh
coverage run -m unittest && coverage report --skip-covered
coverage html
```

## Install required libraries

```sh
micropip install -p src -r requirements.txt
```

### Mqtt
```sh
export RELEASE=ad8c9f6c0f016222efa29189b872107e5cf797c4
rm -rf src/mqtt_as.py
wget -P src https://raw.githubusercontent.com/peterhinch/micropython-mqtt/$RELEASE/mqtt_as/mqtt_as.py
```

### Picoweb
```sh
export RELEASE=fdabc1f69b42848d94a0b2eecb24190c184766df
rm -rf src/picoweb
mkdir -p src/picoweb
wget -P src/picoweb https://raw.githubusercontent.com/pfalcon/picoweb/$RELEASE/picoweb/__init__.py
wget -P src/picoweb https://raw.githubusercontent.com/pfalcon/picoweb/$RELEASE/picoweb/utils.py
```
