
class Boolean:

    def __init__(self, name):
        self.name = name

    def __bool__(self):
        return self.name


if __name__ == '__main__':

    A = Boolean('A')
    print(A)