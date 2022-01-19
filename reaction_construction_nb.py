from copy import deepcopy
import itertools


def iterator_for_combinations(list_of_lists):
    for i in itertools.product(*list_of_lists):
        yield i


def next_combination(current_state, lists_of_species):
    '''
        This function cycles to the species in the reactants to define all the individual reactions for Copasi
    :param current_state: current state requested of the the lists of species
    :param lists_of_species: lists containing all the same time of species involved in the reactions
    :return:
    '''
    to_return = []
    test_list = []
    for k, (i, species) in enumerate(zip(current_state, lists_of_species)):
        to_return.append(lists_of_species[k][i])
        test_list.append(i)

    try:
        current_state[0] = (current_state[0] + 1) % len(lists_of_species[0])

        streak = current_state[0] == 0
        for i in range(1, len(current_state)):

            if current_state[i - 1] == 0 and streak:
                streak = True
                current_state[i] = (current_state[i] + 1) % len(lists_of_species[i])
            else:
                streak = False
    except IndexError:
        pass

    return to_return


def separate_into_orthogonal_reactions(Reactions):
    cont_while = True
    while cont_while:

        reaction = Reactions.pop(0)

        for i, reactant in enumerate(reaction['re']):
            characteristics = reactant[1]

            check_for_duplicates = {}
            for cha in characteristics:

                try:
                    old_cha = check_for_duplicates[Ref_characteristics_to_object[cha]]

                    reaction1 = deepcopy(reaction)
                    reaction2 = deepcopy(reaction)

                    reaction1['re'][i][1].remove(old_cha)
                    reaction2['re'][i][1].remove(cha)

                    Reactions.append(reaction1)
                    Reactions.append(reaction2)

                    break

                except KeyError:
                    check_for_duplicates[Ref_characteristics_to_object[cha]] = cha

            cont_while = False


def construct_reactant_structures(reactant_species, Species_string_dict):
    species_string_combinations = []
    species_order_list = []

    '''
        First we construct the lists of the strings of the species involved
        And a list containing the species in order
    '''
    for reactant in reactant_species:

        species_order_list.append(reactant['object'])

        for _ in range(reactant['stoichiometry']):
            species_string_combinations.append(extract_species_strings(reactant['object'],
                                                                       reactant['characteristics'], Species_string_dict))

    return species_order_list, species_string_combinations


def construct_cyclic_structure(reactant_order_list, current_species_string_list):
    cyclic_dict = {}
    for species_order_list, species_string in zip(reactant_order_list, current_species_string_list):
        try:
            cyclic_dict[species_order_list]['list'].append(species_string)
        except KeyError:
            cyclic_dict[species_order_list] = {'list': [species_string], 'cyclic_value': 0}

    return cyclic_dict


def construct_product_structure(reaction):
    '''
       Here we unpack the products in list. This list will loop through the reactants so we can assign the correct string
       to each product

       We need to unpack according to their stoichiometry
    :param reaction: reaction currently being analysed
    :return: a list of all products involved unpacked according to their stoichiometry
    '''
    product_list = []
    for product in reaction.products:
        for _ in range(product['stoichiometry']):
            product_list.append({'species': product['object'], 'characteristics': product['characteristics']})

    return product_list


def construct_born_species(born_species, Species_string_dict):
    species_string_combinations = []
    for species in born_species:
        species_string_combinations.append(extract_species_strings(species['species'],
                                                                   species['characteristics'],
                                                                   Species_string_dict))

    return species_string_combinations


def construct_single_reaction_for_sbml(reactant_species_string_list, product_species_string_list, reaction_rate):
    to_return = {'re': [], 'pr': [], 'kin': reaction_rate}

    reactant_count_dict = count_string_dictionary(reactant_species_string_list)
    product_count_dict = count_string_dictionary(product_species_string_list)

    for key in reactant_count_dict:
        to_return['re'].append((reactant_count_dict[key], key))

    for key in product_count_dict:
        to_return['pr'].append((product_count_dict[key], key))

    return to_return


def count_string_dictionary(list_of_strings):
    to_return = {}

    for e in list_of_strings:
        try:
            to_return[e] += 1
        except KeyError:
            to_return[e] = 1

    return to_return


def extract_species_strings(species, characteristics, Species_string_dict):

    species_strings_list = []
    species_strings_to_filter = set()

    species_strings_to_filter = species_strings_to_filter.union(Species_string_dict[species])

    for species_string in species_strings_to_filter:
        species_string_split = species_string.split('.')

        if all(char in species_string_split for char in characteristics):
            species_strings_list.append(species_string)

    return species_strings_list


def transform_species_string(species_string, characteristics_to_transform):

    species_to_return = deepcopy(species_string)
    for characteristic in characteristics_to_transform:
        replaceable_characteristics = Ref_object_to_characteristics[Ref_characteristics_to_object[characteristic]]

        for rep_cha in replaceable_characteristics:
            species_to_return = species_to_return.replace('.' + rep_cha, '.' + characteristic)

    return species_to_return


def extract_reaction_rate(species_string_dict, reaction_rate_function, Parameters_For_SBML):
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
        reaction_rate_string = basic_kinetics_string(species_string_dict['reactants'],
                                                     reaction_rate_function, Parameters_For_SBML)

    elif callable(reaction_rate_function):
        rate = reaction_rate_function(species_string_dict, Parameters_For_SBML)

        if type(rate) == int or type(rate) == float:
            reaction_rate_string = basic_kinetics_string(species_string_dict['reactants'],
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


# TODO Ask about this
# TODO REALLY DON'T FORGET THIS, THIS IS VITAL
# TODO Fabricio there are 3 TODO here don't forget it
def basic_kinetics_string(reactants, reaction_rate, Parameters_For_SBML):
    kinetics_string = ""
    for reactant in reactants:
        kinetics_string = kinetics_string + str(reactant) + ' * '

    rate_name = 'rate_' + str(len(Parameters_For_SBML))
    Parameters_For_SBML[rate_name] = (reaction_rate, 'per_min')

    kinetics_string = kinetics_string + rate_name

    return kinetics_string


def get_involved_species(reaction, Species_string_dict):

    reactant_species_combination_list = []

    for reactant in reaction.reactants:
        species_for_reactant = []
        for species in Species_string_dict:
            if reactant['object'] in species.get_references():
                species_for_reactant.append({'object': species,
                                             'characteristics': reactant['characteristics'],
                                             'stoichiometry': reactant['stoichiometry']})

        reactant_species_combination_list.append(species_for_reactant)

    return reactant_species_combination_list


def create_all_reactions(Reactions, Species_string_dict, Reaction_rate_functions):

    Reactions_For_SBML = {}
    Parameters_For_SBML = {}

    for reaction in Reactions:

        reactant_species_combination_list = get_involved_species(reaction, Species_string_dict)
        for combination_of_reactant_species in iterator_for_combinations(reactant_species_combination_list):

            reactant_order_list, reactant_string_list = \
                construct_reactant_structures(combination_of_reactant_species, Species_string_dict)
            product_list = construct_product_structure(reaction)

            for reactants in iterator_for_combinations(reactant_string_list):
                cyclic_dict = construct_cyclic_structure(reactant_order_list, reactants)

            print(cyclic_dict)
            exit()

            born_species = []
            product_species_string_list = []
            born_species_string_list = []
            for product in product_list:

                try:
                    species_string_reactant = cyclic_dict[product['species']]['list'][
                        cyclic_dict[product['species']]['cyclic_value']]
                    cyclic_dict[product['species']]['cyclic_value'] += cyclic_dict[product['species']]['cyclic_value']
                    product_species_string_list.append(
                        transform_species_string(species_string_reactant, product['characteristics']))

                except KeyError:
                    born_species.append(product)

            if len(born_species) > 0:
                born_species_string_combinations = construct_born_species(born_species, Species_string_dict)
                current_state_born = [0] * len(born_species_string_combinations)
                final_state_born = [0] * len(born_species_string_combinations)

            while True:

                if len(born_species) > 0:
                    born_species_string_list = next_combination(current_state_born, born_species_string_combinations)

                reaction_rate = extract_reaction_rate({'reactants': reactant_species_string_list,
                                                       'products': product_species_string_list + born_species_string_list},
                                                      Reaction_rate_functions['reaction_object'],
                                                      Parameters_For_SBML)

                assert type(reaction_rate) == str

                Reactions_For_SBML['reaction_' + str(len(Reactions_For_SBML))] = construct_single_reaction_for_sbml(
                    reactant_species_string_list,
                    product_species_string_list + born_species_string_list,
                    reaction_rate)

                if len(born_species) == 0:
                    break
                else:
                    if current_state_born == final_state_born:
                        break

            if current_state == final_state:
                break

    return Reactions_For_SBML, Parameters_For_SBML


if __name__ == '__main__':

    Ref_characteristics_to_object = {
        'young': 1,
        'old': 1,
        'alive': 2,
        'dead': 2,
        'sad': 3,
        'happy': 3
    }

    Ref_object_to_characteristics = {
        1: {'young', 'old'},
        2: {'alive', 'dead'},
        3: {'sad', 'happy'}
    }

    Species_string_dict = {
        'Ecoli': {'Ecoli.young.alive.sad',
                  'Ecoli.young.alive.happy',
                  'Ecoli.young.dead.sad',
                  'Ecoli.young.dead.happy',
                  'Ecoli.old.alive.sad',
                  'Ecoli.old.alive.happy',
                  'Ecoli.old.dead.sad',
                  'Ecoli.old.dead.happy'}
    }

    def reaction_rate_function_test(*args):
        reaction_dict = args[0]
        return 5

    Reaction_rate_functions = {
        'reaction_object': reaction_rate_function_test
    }

    Reactions = [
        {'re': [('Ecoli', {'young'}, 1)], 'pr': [('Ecoli', {'old'}, 1)]}
    ]

    reactions, parameters = create_all_reactions(Reactions, Species_string_dict, Reaction_rate_functions)

    for key in reactions:
        print(key, reactions[key])

    #TODO
    # Ecoli.not_infected.yellow >> Ecoli.red
    # Ecoli.not_infected.blue >> Ecoli.red

    # 0 >> Ecoli

    # Ecoli + P >> 0
    # Ecoli + P >> Ecoli

    # 0 >> Ecoli.young

    # ResourceEater + R >> 2*ResourceEater

    # 0 >> Ecoli
    # Ecoli >> 2*Ecoli

    # A + B >> C + D

    # Carnivore >> Carnivore + Bone.bloody
