import plot_scripts.statistics_calculations as sc
from copy import deepcopy
import plot_scripts.hierarchical_plot as hp
import json
import simulation_logging.log_scripts as simlog


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
            simlog.error(f'Error while decoding json file "{plot_json_filename}".')

    return json_data


def stochastic_plot(species, data, plot_params):
    data_to_plot = deepcopy(data)
    new_plot_params = deepcopy(plot_params)

    new_plot_params['figures'] = []
    new_plot_params['xlabel'] = 'Time'
    new_plot_params['pad'] = 1.5
    color_cycler = hp.Color_cycle()
    for spe in species:
        # We define new 'mappings' with the resulting runs for the statics for the plot structure
        try:
            plots_for_spe_i = []
            plots_for_spe_i_sta = []
            for i, time_series in enumerate(data):
                if len(time_series) == 1:
                    i = ''

                processed_runs = sc.average_plus_standard_deviation(time_series[spe]['runs'])
                key_average = spe + '$' + 'average'
                key_dev = spe + '$' + 'deviation'
                data_to_plot[i][key_average] = {'runs': [processed_runs[0]]}
                data_to_plot[i][key_dev] =  {'runs': [processed_runs[1], processed_runs[2]]}

                # We define the standard plot for the average and deviation
                color = color_cycler(1)
                plots_for_spe_i.append({'species_to_plot': [spe], 'time_series': i + 1,
                                        spe: {'color': color, 'label': spe + str(i + 1)}})

                plots_for_spe_i_sta.append({'species_to_plot': [key_average], 'time_series': i + 1,
                                            key_average: {'color': color, 'linestyle': '-', 'label': 'avg' + str(i + 1)}})
                plots_for_spe_i_sta.append({'species_to_plot': [key_dev], 'time_series': i + 1,
                                            key_dev: {'color': color, 'linestyle': ':', 'label': 'dev' + str(i + 1)}})
        except KeyError:
            simlog.error(f'{spe} species not found in data')
        new_plot_params['figures'].append({'plots': plots_for_spe_i })
        new_plot_params['figures'].append({'plots': plots_for_spe_i_sta})

    hp.plot_data(data_to_plot, new_plot_params)


def deterministic_plot(species, data, plot_params):
    new_plot_params = deepcopy(plot_params)
    new_plot_params['xlabel'] = 'Time'
    new_plot_params['ylabel'] = 'Concentration'
    new_plot_params['species_to_plot'] = species
    color_cycler = hp.Color_cycle()
    for spe in species:
        new_plot_params[spe] = {'label': spe, 'color': color_cycler(1)}
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
        simlog.error('Raw plot only takes json files or parameters for configuration')
    hp.plot_data(data, plot_params)


if __name__ == '__main__':
    raw_plot({}, 'default_parameters.json')
