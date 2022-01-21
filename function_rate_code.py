from meta_class import *


class Bool_Override:

    def __bool__(self):
        # Reset the boolean value everytime this is called
        to_return_boolean = self._stocked_boolean
        self._stocked_boolean = True
        return to_return_boolean


class Specific_Species_Operator(Bool_Override):

    def __init__(self, species_string):
        self.species_string = species_string
        self._stocked_characteristics = set()

    def __getattr__(self, characteristic):
        self._stocked_characteristics.add(characteristic)
        return self

    def __str__(self):
        return self.species_string


class Concatenate_Specific_Species_Operator:

    def __init__(self, list_of_species_operators):
        self.list_of_species_operators = list_of_species_operators

    def __getattr__(self, item):
        self.list_of_species_operators[0].__getattr__(item)
        return self


class Rate_Operator_Base():
    pass


class All(Bool_Override):

    def __init__(self, concatenate_sso_object):
        self._concatenate_sso_object = concatenate_sso_object
        self._stocked_boolean = True

    def __getattr__(self, item):
        bool_list = []
        for sso_object in self._concatenate_sso_object:
            bool_list.append(bool(sso_object.__get))


def extract_reaction_rate(combination_of_reactant_species, reactant_string_list
                          , reaction_rate_function, Parameters_For_SBML):
    '''
        The order of the reactants appears in species_string_dict appears equality
        to the order they appear on the reaction

        If an int or a flot is returned we apply basic kinetics from CRN
        If a str is returned we use that as it is.
        Remember to set Parameters_For_SBML if needed

        remember 2-Ecoli means Ecoli + Ecoli so stoichiometry must be taken into consideration

        species_string_list is a dictionary with {'reactants' :[ list_of_reactants ], 'products':[ list_of_products ]}
        reaction_rate_function is the rate function passed by the user
        Parameters_For_SBML are the parameters used for the SBML construction

        returns: the reaction kinetics as a string for SBML
    '''

    if type(reaction_rate_function) == int or type(reaction_rate_function) == float:
        reaction_rate_string = basic_kinetics_string(reactant_string_list,
                                                     reaction_rate_function, Parameters_For_SBML)

    elif callable(reaction_rate_function):
        prepare_arguments_for_callable(combination_of_reactant_species,
                                       reactant_string_list, reaction_rate_function.__code__.co_varnames)
        exit()
        rate = reaction_rate_function(reactant_string_list, Parameters_For_SBML)

        if type(rate) == int or type(rate) == float:
            reaction_rate_string = basic_kinetics_string(reactant_string_list,
                                                         rate, Parameters_For_SBML)
        elif type(rate) == str:
            return rate

        else:
            raise TypeError('The function return a non-valid value')

    elif type(reaction_rate_function) == str:
        return reaction_rate_function

    else:
        raise TypeError('The rate type is not supported')

    return reaction_rate_string


def basic_kinetics_string(reactants, reaction_rate, Parameters_For_SBML):
    kinetics_string = ""
    for reactant in reactants:
        kinetics_string = kinetics_string + str(reactant) + ' * '

    rate_name = 'rate_' + str(len(Parameters_For_SBML))
    Parameters_For_SBML[rate_name] = (reaction_rate, 'per_min')

    kinetics_string = kinetics_string + rate_name

    return kinetics_string


def prepare_arguments_for_callable(combination_of_reactant_species, reactant_string_list, rate_function_arguments):

    base_dict = {}
    species_counter = {}
    for i, (species, reactant_string) in enumerate(zip(combination_of_reactant_species, reactant_string_list)):
        species = species['object']
        reactant_name = 'reactant' + str(i + 1)

        try:
            species_counter[species] += 1
        except KeyError:
            species_counter[species] = 1

        species_name = species.get_name() + str(species_counter[species])

        base_dict[reactant_name] = Specific_Species_Operator(reactant_string)
        base_dict[species_name] = Specific_Species_Operator(reactant_string)
        base_dict[species_name.lower()] = Specific_Species_Operator(reactant_string)

    print(base_dict)
    exit()


if __name__ == '__main__':

    All().freefall
    exit()

    Human = Specific_Species_Operator('Human.happy.sad.eater')

    if Human.happy.not_eating:
        print('Hi')
    else:
        print('Ho')

    if Human.happy.eater:
        print('Hi')
    else:
        print('Ho')

    exit()

    def human_rate(human0, human1):
        if human0.hot and human1.hot:
            return 5
        else:
            return 10

    def hi(a, b):
        return a + b

    # k = {'a': 10, 'b': 20}

    # print(hi(**k))