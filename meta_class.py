

class Model:

    Entity_Pointer = {}
    Model_Characteristics = set()
    Reactions = set()

    @classmethod
    def check_existing_characteristic(cls, characteristic):
        if characteristic in cls.Model_Characteristics:
            raise TypeError('Characteristics must be unique. It can only belong to one property')
        else:
            cls.Model_Characteristics.add(characteristic)


class Reactions:

    def __init__(self, reactants, products):
        self.reactants = reactants
        self.products = products

        # For compiling purposes
        self.rate = None
        Model.Reactions.add(self)

    def __getitem__(self, rate):
        if type(rate) == float or type(rate) == int:
            self.rate = rate


class Reactants:

    def __init__(self, object_reference, characteristics, stochiometry=1):
        self.list_of_reactants = [(object_reference, characteristics, stochiometry)]

    def __add__(self, other):
        self.list_of_reactants = self.list_of_reactants + other.list_of_reactants
        return self

    def __rshift__(self, other):

        if isinstance(other, Entity):
            p = Reactants(other, '')
        else:
            p = other

        reaction = Reactions(self.list_of_reactants, p.list_of_reactants)
        Model.Reactions.add(reaction)
        return reaction

class Entity:

    entity_counter = 0

    def __rmul__(self, other):
        r = Reactants(self, '', int(other))

    def __add__(self, other):
        r1 = Reactants(self, '')
        if isinstance(other, Reactants):
            r2 = other
        else:
            r2 = Reactants(self, '')
        return r1 + r2

    def __radd__(self, other):
        Entity.__add__(self, other)

    def __getattr__(self, item):
        characteristics = item.split('_')

        for characteristic in characteristics:
            if characteristic not in self._characteristics:
                Model.check_existing_characteristic(characteristic)
                self._characteristics.add(characteristic)

        return Reactants(self, characteristics)

    def __init__(self, name):
        self._name = name
        self._characteristics = set()
        self._entity_references = set()
        Model.Entity_Pointer[name] = self


# Property Call to return several properties as called
def Propertie(number_of_properties=1):

    global entity_counter

    to_return = []
    for i in range(number_of_properties):
        Entity.entity_counter += 1
        name = 'P' + str(Entity.entity_counter)

        to_return.append(Entity(name))

    if number_of_properties == 1:
        return to_return[0]
    else:
        return tuple(to_return)


if __name__ == '__main__':

    A, B, C = Propertie(3)
    A + B >> C
    print(Model.Reactions)

