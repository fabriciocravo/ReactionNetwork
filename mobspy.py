import Modules.meta_class
import SBML_simulator.run
from Modules.meta_class import *
from parameter_scripts import parameter_reader as pr
from parameters.default_reader import get_default_parameters
from plot_params.default_plot_reader import get_default_plot_parameters
from SBML_simulator import builder, util
import plot_scripts.default_plots as dp

import os


class MobsPy:

    def __init__(self, model, names=None, parameters=None, plot_parameters=None):
        """
            This part of the code just creates a model
        :param model: Species or Parallel species object instance for modeling
        :param names: Names of the variables. Set to globals() for easy naming
        :param parameters: Parameters for a Model
        :param plot_parameters: Plot parameters for plotting
        """

        current_directory = os.getcwd()
        self.Model = model

        if not isinstance(model, Species) and not isinstance(model, ParallelSpecies):
            raise TypeError('Model must be formed by Species objects')

        if not parameters:
            self.Parameters = get_default_parameters()

        if not plot_parameters:
            self.Plot_Parameters = get_default_plot_parameters()

        self._Species_for_SBML, self._Reactions_For_SBML, \
        print('Compiling model')
        self._Parameters_For_SBML, self._Mappings_for_SBML = Compiler.compile(model, names=names,
                                                                              volume_ml=self.Parameters['volume_ml'],
                                                                              type_of_model=self.Parameters["simulation_method"],
                                                                              verbose=False)
        print('Model compiled successfully')

        # Other needed things for simulating
        self.SBML_string = None
        self.Data = None

    def run(self):
        """
            Just calls the simulator part of the codes for running
        :return: nothing, data is saved automaticaly or in self.Data
        """
        # We process the parameters here in case there were updates
        pr.parameter_process(self.Parameters, self._Mappings_for_SBML, self._Parameters_For_SBML)
        if self.Parameters['simulation_method'].lower() == 'deterministic':
            self.Parameters['repetitions'] = 1
            self.Plot_Parameters['simulation_method'] = 'deterministic'
        elif self.Parameters['simulation_method'].lower() == 'stochastic':
            self.Plot_Parameters['simulation_method'] = 'stochastic'

        print('Starting Simulator')
        self.SBML_string = builder.build(self._Species_for_SBML,
                                         self._Parameters_For_SBML,
                                         self._Reactions_For_SBML)
        self.Data = SBML_simulator.run.simulate(self.SBML_string, self.Parameters, self._Mappings_for_SBML)

        if self.Parameters['save_data']:
            print("Saving data (reason: parameter <save_data>)")
            pickled = {'data': self.Data,
                       'mappings': self._Mappings_for_SBML,
                       'params': self.Parameters}
            # Save pickle data
            # TODO Add error here
            if not os.path.isdir(self.Parameters['output_absolute_directory']):
                print("Creating output directory: %s..." % (self.Parameters['output_absolute_directory']))
                os.makedirs(self.Parameters['output_absolute_directory'], exist_ok=True)
            util.pickle_it(pickled, self.Parameters['output_absolute_file'])

        if self.Parameters['plot']:
            pass

        else:
            print("WARNING: NOT saving data (reason: parameter <save_data>)")

        if self.Parameters['plot']:
            if self.Plot_Parameters['simulation_method'] == 'stochastic':
                self.plot_stochastic()
            elif self.Plot_Parameters['simulation_method'] == 'deterministic':
                self.plot_deterministic()

    def extract_plot_essentials(self, species = None, data = None, plot_params = None):
        if species is None:
            species = list(self._Mappings_for_SBML.keys())
        if data is None:
            data = self.Data['data']
        if plot_params is None:
            plot_params = self.Plot_Parameters
        return species, data, plot_params

    # Plotting encapsulation
    def plot_stochastic(self, species = None, data = None, plot_params = None):
        plot_essentials = self.extract_plot_essentials(species, data, plot_params)
        dp.stochastic_plot(plot_essentials[0], plot_essentials[1], plot_essentials[2])

    def plot_deterministic(self, species = None, data = None, plot_params = None):
        plot_essentials = self.extract_plot_essentials(species, data, plot_params)
        dp.deterministic_plot(plot_essentials[0], plot_essentials[1], plot_essentials[2])

    def plot_raw(self, parameters_or_file):
        dp.raw_plot(self.Data['data'], parameters_or_file)


if __name__ == '__main__':

    A, B, C, D = Create(4)
    A(100) + B(200) >> C + D [0.1]
    My_Model = MobsPy(A | B | C | D, globals())
    My_Model.Parameters['simulation_method'] = 'stochastic'
    My_Model.run()
