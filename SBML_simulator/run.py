import basico
import os
from SBML_simulator import util
from joblib import Parallel, delayed


def simulate(sbml_str, params, mappings):
    """
        This function coordinates the simulation by calling the necessary jobs
        In the future we hope to implement parallel cluster computing compatibility
    :param sbml_str: SBML file for running the Copasi simulator
    :param mappings: Mappings that sum to the same species
    :param params: simulation parameters from the text file
    :return: COPASI simulated data
    """

    # Run in parallel or sequentially
    # If nothing is specified just run it in parallel
    try:
        if params["jobs"] == 1:
            print("Running simulation sequentially")
            jobs = params["jobs"]
        else:
            print("Running simulation in parallel")
            jobs = params["jobs"]
    except KeyError:
        print("Running simulation in parallel")
        jobs = -1

    # TODO: If cluster compatibility is added I suggest here
    data = job_execution(sbml_str, params, jobs)
    data = remap_species(data, mappings)

    print("Simulation is Over")
    return {'data': data, 'params': params, 'mappings': mappings}


def job_execution(sbml_str, params, jobs):
    # This is defined for parallelism purposes
    # THERE MUST BE ONE TEMP DIRECTORY FOR EVERY COPASI FILE
    # OTHERWISE PARALLELISM DOES NOT WORK - COPASI OVERWRITES THE OUTPUT
    def __single_run(packed):
        sbml_str, i = packed
        basico.model_io.load_model_from_string(sbml_str)

        data = basico.run_time_course(params['duration'],
                                      method=params["simulation_method"].lower(),
                                      start_time=params["start_time"])

        reformated_data = reformat_time_series(data)

        return reformated_data

    parallel_data = Parallel(n_jobs=jobs)(delayed(__single_run)((sbml_str, i)) for i in range(params['repetitions']))

    if not parallel_data:
        raise TypeError("Error: The parallel model has not produced an output." +
                        "Try addding ('sequential': True) to parameters")

    # We always call merge to keep the data in the format we want
    merged_data = merge(params, parallel_data)

    return merged_data


def reformat_time_series(data):
    data_dict = {'Time': data.index.tolist()}

    for key in data:
        data_dict[key.replace('_dot_', '.')] = list(data[key])

    return data_dict


def merge(params, data):
    """
    a basic merge of the data with possible resampling in time to save less data

    params: dict of parameters
    data:   Array of single runs: data[0], data[1], ...

    returns: Data merged in a dictionary with all time series from all experiments
                separated by species and mapping
    """

    for i in range(1, len(data)):
        assert (data[i - 1]['Time'] == data[i]['Time'])  # should be set at exact same times

    merged_data = {'Time': data[0]['Time']}
    for key in data[0].keys():
        if key not in ['Time']:
            merged_data[key] = {'runs': [data[i][key]
                                         for i in range(params["repetitions"])]}

    return merged_data


def remap_species(data, mapping):
    """
    Takes the simulated species (data) and add ones defined by
    mapping (mapping).

    By default, a mapping is a list of species in which case the
    sum is taken: ['a', 'b', ...]
    """

    mapped_data = {'Time': data['Time']}
    T = range(len(data['Time']))

    # copy over all unmapped ones
    for k in data.keys():
        mapped_data[k] = data[k]

    # 1st pass with sum mappings
    for group in mapping.keys():
        the_mapping = mapping[group]
        mapped_data[group] = {'runs': []}

        try:
            # check if is a list -> sum
            if type(the_mapping) is list:

                for run in range(len(data[k]['runs'])):
                    species = the_mapping
                    mapped_data[group]['runs'].append([sum([data[species[i]]['runs'][run][t]
                                                            for i in range(len(species))]) for t in T])

        except Exception:
            raise ValueError(f'run: remap_species: error when remapping "{the_mapping}".' +
                             'Possible fix: All runs must have the same time')

    return mapped_data
