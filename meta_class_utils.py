import copy


def unite_dictionaries(first_dict, second_dict):
    for key in second_dict:
        try:
            first_dict[key].union(second_dict[key])
        except KeyError:
            first_dict[key] = second_dict[key]


def combine_references(species1, species2):
    return species1.get_references().union(species2.get_references())


def check_orthogonality_between_references(references):

    for i, reference1 in enumerate(references):
        for j, reference2 in enumerate(references):

            if i == j:
                continue

            if len(reference1.get_characteristics().intersection(reference2.get_characteristics())) != 0:
                raise TypeError('A characteristic must be unique between different base properties')


def complete_characteristics_with_first_values(spe_object, characteristics, characteristics_to_object):

    if characteristics == 'std$':
        characteristics = set()

    vector_elements = {}
    for cha in characteristics:
        vector = characteristics_to_object[cha]
        if vector in vector_elements:
            raise TypeError('The assignment refers to multiple strings')
        else:
            vector_elements[vector] = True

    first_characteristics = set()
    for reference in spe_object.get_references() - set(vector_elements.keys()):
        if reference.first_characteristic:
            first_characteristics.add(reference.first_characteristic)

    return {spe_object.get_name()}.union(first_characteristics).union(characteristics)


def extract_characteristics_from_string(species_string):
    return set(species_string.split('.'))


def turn_set_into_0_value_dict(set):
    to_return = {}
    for e in set:
        to_return[e] = 0
    return to_return


def unite_characteristics(species):
    '''
        This function checks if there are repeated characteristics in the model
    :param species: All species added to the model
    ;return: characteristics
    '''
    characteristics = set()

    if species is not None:
        for spe in species:
            characteristics = characteristics.union(spe.get_characteristics())

    return characteristics


def extract_characteristics(spe):

    lists_of_characteristics = []
    for reference in spe.get_references():
        lists_of_characteristics.append(reference.get_characteristics())

    return lists_of_characteristics


def add_negative_complement_to_characteristics(species):
    '''
    :param species: all the species involved in the simulation

        Here we check if any of the species has a unique characteristic assigned to it
        We assign a negative to refer to the state without that characteristic
        We do so by adding not$ to it
        We check later for repeated characteristics
        This is defined to be able to reference all object states later
    '''
    for spe in species:
        if len(spe.get_characteristics()) == 1:
            cha = list(spe.get_characteristics())[0]
            spe.add_characteristic('not$' + cha)


def create_orthogonal_vector_structure(species):
    '''
    :param species: All species used in the model
    :return: Two hashes one that references objects to characteristics
            and other that references characteristics to objects

            Here we create the basis of the orthogonal vector structure
            Each base property object must contain a set of independent characteristics
            We think of it as properties being unity vectors in a cartesian coordinate system
            And the characteristics as values

            We use the dictionary structure to easily define the reactions as being transformations
            within the same unity vector
    '''
    Ref_characteristics_to_object = {}
    Ref_object_to_characteristics = {}

    for spe in species:
        for prop in spe.get_references():
            Ref_object_to_characteristics[prop] = prop.get_characteristics()

    for spe in species:
        for prop in spe.get_references():
            for cha in prop.get_characteristics():

                if cha not in Ref_characteristics_to_object:
                    Ref_characteristics_to_object[cha] = prop
                else:
                    raise TypeError('Characteristics must be unique for modeling properties')

    return Ref_object_to_characteristics, Ref_characteristics_to_object


def create_species_strings(spe_object, lists_of_definitions):

    # Remove empty sets from the list
    lists_of_definitions = [i for i in lists_of_definitions if i != set()]

    # Defining needed structures
    set_of_species = set()
    accumulated_list = [spe_object.get_name()]
    species_from_characteristic = {}

    # Recursive exponential combination implementation
    def recursive_combine_properties(i, list_definitions, accumulated_list):

        for j, characteristic in enumerate(list_definitions):

            if j == 0:
                accumulated_list.append(characteristic)
            else:
                accumulated_list[-1] = characteristic

            try:
                recursive_combine_properties(i + 1, lists_of_definitions[i + 1], copy.deepcopy(accumulated_list))
            except IndexError:
                spe = '.'.join(accumulated_list)
                set_of_species.add(spe)

    recursive_combine_properties(0, lists_of_definitions[0], accumulated_list)

    return set_of_species


if __name__ == '__main__':
    pass
