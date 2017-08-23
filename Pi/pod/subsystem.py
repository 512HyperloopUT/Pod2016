class TestSubsystem:
    def __init__(self, podinput):
        self.podinput = podinput
        self.printed = False

    def run(self):
        if self.podinput.duration > 2 and not self.printed:
            self.printed = True
            print("hi there")


class PublishSubsystem:
    def __init__(self, podinput):
        self.podinput = podinput

    def run(self):
        # publish sensor data to UDP
        pass
