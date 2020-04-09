import utime
from brick.app import Application


def main():
    app = Application()
    while True:
        app.start()
        # Wait a little before restarting app
        utime.sleep(5)



if __name__ == '__main__':
    main()
