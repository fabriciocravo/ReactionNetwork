from meta_class import *
import reaction_construction_nb as rc


class Bool_Override:

    def __bool__(self):
        # Return false if the species does not exist in reaction
        if self.species_string == '$Null':
            return False

        species_string_split = self.species_string.split('.')
        if all(char in species_string_split for char in self._stocked_characteristics):
            to_return_boolean = True
        else:
            to_return_boolean = False

        self._stocked_characteristics = set()
        return to_return_boolean


class Specific_Species_Operator(Bool_Override):

    def __init__(self, species_string, species_object):
        self.species_string = species_string
        self._stocked_characteristics = set()
        self._species_object = species_object

    def __getattr__(self, characteristic):
        self._stocked_characteristics.add(characteristic)
        return self

    def __str__(self):
        return self.species_string

    def add(self, characteristic):
        self._stocked_characteristics.add(characteristic)


class Concatenate_Specific_Species_Operator:

    def __init__(self, list_of_species_operators):
        self.list_of_species_operators = list_of_species_operators

    def __getattr__(self, item):
        if len(self.list_of_species_operators) > 1:
            raise TypeError("Error: Two more species were referenced as one. \n" +
                            "Please use All() or Any()")
        self.list_of_species_operators[0].__getattr__(item)
        return self


class Group_Operator_Base:

    def __init__(self, sso):
        if isinstance(sso, Specific_Species_Operator):
            self._concatenate_sso_object = [sso]
        elif isinstance(sso, Concatenate_Specific_Species_Operator):
            self._concatenate_sso_object = sso.list_of_species_operators

    def __getattr__(self, item):
        for sso_object in self._concatenate_sso_object:
            sso_object.add(item)
        return self


class All(Bool_Override, Group_Operator_Base):

    def __bool__(self):
        return all([bool(sso_object) for sso_object in self._concatenate_sso_object])


class Any(Bool_Override, Group_Operator_Base):

    def __bool__(self):
        return any([bool(sso_object) for sso_object in self._concatenate_sso_object])


class IsInstance(Bool_Override):

    @staticmethod
    def contains_reference(sso, reference):

        if reference in sso._species_object.get_references():
            return True
        else:
            return False

    def __init__(self, sso, reference):
        self._operator = None
        self._reference = reference
        if isinstance(sso, Specific_Species_Operator):
            self._concatenate_sso_object = [sso]
        elif isinstance(sso, Concatenate_Specific_Species_Operator):
            self._concatenate_sso_object = sso.list_of_species_operators
        elif isinstance(sso, All):
            self._concatenate_sso_object = sso._concatenate_sso_object
            self._operator = 'All'
        elif isinstance(sso, Any):
            self._concatenate_sso_object = sso._concatenate_sso_object
            self._operator = 'Any'

    def __bool__(self):
        if not self._operator:
            if len(self._concatenate_sso_object) > 1:
                raise TypeError('IsInstance is only used for single species. Please use all or any')
            if self.contains_reference(self._concatenate_sso_object[0], self._reference):
                return True

        # All code
        if self._operator == 'All':
            for sso in self._concatenate_sso_object:
                if not self.contains_reference(sso, self._reference):
                    return False
            return True

        # Any Code
        if self._operator == 'Any':
            for sso in self._concatenate_sso_object:
                if self.contains_reference(sso, self._reference):
                    return True
            return False


def extract_reaction_rate(combination_of_reactant_species, reactant_string_list
                          , reaction_rate_function, Parameters_For_SBML, type_of_model):
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
                                                     reaction_rate_function, Parameters_For_SBML, type_of_model)

    elif callable(reaction_rate_function):
        arguments = prepare_arguments_for_callable(combination_of_reactant_species,
                                                   reactant_string_list, reaction_rate_function.__code__.co_varnames)
        rate = reaction_rate_function(**arguments)

        if type(rate) == int or type(rate) == float:
            reaction_rate_string = basic_kinetics_string(reactant_string_list,
                                                         rate, Parameters_For_SBML, type_of_model)
        elif type(rate) == str:
            return rate

        else:
            raise TypeError('The function return a non-valid value')

    elif type(reaction_rate_function) == str:
        return reaction_rate_function

    else:
        raise TypeError('The rate type is not supported')

    return reaction_rate_string


def basic_kinetics_string(reactants, reaction_rate, Parameters_For_SBML, type_of_model):

    counts = rc.count_string_dictionary(reactants)

    if type_of_model.lower() not in ['stochastic', 'deterministic']:
        raise TypeError('Type of model not supported. Only stochastic or deterministic')

    kinetics_string = ""
    for name, number in counts.items():
        if type_of_model.lower() == 'stochastic':
            kinetics_string += stochastic_string(name, number)
        elif type_of_model.lower() == 'deterministic':
            kinetics_string += deterministic_string(name, number)

    rate_str = 'rate_' + str(len(Parameters_For_SBML))
    Parameters_For_SBML[rate_str] = reaction_rate

    if kinetics_string == '':
        kinetics_string += rate_str
    else:
        kinetics_string += ' * ' + rate_str

    return kinetics_string


# TODO ask about this, make sure it is right
# TODO really important !!!!!!!
def stochastic_string(reactant_name, number):

    to_return_string = ''
    for i in range(number):
        if i == 0:
            to_return_string = reactant_name
        else:
            to_return_string += f' * ({reactant_name} - {i})/{i + 1}'
    return to_return_string


def deterministic_string(reactant_name, number):

    to_return_string = ''
    for i in range(number):
        if i == 0:
            to_return_string = reactant_name
        else:
            to_return_string += f' * {reactant_name}'
    return to_return_string


def prepare_arguments_for_callable(combination_of_reactant_species, reactant_string_list, rate_function_arguments):
    base_dict = {}
    species_counter = {}
    species_lists = {}
    reactants_list = []
    for i, (species, reactant_string) in enumerate(zip(combination_of_reactant_species, reactant_string_list)):
        species = species['object']
        reactant_name = 'reactant' + str(i + 1)

        try:
            species_counter[species] += 1
        except KeyError:
            species_counter[species] = 1

        species_name = species.get_name() + str(species_counter[species])

        sso = Specific_Species_Operator(reactant_string, species)
        base_dict[reactant_name] = sso
        base_dict[species_name] = sso
        base_dict[species_name.lower()] = sso

        reactants_list.append(Specific_Species_Operator(reactant_string, species))

        try:
            species_lists[species].append(sso)
        except KeyError:
            species_lists[species] = [sso]

    base_dict['reactants'] = Concatenate_Specific_Species_Operator(reactants_list)

    for keys in species_lists:
        base_dict[keys.get_name()] = Concatenate_Specific_Species_Operator(species_lists[keys])
        base_dict[keys.get_name().lower()] = Concatenate_Specific_Species_Operator(species_lists[keys])

    to_return_dict = {}
    for argument in rate_function_arguments:
        try:
            to_return_dict[argument] = base_dict[argument]
        # If not create a null species to return false to everything
        except KeyError:
            to_return_dict[argument] = Specific_Species_Operator('$Null', create_properties(1))

    return to_return_dict


if __name__ == '__main__':
    pass
