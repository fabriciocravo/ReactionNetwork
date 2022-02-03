import plot_scripts.statistics_calculations as sc
from copy import deepcopy
import plot_scripts.hierarchical_plot as hp
import json


def read_plot_json(plot_json_filename):
    """
    In:
      plot_json_filename: json file name

    Returns:
      plot parameter dictionary
    """
    with open(plot_json_filename, 'r') as file:
        try:
            json_data = json.load(file)
        except Exception:
            raise ValueError(f'Error while decoding json file "{plot_json_filename}".')

    return json_data


def stochastic_plot(species, data, plot_params):
    new_data = {'Time': data['Time']}
    new_plot_params = deepcopy(plot_params)

    new_plot_params['figures'] = []
    new_plot_params['xlabel'] = 'Time'
    new_plot_params['pad'] = 1.5
    for spe in species:
        processed_runs = sc.average_plus_standard_deviation(data[spe]['runs'])

        # We define new 'mappings' with the resulting runs for the statics for the plot structure
        key_average = spe + '$' + 'average'
        new_data[spe] = data[spe]
        new_data[key_average] = {'runs': [processed_runs[0]]}
        key_dev = spe + '$' + 'deviation'
        new_data[key_dev] = {'runs': [processed_runs[1], processed_runs[2]]}

        # We define the standard plot for the average and deviation
        color = hp.color_cycle()
        new_plot_params[spe] = {'color': color}
        new_plot_params[key_average] = {'color': color, 'linestyle': '-'}
        new_plot_params[key_dev] = {'color': color, 'linestyle': ':'}
        new_plot_params['figures'].append({'species_to_plot': [spe],
                                           spe: {'color': color},
                                           'ylabel': str(spe) + ' runs'})
        new_plot_params['figures'].append({'plots': [{'species_to_plot': [key_average]},
                                                     {'species_to_plot': [key_dev]}],
                                           'ylabel': str(spe) + ' average'})

    hp.plot_data(new_data, new_plot_params)


def deterministic_plot(species, data, plot_params):
    new_plot_params = deepcopy(plot_params)
    new_plot_params['xlabel'] = 'Time'
    new_plot_params['ylabel'] = 'Concentration'
    new_plot_params['species_to_plot'] = species
    for spe in species:
        new_plot_params[spe] = {'label': spe}
    hp.plot_data(data, new_plot_params)


def raw_plot(data, parameters_or_file):
    """
            Plots data from a json or parameter dictionary configured according to the hierarchical plot structure
        data: data points
        parameters_or_file: .json file name or python dictionary
    """
    if type(parameters_or_file) == str and parameters_or_file[-5:] == '.json':
        plot_params = read_plot_json(parameters_or_file)
    elif type(parameters_or_file) == dict:
        plot_params = parameters_or_file
    else:
        raise TypeError('Raw plot only takes json files or parameters for configuration')
    hp.plot_data(data, plot_params)


if __name__ == '__main__':
    raw_plot({}, 'default_parameters.json')