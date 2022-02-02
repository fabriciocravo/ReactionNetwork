import json
import sys
from datetime import datetime
import os
from pathlib import Path


def read_json(json_file_name):
    """
    In:
      plot_json_filename: json file name

    Returns:
      plot parameter dictionary
    """
    with open(json_file_name, 'r') as file:
        try:
            json_data = json.load(file)
        except json.decoder.JSONDecodeError as e:
            # logging_array[0].error(f'Error while decoding json file "{plot_json_filename}".')
            # logging_array[0].error(f'{e}')
            # logging_array[0].error(f'File content:\n{file.read()}', level='error')
            raise TypeError('Error reading file')
            exit(1)

    return json_data


def __set_standard_duration(params, params_for_sbml):

    if params['duration'] is None:
        max_rate = 0
        for p in params_for_sbml:
            rate = params_for_sbml[p][0]
            if rate > max_rate:
                max_rate = rate
        params['duration'] = 5 * max_rate


def __name_output_file(params, mappings):

    if params['output_dir'][0] == '/':
        params['output_dir'] = params['output_dir'][1:]

    main_directory = os.path.abspath(sys.modules['__main__'].__file__)
    save_dir = os.path.join(Path(main_directory).parent.absolute(), params['output_dir'])

    if params['output_file'] is None:
        file_name = "r"
        for species in mappings:
            file_name += '_' + str(species)
        file_name += ' ' + str(datetime.now()) + '.pkl'
    else:
        file_name = params['output_file']

    params['output_absolute_directory'] = save_dir
    params['output_absolute_file'] = os.path.join(params['output_absolute_directory'], file_name)


def parameter_process(params, mappings, params_for_sbml):
    __set_standard_duration(params, params_for_sbml)
    __name_output_file(params, mappings)
