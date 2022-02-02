from parameter_scripts.parameter_reader import read_json


# This was just created to avoid potential directory compatibilities
def get_default_plot_parameters():
    return read_json('plot_params/default_plot.json')
