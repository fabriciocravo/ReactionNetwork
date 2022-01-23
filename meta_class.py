import copy

import meta_class_utils
from order_operators import *
from function_rate_code import *
import reaction_construction_nb
import function_rate_code
import itertools


# Easter Egg: I finished the first version on a sunday at the BnF in Paris
# If anyone is reading this, I highly recommend you study there, it is quite a nice place
class Simulator:
    """
        This is the simulator call
        It receives the constructed objects and keeps track of the number of 
    """
    
    # Basic storage of defined variables for Simulator
    Entity_counter = 0
    Reactions_set = set()
    Species_string_dict = {}
    Ref_object_to_characteristics = {}
    Ref_characteristics_to_object = {}
    Last_rate = None

    @classmethod
    def override_get_item(cls, object_to_return, item):
        cls.Last_rate = item
        return object_to_return

    @classmethod
    def name_all_involved_species(cls, list_of_species_objects):
        for species in list_of_species_objects:
            variable_name = [k for k, v in globals().items() if v == species][0]
            species.name(variable_name)

    @classmethod
    def compile(cls, species_to_simulate, type_of_model):
        # TODO no events for now
        # If there is only a single species
        if isinstance(species_to_simulate, Species):
            list_of_species_objects = [species_to_simulate]
        elif isinstance(species_to_simulate, ParallelSpecies):
            list_of_species_objects = species_to_simulate.list_of_species
        else:
            raise TypeError('Wrong input type')

        """
            Here we construct the species for Copasi using their objects
            
            First we extract all the species from all the given objects and add them to a set
            and for the species dictionary for the Simulator
            
            And construct the Species_from_characteristic dictionary 
            This dictionary returns the species with an specific characteristic using it's key
            
            Also we construct the Species_from_object dictionary
            This dictionary returns the species from an specific object using the object as key
        """

        # We name the species according to variables names for convenience
        cls.name_all_involved_species(list_of_species_objects)

        # Perform checks
        meta_class_utils.add_negative_complement_to_characteristics(list_of_species_objects)

        # Construct structures necessary for reactions
        cls.Ref_object_to_characteristics, cls.Ref_characteristics_to_object = \
            meta_class_utils.create_orthogonal_vector_structure(list_of_species_objects)

        # Start by creating the Mappings for the SBML
        Mappings_for_SBML = {}
        for spe_object in list_of_species_objects:
            Mappings_for_SBML[spe_object.get_name()] = []

        # List of Species objects
        for spe_object in list_of_species_objects:
            list_of_definitions = []
            for reference in spe_object.get_references():
                list_of_definitions.append(reference.get_characteristics())
            cls.Species_string_dict[spe_object] = meta_class_utils.create_species_strings(spe_object,
                                                                                          list_of_definitions)
        # Set of reactions involved
        for spe_object in list_of_species_objects:
            for reference in spe_object.get_references():
                cls.Reactions_set = cls.Reactions_set.union(reference.get_reactions())

        # Setting Species for SBML and their initial values
        Species_for_SBML = {}
        for spe_object in list_of_species_objects:
            for species_string in cls.Species_string_dict[spe_object]:
                Species_for_SBML[species_string] = 0

        # Create the mappings for sbml
        for spe_object in list_of_species_objects:
            for species_string in cls.Species_string_dict[spe_object]:
                Mappings_for_SBML[spe_object.get_name()].append(species_string)

        # Set initial counts for SBML
        for spe_object in list_of_species_objects:
            for count in spe_object.get_quantities():

                if count['quantity'] == 0:
                    continue

                count_set = \
                    meta_class_utils.complete_characteristics_with_first_values(spe_object,
                                                                                count['characteristics'],
                                                                                cls.Ref_characteristics_to_object)

                for species_string in Species_for_SBML.keys():
                    species_set = meta_class_utils.extract_characteristics_from_string(species_string)
                    if species_set == count_set:
                        Species_for_SBML[species_string] = count['quantity']
                        break

        # Create reactions for SBML with theirs respective parameters and rates
        # What do I have so far
        # Species_String_Dict and a set of reaction objects in Reactions_Set
        Reactions_For_SBML, Parameters_For_SBML = reaction_construction_nb.create_all_reactions(cls.Reactions_set,
                                                                                                cls.Species_string_dict,
                                                                                                cls.Ref_object_to_characteristics,
                                                                                                cls.Ref_characteristics_to_object,
                                                                                                type_of_model)

        for parameters in Parameters_For_SBML:
            print(parameters, Parameters_For_SBML[parameters])

        for reaction in Reactions_For_SBML:
            print(reaction, Reactions_For_SBML[reaction])

        return Species_for_SBML, Reactions_For_SBML, Parameters_For_SBML, Mappings_for_SBML


class Reactions:

    @staticmethod
    def __create_reactants_string(list_of_reactants):
        reaction_string = ''
        for i, r in enumerate(list_of_reactants):
            if r['stoichiometry'] > 1:
                reaction_string += str(r['stoichiometry']) + '*' + str(r['object'])
            else:
                reaction_string += str(r['object'])

            reaction_string += "." + "_".join(r['characteristics'])

            if i != len(list_of_reactants) - 1:
                reaction_string += ' '
                reaction_string += '+'
                reaction_string += ' '

        return reaction_string

    def __str__(self):
        return self.__create_reactants_string(self.reactants) + \
               ' -> ' + self.__create_reactants_string(self.products)

    def __getitem__(self, item):
        return Simulator.override_get_item(self, item)

    def __init__(self, reactants, products):
        self.reactants = reactants
        self.products = products

        # Assign default order
        self.order = Round_Robin_RO

        self.rate = Simulator.Last_rate
        if Simulator.Last_rate is not None:
            Simulator.Last_rate = None

        # Here we extract all involved objects to pact them in a set
        # This is done to find the reactions associated with the species when the Simulator is started
        for reactant in reactants:
            reactant['object'].add_reaction(self)
        for product in products:
            product['object'].add_reaction(self)


class Reacting_Species:

    def __getitem__(self, item):
        return Simulator.override_get_item(self, item)

    def __init__(self, object_reference, characteristics, stoichiometry=1):
        if object_reference.get_name() == 'S0' and characteristics == set():
            self.list_of_reactants = []
        else:
            self.list_of_reactants = [{'object': object_reference, 'characteristics': characteristics,
                                       'stoichiometry': stoichiometry}]

    def __add__(self, other):
        if isinstance(other, Species):
            other = Reacting_Species(other, set())
        self.list_of_reactants += other.list_of_reactants
        return self

    def __rshift__(self, other):
        if isinstance(other, Species):
            p = Reacting_Species(other, set())
        else:
            p = other

        reaction = Reactions(self.list_of_reactants, p.list_of_reactants)
        return reaction

    def __call__(self, quantity):
        if len(self.list_of_reactants) != 1:
            raise TypeError('Assignment used incorrectly')

        species_object = self.list_of_reactants[0]['object']
        characteristics = self.list_of_reactants[0]['characteristics']
        species_object.add_quantities(characteristics, quantity)
        return self

    def __getattr__(self, characteristic):

        """
            Test
        """
        for reactant in self.list_of_reactants:

            species_object = reactant['object']
            characteristics_from_references = meta_class_utils.unite_characteristics(species_object.get_references())

            if characteristic not in characteristics_from_references:
                species_object.add_characteristic(characteristic)

            reactant['characteristics'].add(characteristic)

        return self


class ParallelSpecies:

    def __init__(self, list_of_species):
        self.list_of_species = list_of_species

    def append(self, species):
        if not isinstance(species, Species):
            raise TypeError('Only Species can be appended')
        self.list_of_species.append(species)

    def __or__(self, other):
        if isinstance(other, Species):
            self.append(other)
            return self
        elif isinstance(other, ParallelSpecies):
            return ParallelSpecies(self.list_of_species + other.list_of_species)
        else:
            raise TypeError('Operator must only be used in Species on ParallelSpecies')


class Species:

    # Get data from species for debugging Simulators
    def __str__(self):
        return self._name

    def show_reactions(self):
        print(str(self) + ':')
        for reference in self._references:
            for reaction in reference.get_reactions():
                print(reaction)

    def show_characteristics(self):
        print(str(self) + ':')
        for i, reference in enumerate(self.get_references()):
            if reference.get_characteristics():
                print(str(reference) + ': ', end='')
                reference.print_characteristics()

    def show_references(self):
        print(str(self) + ':')
        print('{', end='')
        for i, reference in enumerate(self.get_references()):
            if reference.get_characteristics():
                print(' ' + str(reference) + ' ', end='')
        print('}')

    def show_quantities(self):
        print(self._species_counts)

    # Creation of ParallelSpecies For Simulation ##################
    def __or__(self, other):
        if isinstance(other, ParallelSpecies):
            other.append(self)
            return other
        else:
            return ParallelSpecies([self, other])

    # Creation of reactions using entities ########################
    def __getitem__(self, item):
        return Simulator.override_get_item(self, item)

    def __rmul__(self, stoichiometry):
        if type(stoichiometry) == int:
            r = Reacting_Species(self, set(), stoichiometry)
        else:
            raise ValueError('Stoichiometry can only be an int')
        return r

    def __add__(self, other):
        r1 = Reacting_Species(self, set())
        if isinstance(other, Reacting_Species):
            r2 = other
        else:
            r2 = Reacting_Species(other, set())
        return r1 + r2

    def __radd__(self, other):
        Species.__add__(self, other)

    def __rshift__(self, other):
        myself = Reacting_Species(self, set())

        if isinstance(other, Species):
            p = Reacting_Species(other, set())
        elif other == 0:
            exit()
        else:
            p = other

        reaction = Reactions(myself.list_of_reactants, p.list_of_reactants)
        return reaction

    # Adding characteristics to an Entity or Property ####################
    def __getattr__(self, characteristic):

        # First check for commands
        self.check_for_commands(characteristic)

        characteristics_from_references = meta_class_utils.unite_characteristics(self.get_references())
        characteristics = {characteristic}

        if characteristic not in characteristics_from_references:

            if len(self.get_characteristics()) == 0:
                self.first_characteristic = characteristic

            self.add_characteristic(characteristic)

        return Reacting_Species(self, characteristics)

    def check_for_commands(self, characteristic):
        if characteristic == 'characteristics' or characteristic == 'characteristic':
            self.show_characteristics()
        elif characteristic == 'reactions' or characteristic == 'reaction':
            self.show_reactions()
        elif characteristic == 'references' or characteristic == 'reference':
            self.show_references()

    # Adding counts to species
    def __call__(self, quantity):
        self.add_quantities('std$', quantity)
        return self

    def add_quantities(self, characteristics, quantity):
        '''
        :param characteristics: characteristics of the species to be set
        :param quantity: counts of that specific species

            We do it like this because Python can't accept sets as dictionary keys
            Set the quantity of an specific string of species
        '''
        already_in = False
        for e in self._species_counts:
            if characteristics == e['characteristics']:
                e['quantity'] = quantity
                already_in = True
        if not already_in:
            self._species_counts.append({'characteristics': characteristics, 'quantity': quantity})

    def reset_quantities(self):
        self._species_counts = []

    def get_quantities(self):
        return self._species_counts

    # Creation of other objects through multiplication ##################
    def __mul__(self, other):

        Simulator.Entity_counter += 1
        name = 'E' + str(Simulator.Entity_counter)
        new_entity = Species(name)
        new_entity.set_references(meta_class_utils.combine_references(self, other))
        new_entity.add_reference(new_entity)

        meta_class_utils.check_orthogonality_between_references(new_entity.get_references())

        return new_entity

    def __init__(self, name):
        self._name = name
        self._characteristics = set()
        self._references = {self}

        # This is necessary for the empty objects generated when we perform multiplication with more than 2 Properties
        self.first_characteristic = None

        # Each object stores the reactions it is involved in
        self._reactions = set()

        # This will store the quantities relating to the species counts
        self._species_counts = []

    # Encapsulation of Species ########################################

    def name(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def get_characteristics(self):
        return self._characteristics

    def add_characteristic(self, characteristic):
        self._characteristics.add(characteristic)

    def remove_characteristic(self, characteristic):
        self._characteristics.remove(characteristic)

    def print_characteristics(self):
        print(self._characteristics)

    def get_references(self):
        return self._references

    def add_reference(self, reference):
        self._references.add(reference)

    def set_references(self, reference_set):
        self._references = reference_set

    def get_reactions(self):
        return self._reactions

    def set_reactions(self, reactions):
        self._reactions = reactions

    def add_reaction(self, reaction):
        self._reactions.add(reaction)


# Property Call to return several properties as called
def Create(number_of_properties=1):
    to_return = []
    for i in range(number_of_properties):
        Simulator.Entity_counter += 1
        name = 'P' + str(Simulator.Entity_counter)
        to_return.append(Species(name))

    if number_of_properties == 1:
        return to_return[0]
    else:
        return tuple(to_return)


S0 = Create(1)
S0.name('S0')

if __name__ == '__main__':

    Age, Mood, Live = Create(3)


    def rate(human1):
        if human1.happy:
            return 10
        else:
            return 5


    # Age.young >> Age.old[rate]
    # Mood.sad >> Mood.happy[3]
    # Live.live >> Live.dead[40]
    # Human = Age * Mood
    # Human(200)  # Human.young.sad.live
    # Simulator.compile(Human, type_of_model='stochastic')

    P = Create(1)

    Age.young >> Age.old[rate]
    Mood.sad >> Mood.happy[3]
    # Live.live >> Live.dead[40]
    Human = Age * Mood
    S0 >> Human [10]
    Human(200)  # Human.young.sad.live
    Simulator.compile(Human | P, type_of_model='stochastic')


    """
    A, B, C, D = Create(4)
    A(100) + B(100) >> C + D [20]
    print(Simulator.compile(A | B | C | D, type_of_model='stochastic'))
    """