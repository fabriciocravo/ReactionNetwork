
def time_series_average(list_series):

    '''
    :param list_series: a list of all time series to calculate the average
    :return: a single series with average value for each time
    '''

    average_series = []
    for j in range(len(list_series[0])):

        add = 0
        try:
            for series in list_series:
                add = add + series[j]

        except KeyError:
            raise ValueError('The time_series_average function was programed for same size time series')

        average_series.append(add/len(list_series))

    return average_series


def standard_deviation(list_series):

    '''
    :param list_series: a list of all time series to calculate the standard deviation
    :return: the standard deviation per time value
    '''

    average_series = time_series_average(list_series)
    deviation_series = []

    for j in range(len(list_series[0])):

        add = 0
        try:
            for series in list_series:
                add = add + (average_series[j] - series[j])**2

        except KeyError:
            raise ValueError('The time_series_average function was programed for same size time series')

        deviation_series.append(add/len(list_series))

    return deviation_series