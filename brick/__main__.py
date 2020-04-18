import time
from brick.app import Application


def main():
    app = Application()
    while True:
        app.start()
        # Wait a little before restarting app
        time.sleep(5)
        print('Restarting app')


if __name__ == '__main__':
    main()
