
class Entity:

    def __getattribute__(self, *args):
        for arg in args:
            print(arg)

    def __init__(self, name, entity=True):
        self._name = name


A = Entity('A')
