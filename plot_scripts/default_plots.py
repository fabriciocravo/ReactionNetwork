import statistics


def stochastic_plot(data, mappings, plot_params):

    for key in data:
        print(key, data[key])
    exit()

    new_data = {'Time': data['Time']}
    for map in mappings:
        # print(data[map]['runs'][0])
        # print(data[map]['runs'][1])
        # print(data[map]['runs'][2])

        key = map + '$' + 'statistics'
        new_data[map] = data[map]
        new_data[key] = {'runs': statistics.time_series_average(data[map])}

        exit()