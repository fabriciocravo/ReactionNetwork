from copy import deepcopy

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

Reaction_Rates = {'sad': 2, 'happy': 1}

Reactions = [
    {'re': [('Ecoli', {'young'}, 1)], 'pr': [('Ecoli', {'old'}, 1)]}
]

Reactions = [
    {'re': [], 'pr': [('Ecoli', {'young'}, 1)]}
]


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


def construct_reactant_structures(reaction, Species_string_dict):

    # Just in case there are no reactants in the reaction
    # Which is the creation case
    per_species = []

    species_string_combinations = []
    species_order_list = []

    '''
        First we construct the lists of the strings of the species involved
        And a list containing the species in order
    '''
    for reactant in reaction['re']:

        per_species = []
        species_order_list.append(reactant[0])

        for _ in range(reactant[2]):
            species_string_combinations.append(extract_species_strings(reactant[0], reactant[1], Species_string_dict))

    return species_order_list, species_string_combinations


def construct_cyclic_structure(species_order_list, current_species_string_list):

    cyclic_dict = {}
    for species_order_list, species_string in zip(species_order_list, current_species_string_list):
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
    for product in reaction['pr']:
        for _ in range(product[2]):
            product_list.append({'species': product[0], 'characteristics': product[1]})

    return product_list


def construct_born_species(born_species, Species_string_dict):

    species_string_combinations = []
    for species in born_species:
        species_string_combinations.append(extract_species_strings(species['species'],
                                                                species['characteristics'],
                                                                Species_string_dict))

    return species_string_combinations


def construct_single_reaction_for_sbml(reactant_species_string_list, product_species_string_list,
                                       born_species_string_list, reaction_rate):

    to_return = {'re': [], 'pr': []}

    reactant_count_dict = count_string_dictionary(reactant_species_string_list)
    product_count_dict = count_string_dictionary(product_species_string_list + born_species_string_list)

    for key in reactant_count_dict:
        to_return['re'].append((reactant_count_dict[key], key))

    for key in product_count_dict:
        to_return['pr'].append((product_count_dict[key], key))

    return to_return


def count_string_dictionary(list_of_strings):

    to_return = {}

    print(list_of_strings)

    for e in list_of_strings:
        try:
            to_return[e] += 1
        except KeyError:
            to_return[e] = 1

    return to_return


def extract_species_strings(species, characteristics, Species_string_dict):

    species_string_list = []

    species_strings = Species_string_dict[species]
    for species_string in species_strings:
        species_string_split = species_string.split('.')

        if all(char in species_string_split for char in characteristics):
            species_string_list.append(species_string)

    return species_string_list


def transform_species_string(species_string, characteristics_to_transform):

    species_to_return = deepcopy(species_string)
    for characteristic in characteristics_to_transform:
        replaceable_characteristics = Ref_object_to_characteristics[Ref_characteristics_to_object[characteristic]]

        for rep_cha in replaceable_characteristics:
            species_to_return = species_to_return.replace('.' + rep_cha, '.' + characteristic)

    return species_to_return


def extract_reaction_rate():
    pass


def create_all_reactions(Reactions, Species_string_dict):

    Reactions_For_SBML = {}
    res_number = 0
    reactions_model_formatted = {}

    for reaction in Reactions:

        species_order_list, species_string_combinations = construct_reactant_structures(reaction, Species_string_dict)
        product_list = construct_product_structure(reaction)

        # Now we loop through every possible combination
        current_state = [0] * len(species_string_combinations)
        final_state = [0] * len(species_string_combinations)

        while True:

            '''
                reaction_species_string_list has the string of all reactants involved
                reaction_product_string_list has the string of all products involved
                mix them to get a single reaction
            '''
            reactant_species_string_list = next_combination(current_state, species_string_combinations)
            cyclic_dict = construct_cyclic_structure(species_order_list, reactant_species_string_list)

            born_species = []
            product_species_string_list = []
            born_species_string_list = []
            for product in product_list:

                try:
                    species_string_reactant = cyclic_dict[product['species']]['list'][cyclic_dict[product['species']]['cyclic_value']]
                    cyclic_dict[product['species']]['cyclic_value'] += cyclic_dict[product['species']]['cyclic_value']
                    product_species_string_list.append(transform_species_string(species_string_reactant, product['characteristics']))

                except KeyError:
                    born_species.append(product)

            if born_species:

                born_species_string_combinations = construct_born_species(born_species, Species_string_dict)

                current_state_born = [0] * len(born_species_string_combinations)
                final_state_born = [0] * len(born_species_string_combinations)

                born_species_string_list = next_combination(current_state_born, born_species_string_combinations)

                reaction_rate = extract_reaction_rate()
                test = construct_single_reaction_for_sbml(reactant_species_string_list, product_species_string_list,
                                                   born_species_string_list, 0)
                print(test)

            if current_state == final_state:
                break


if __name__ == '__main__':

    create_all_reactions(Reactions, Species_string_dict)
    pass