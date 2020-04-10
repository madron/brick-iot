## Coverage
coverage run -m unittest && coverage report --skip-covered
coverage html


## Install required libraries
wget -O src/mqtt_as.py https://raw.githubusercontent.com/peterhinch/micropython-mqtt/ad8c9f6c0f016222efa29189b872107e5cf797c4/mqtt_as/mqtt_as.py
