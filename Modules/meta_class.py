import inspect
import Modules.meta_class_utils as mc
from Modules.order_operators import *
from Modules.function_rate_code import *
import Modules.reaction_construction_nb as rc


# Easter Egg: I finished the first version on a sunday at the BnF in Paris
# If anyone is reading this, I highly recommend you study there, it is quite a nice place
class Compiler:
    """
        This is the simulator call
        It receives the constructed objects and keeps track of the number of number of base species created
        It does so for automatic naming before compilation
        After compilation the species receive the variable name
    """

    # Basic storage of defined variables for Compiler
    Entity_counter = 0
    Reactions_set = set()
    Species_string_dict = {}
    Ref_object_to_characteristics = {}
    Ref_characteristics_to_object = {}
    Last_rate = None

    @classmethod
    def override_get_item(cls, object_to_return, item):
        """
            Due to priority in python the item is stored before the reaction
            So it is stored in the Compiler level and passed to the reaction object in the end
        """
        cls.Last_rate = item
        return object_to_return

    @classmethod
    def name_all_involved_species(cls, list_of_species_objects, names=None):
        """
            Name species automatically according to their variable names
        """
        if not names:
            raise TypeError('Species must be named' +
                            'Please set ( names == globals() ) in the MobsPy constructor for automatic naming')

        for species in list_of_species_objects:
            try:
                variable_name = [k for k, v in names.items() if v == species][0]
                species.name(variable_name)
            except KeyError:
                raise ValueError('There is a non-named species. '
                                 'Please set ( names == globals() ) in the MobsPy constructor for automatic naming')

    @classmethod
    def compile(cls, species_to_simulate, volume_ml, names=None, type_of_model='deterministic', verbose=True):
        # Define dictionaries to return to avoid compatibility problems

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
            and for the species dictionary for the Compiler
            
            And construct the Species_from_characteristic dictionary 
            This dictionary returns the species with an specific characteristic using it's key
            
            Also we construct the Species_from_object dictionary
            This dictionary returns the species from an specific object using the object as key
        """

        # We name the species according to variables names for convenience
        cls.name_all_involved_species(list_of_species_objects, names)

        # Perform checks
        mc.add_negative_complement_to_characteristics(list_of_species_objects)

        # Construct structures necessary for reactions
        cls.Ref_characteristics_to_object = mc.create_orthogonal_vector_structure(list_of_species_objects)

        # Start by creating the Mappings for the SBML
        # Convert to user friendly format as well
        Mappings_for_SBML = {}
        for spe_object in list_of_species_objects:
            Mappings_for_SBML[spe_object.get_name()] = []

        # List of Species objects
        for spe_object in list_of_species_objects:
            list_of_definitions = []
            for reference in spe_object.get_references():
                list_of_definitions.append(reference.get_characteristics())
            cls.Species_string_dict[spe_object] = mc.create_species_strings(spe_object,
                                                                            list_of_definitions)
        # Set of reactions involved
        cls.Reactions_set = set()
        for spe_object in list_of_species_objects:
            for reference in spe_object.get_references():
                cls.Reactions_set = cls.Reactions_set.union(reference.get_reactions())

        # Setting Species for SBML and 0 for counts
        Species_for_SBML = {}
        for spe_object in list_of_species_objects:
            for species_string in cls.Species_string_dict[spe_object]:
                Species_for_SBML[species_string] = 0

        # Create the mappings for sbml
        for spe_object in list_of_species_objects:
            for species_string in cls.Species_string_dict[spe_object]:
                Mappings_for_SBML[spe_object.get_name()].append(species_string.replace('_dot_', '.'))

        # Set initial counts for SBML
        for spe_object in list_of_species_objects:
            for count in spe_object.get_quantities():

                if count['quantity'] == 0:
                    continue

                count_set = \
                    mc.complete_characteristics_with_first_values(spe_object,
                                                                  count['characteristics'],
                                                                  cls.Ref_characteristics_to_object)

                for species_string in Species_for_SBML.keys():
                    species_set = mc.extract_characteristics_from_string(species_string)
                    if species_set == count_set:
                        Species_for_SBML[species_string] = count['quantity']
                        break

        # Volume correction
        for s in Species_for_SBML:
            Species_for_SBML[s] = int(Species_for_SBML[s] * volume_ml)

        # Create reactions for SBML with theirs respective parameters and rates
        # What do I have so far
        # Species_String_Dict and a set of reaction objects in Reactions_Set
        Reactions_For_SBML, Parameters_For_SBML = rc.create_all_reactions(cls.Reactions_set,
                                                                          cls.Species_string_dict,
                                                                          cls.Ref_characteristics_to_object,
                                                                          type_of_model)

        # Attach units to rates
        # Set rates to per_minute and not per_second
        for p in Parameters_For_SBML:
            Parameters_For_SBML[p] = (Parameters_For_SBML[p], 'per_min')

        if verbose:
            print()
            print('Species')
            for species in Species_for_SBML:
                print(species.replace('_dot_', '.'), Species_for_SBML[species])
            print()

            print('Mappings')
            for mapping in Mappings_for_SBML:
                print(str(mapping) + ' :')
                for element in Mappings_for_SBML[mapping]:
                    print(element)
            print()

            print('Parameters')
            for parameters in Parameters_For_SBML:
                print(parameters, Parameters_For_SBML[parameters])
            print()

            print('Reactions')
            for reaction in Reactions_For_SBML:
                print(reaction, str(Reactions_For_SBML[reaction]).replace('_dot_', '.'))

        return Species_for_SBML, Reactions_For_SBML, Parameters_For_SBML, Mappings_for_SBML


class Reactions:
    """
        This is the Reaction class. It contains the reactants, products, rate and order
        Reactions are created with the >> operator. Each reaction is stored in all involved objects
    """

    @staticmethod
    def __create_reactants_string(list_of_reactants):
        """
            Just a simple way to print reactions for debbuging
            Not relevant for simulation
        """
        reaction_string = ''
        for i, r in enumerate(list_of_reactants):
            if r['stoichiometry'] > 1:
                reaction_string += str(r['stoichiometry']) + '*' + str(r['object'])
            else:
                reaction_string += str(r['object'])

            reaction_string += '.' + '.'.join(r['characteristics'])

            if i != len(list_of_reactants) - 1:
                reaction_string += ' '
                reaction_string += '+'
                reaction_string += ' '

        return reaction_string

    def __str__(self):
        return self.__create_reactants_string(self.reactants) + \
               ' -> ' + self.__create_reactants_string(self.products)

    def __getitem__(self, item):
        return Compiler.override_get_item(self, item)

    def __init__(self, reactants, products):
        self.reactants = reactants
        self.products = products

        # Assign default order
        self.order = Round_Robin_RO

        self.rate = Compiler.Last_rate
        if Compiler.Last_rate is not None:
            Compiler.Last_rate = None

        # Here we extract all involved objects to pact them in a set
        # This is done to find the reactions associated with the species when the Compiler is started
        for reactant in reactants:
            reactant['object'].add_reaction(self)
        for product in products:
            product['object'].add_reaction(self)

    def set_rate(self, rate):
        self.rate = rate


class Reacting_Species:
    """
        If a species is involved in a reaction this object is created
        It contains the species object reference, the characteristics involved in the reaction and finally the stoichiometry
        It adds up by appending elements to a list
    """

    def __getitem__(self, item):
        return Compiler.override_get_item(self, item)

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
        for reactant in self.list_of_reactants:

            species_object = reactant['object']
            characteristics_from_references = mc.unite_characteristics(species_object.get_references())

            if characteristic not in characteristics_from_references:
                species_object.add_characteristic(characteristic)

            reactant['characteristics'].add(characteristic)

        return self


class ParallelSpecies:
    """
        Class to simulate several species at the same time
        It is basically a list of species
        Species become this using the | operator
    """

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
    """
        Fundamental class
        Contains the characteristics, the species name, the reactions it is involved in
        and finally the other species it references
        Objects store all the basic information necessary to create an SBML file and construct a model
        So we construct the species through reactions and __getattr__ to form a model
    """

    # Get data from species for debugging Compilers
    def __str__(self):
        return self._name

    def show_reactions(self):
        print(str(self) + '_dot_')
        for reference in self._references:
            for reaction in reference.get_reactions():
                print(reaction)

    def show_characteristics(self):
        print(str(self) + ' has the following characteristics referenced:')
        for i, reference in enumerate(self.get_references()):
            if reference.get_characteristics():
                print(str(reference) + ': ', end='')
                reference.print_characteristics()

    def show_references(self):
        print(str(self) + '_dot_')
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
        return Compiler.override_get_item(self, item)

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
        """
            characteristic: string of characteristic
            We add characteristics using the following manner Species.characteristic
            If it is the first time is called we add it to the set of characteristics
            Second time just creates a Reacting_Species for reaction construction

            IMPORTANT - DON'T USE DEEPCOPY - IT DOES NOT WORK WITH __getattr__
        """

        characteristics_from_references = mc.unite_characteristics(self.get_references())
        characteristics = {characteristic}

        if characteristic not in characteristics_from_references:

            if len(self.get_characteristics()) == 0:
                self.first_characteristic = characteristic

            self.add_characteristic(characteristic)

        return Reacting_Species(self, characteristics)

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
        """
            Multiplications are used to construct more complex species
            We do not concatenate characteristics. This keeps the structure intact for reaction construction
            Instead we combine the sets of references. Every processes references itself
        """
        Compiler.Entity_counter += 1
        name = 'E' + str(Compiler.Entity_counter)
        new_entity = Species(name)
        new_entity.set_references(mc.combine_references(self, other))
        new_entity.add_reference(new_entity)

        mc.check_orthogonality_between_references(new_entity.get_references())

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
    """
        A function to create multiple species at once
        Reduce the number of lines
    """
    to_return = []
    for i in range(number_of_properties):
        Compiler.Entity_counter += 1
        name = 'P' + str(Compiler.Entity_counter)
        to_return.append(Species(name))

    if number_of_properties == 1:
        return to_return[0]
    else:
        return tuple(to_return)


"""
    The Zero is defined here
    Used this for reactions that result in nothing or come from nothing
    The One is used to create new similar instances of a base species
    It's used to implement Copy
"""
__S0, __S1 = Create(2)
__S0.name('S0')
__S1.name('S1')

Zero = __S0


def Copy(species):
    return species*__S1


if __name__ == '__main__':

    # TODO: Fix this
    Age, Mood, Live, Phage, Infection = Create(5)


    # A, B, C, D = Create(4)
    # A(100) + B(100) >> C + D[20]
    # print(Compiler.compile(A | B | C | D, type_of_model='stochastic'))
    # exit()

    # TODO Check
    # Mood.sad >> Mood.happy [10]
    # Age.young >> Age.old [3]
    # Default_RR[ S0 >> Age [20] ]
    # Human = Age*Mood
    # Compiler.compile(Human, type_of_model='stochastic')
    # exit()

    def rate(x):
        if x.happy:
            return 10
        else:
            return 5


    Age.young >> Age.old[rate]
    Mood.sad >> Mood.happy[3]
    Human = Age * Mood
    Human(200)  # Human.young.sad.live
    Compiler.compile(Human, type_of_model='stochastic')
    exit()

    P = Create(1)

    Age.young >> Age.old[rate]
    Mood.sad >> Mood.happy[3]
    # Live.live >> Live.dead[40]
    Human = Age * Mood
    S0 >> Human[10]
    Human(200)  # Human.young.sad.live
    Compiler.compile(Human | P, type_of_model='stochastic')

    exit()

    A, B, C, D = Create(4)
    A(100) + B(100) >> C + D[20]
    print(Compiler.compile(A | B | C | D, type_of_model='stochastic'))
