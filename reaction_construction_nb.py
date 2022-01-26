from copy import deepcopy
import function_rate_code as fr
import itertools
import meta_class as mc


def iterator_for_combinations(list_of_lists):
    """
        Iterate through all the combinations of a list of lists
        [[A,B,C], [D, F, E], [G]] means:
        ADG, AFG, AEG, BDG, BFG, BEG, CDG, CFG, CEG .....
    """
    for i in itertools.product(*list_of_lists):
        yield i


def copy_reaction(reaction):
    """
        Just copies a reaction
        Deepcopy is not working because it calls __getattr__ on the species with a private method
    """
    reactants = []
    for reactant in reaction.reactants:
        characteristics = deepcopy(reactant['characteristics'])
        species = reactant['object']
        stoichiometry = reactant['stoichiometry']
        reactants.append({'object': species, 'characteristics': characteristics,
                          'stoichiometry': stoichiometry})

    products = []
    for product in reaction.products:
        characteristics = deepcopy(product['characteristics'])
        species = product['object']
        stoichiometry = product['stoichiometry']
        products.append({'object': species, 'characteristics': characteristics,
                        'stoichiometry': stoichiometry})

    reaction_copy = mc.Reactions(reactants, products)
    reaction_copy.set_rate(reaction.rate)
    return reaction_copy


def separate_into_orthogonal_reactions(Reactions, Ref_characteristics_to_object, with_products = False):
    """
        This function separates reactions into completely orthogonal ones
        For instance, lets say red and blue belong to the same set of Species Characteristics

        Age.young >> Age.old [3]
        Mood.sad >> Mood.happy [5]
        Human = Age*Mood
        Human.blue.yellow >> Human.red  [20]

        This would mean Human.blue >> Human.red and Human.yellow >> Human.red
        This function creates two new reaction objects with that
        This function was designed so a user can reference multiple characteristics from the same Species
        To group reactions

        It does by transforming the reactions in a list and reading two reactions if there is ever
        a reference to two characteristics that belong to the same Species

        It works in a similar fashion for products. Generating both reactions
    """
    Reaction_List = list(Reactions)

    cont_while = True
    while cont_while:

        reaction = Reaction_List.pop(0)

        for i, reactant in enumerate(reaction.reactants):
            characteristics = reactant['characteristics']

            check_for_duplicates = {}
            for cha in characteristics:

                try:
                    old_cha = check_for_duplicates[Ref_characteristics_to_object[cha]]

                    # DEEP COPY DOES NOT WORK DIRECTLY, WE NEED TO CREATE A NEW OBJECT
                    reaction1 = copy_reaction(reaction)
                    reaction2 = copy_reaction(reaction)

                    reaction1.reactants[i]['characteristics'].remove(old_cha)
                    reaction2.reactants[i]['characteristics'].remove(cha)

                    Reaction_List.append(reaction1)
                    Reaction_List.append(reaction2)

                    break

                except KeyError:
                    check_for_duplicates[Ref_characteristics_to_object[cha]] = cha

            cont_while = False

    if not with_products:
        return set(Reaction_List)

    cont_while = True
    while cont_while:

        reaction = Reaction_List.pop(0)

        for i, product in enumerate(reaction.products):
            characteristics = product['characteristics']

            check_for_duplicates = {}
            for cha in characteristics:

                try:
                    old_cha = check_for_duplicates[Ref_characteristics_to_object[cha]]

                    # DEEP COPY DOES NOT WORK DIRECTLY, WE NEED TO CREATE A NEW OBJECT
                    reaction1 = copy_reaction(reaction)
                    reaction2 = copy_reaction(reaction)

                    reaction1.products[i]['characteristics'].remove(old_cha)
                    reaction2.products[i]['characteristics'].remove(cha)

                    Reaction_List.append(reaction1)
                    Reaction_List.append(reaction2)

                    break

                except KeyError:
                    check_for_duplicates[Ref_characteristics_to_object[cha]] = cha

            cont_while = False

    return set(Reaction_List)


def check_for_invalid_reactions(Reactions, Ref_characteristics_to_object):
    """
        Alternative to orthogonal reactions. Disallow ambiguous meaning
        Both will be left in the code to facilitate those who wish to change between then
    """
    for reaction in Reactions:
        for product in reaction.products:

            check_for_duplicates = {}
            for cha in product['characteristics']:

                # Ok I love try catches for checking if something is in a dict. Don't judge me
                try:
                    check_for_duplicates[Ref_characteristics_to_object[cha]]
                    raise TypeError('Illegal reaction, there is a product with multiple '
                                    'characteristics from the same Species referenced')
                except KeyError:
                    check_for_duplicates[Ref_characteristics_to_object[cha]] = cha


def construct_reactant_structures(reactant_species, Species_string_dict):
    species_string_combinations = []

    """=
        reactant_species: species objects of the involved species
        Species_string_dict : dictionary with species objects as keys and corresponding species strings
        
        Here we just find the corresponding strings according to the reactant species
        Pack then in a list and return
    """
    for reactant in reactant_species:
        species_string_combinations.append(extract_species_strings(reactant['object'],
                                                                   reactant['characteristics'], Species_string_dict))

    return species_string_combinations


def construct_order_structure(species_order_list, current_species_string_list):
    """
        Order structure for reaction order operations
        Here species are position in a dictionary where the key is the object and the item are the species strings
        in order of appearance in the dictionary
        This helps the implementation of the round_robin_structure

        # TODO Replace this - Put it in order
    """
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


def construct_single_reaction_for_sbml(reactant_species_string_list, product_species_string_list, reaction_rate):
    """
        Here we construct the reactions for SBML for the conversion by the model builder script
        It follows the following structure 're':[('stoichmetry', reactantant_string) ....
        The reaction rate must be a string containing the reaction kinetics here
        We return a single reaction to be appended by the Reactions_For_SBML dictionary
    """
    to_return = {'re': [], 'pr': [], 'kin': reaction_rate}

    reactant_count_dict = count_string_dictionary(reactant_species_string_list)
    product_count_dict = count_string_dictionary(product_species_string_list)

    for key in reactant_count_dict:
        to_return['re'].append((reactant_count_dict[key], key))

    for key in product_count_dict:
        to_return['pr'].append((product_count_dict[key], key))

    return to_return


def count_string_dictionary(list_of_strings):
    """
        Count the number of instances in a list and return them in a dictionary
        element: instances
    """
    to_return = {}

    for e in list_of_strings:
        try:
            to_return[e] += 1
        except KeyError:
            to_return[e] = 1

    return to_return


def extract_species_strings(species, characteristics, Species_string_dict):
    """
        Extract a species_string from the species string dictionary
        Uses the species object as key
        If the characteristics match with the string it is returned
    """
    species_strings_list = []
    species_strings_to_filter = set()

    species_strings_to_filter = species_strings_to_filter.union(Species_string_dict[species])

    for species_string in species_strings_to_filter:
        species_string_split = species_string.split('.')

        if all(char in species_string_split for char in characteristics):
            species_strings_list.append(species_string)

    return species_strings_list


def get_involved_species(reaction, Species_string_dict):
    """
        Extract all the involved species with a reaction
        This is done since reactions are defined through base species (by multiplication)
        We get all the species that have the base one in it's references
        We iterate through all to create all possible reactions
    """
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
                         Ref_characteristics_to_object,
                         type_of_model):
    Reactions_For_SBML = {}
    Parameters_For_SBML = {}

    Reactions = separate_into_orthogonal_reactions(Reactions, Ref_characteristics_to_object)
    check_for_invalid_reactions(Reactions, Ref_characteristics_to_object)

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
                    rate_string = fr.extract_reaction_rate(combination_of_reactant_species, reactant_string_list
                                                           , reaction.rate, Parameters_For_SBML, type_of_model)

                    Reactions_For_SBML['reaction_' + str(len(Reactions_For_SBML))] = \
                        construct_single_reaction_for_sbml(reactant_string_list, product_string_list, rate_string)

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
