import copy


def combine_properties(name, lists_of_definitions):

    set_of_species = set()
    accumulated_list = [name]

    def recursive_combine_properties(i, list_definitions, accumulated_list):

        for j, characteristic in enumerate(list_definitions):

            if j == 0:
                accumulated_list.append(characteristic)
            else:
                accumulated_list[-1] = characteristic

            try:
                recursive_combine_properties(i + 1, lists_of_definitions[i + 1], copy.deepcopy(accumulated_list))
            except IndexError:
                set_of_species.add('.'.join(accumulated_list))

    recursive_combine_properties(0, lists_of_definitions[0], accumulated_list)

    return set_of_species


if __name__ == '__main__':

    print(combine_properties('Ecoli', [['young', 'old'],['green', 'red'], ['deja', 'vu']]))

