
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


if __name__ == '__main__':
    print(deterministic_string('Human', 3))

