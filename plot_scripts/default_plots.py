import plot_scripts.statistics_calculations as sc
from copy import deepcopy
import plot_scripts.hierarchical_plot as hp


def stochastic_plot(species, data, plot_params):

    print(data)
    new_data = {'Time': data['Time']}
    new_mappings = []
    new_plot_params = deepcopy(plot_params)

    new_plot_params['figures'] = []
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
        new_plot_params['figures'].append({'species_to_plot': [spe], spe: {'color': color}})
        new_plot_params['figures'].append({'plots': [{'species_to_plot': [key_average]},
                                                     {'species_to_plot': [key_dev]}]})

        # We add the new keys to the mapping. Since we use the keys to plot from the data
        new_mappings.append(spe)
        new_mappings.append(key_average)
        new_mappings.append(key_dev)

    hp.plot_data(new_data, new_mappings, new_plot_params)


def deterministic_plot(species, data, plot_params):
    pass
