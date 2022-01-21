from copy import deepcopy
import function_rate_code as fr
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

    '''
        First we construct the lists of the strings of the species involved
        And a list containing the species in order
    '''
    for reactant in reactant_species:
        species_string_combinations.append(extract_species_strings(reactant['object'],
                                                                   reactant['characteristics'], Species_string_dict))

    return species_string_combinations


def construct_order_structure(species_order_list, current_species_string_list):
    cyclic_dict = {}
    for species_object, species_string in zip(species_order_list, current_species_string_list):
        try:
            cyclic_dict[species_object].append(species_string)
        except KeyError:
            cyclic_dict[species_object] = [species_string]

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


def get_involved_species(reaction, Species_string_dict):
    reactant_species_combination_list = []
    base_species_order = []
    species_for_reactant = []

    for reactant in reaction.reactants:
        for _ in range(reactant['stoichiometry']):

            species_for_reactant = []
            base_species_order.append(reactant['object'])

            for species in Species_string_dict:
                if reactant['object'] in species.get_references():
                    species_for_reactant.append({'object': species,
                                                 'characteristics': reactant['characteristics']})

        reactant_species_combination_list.append(species_for_reactant)

    return base_species_order, reactant_species_combination_list


def create_all_reactions(Reactions, Species_string_dict,
                         Ref_object_to_characteristics,
                         Ref_characteristics_to_object):
    Reactions_For_SBML = {}
    Parameters_For_SBML = {}
    reaction_number = 0

    for reaction in Reactions:

        base_species_order, reactant_species_combination_list = get_involved_species(reaction, Species_string_dict)
        for combination_of_reactant_species in iterator_for_combinations(reactant_species_combination_list):

            reactant_species_string_combination_list = \
                construct_reactant_structures(combination_of_reactant_species, Species_string_dict)

            for reactant_string_list in iterator_for_combinations(reactant_species_string_combination_list):
                product_object_list = construct_product_structure(reaction)
                order_structure = construct_order_structure(base_species_order, reactant_string_list)

                product_species_species_string_combination_list = reaction.order(order_structure, product_object_list,
                                                                                 Species_string_dict,
                                                                                 Ref_object_to_characteristics,
                                                                                 Ref_characteristics_to_object)

                for product_string_list in iterator_for_combinations(product_species_species_string_combination_list):
                    reaction_number += reaction_number
                    fr.extract_reaction_rate(combination_of_reactant_species, reactant_string_list
                                             , lambda x: x, Parameters_For_SBML)
                    exit()

                    Reactions_For_SBML['reaction_' + str(reaction_number)] = \
                        construct_single_reaction_for_sbml(reactant_string_list, product_string_list, 10)

    print(Reactions_For_SBML)
    exit()

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

    # TODO
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
