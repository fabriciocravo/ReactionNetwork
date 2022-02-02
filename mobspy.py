import Modules.meta_class
import SBML_simulator.run
from Modules.meta_class import *
from parameter_scripts import parameter_reader as pr
from SBML_simulator import builder, util
from plot_scripts.hierarchical_plot import get_plot_params, plot_data

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
            self.Parameters = pr.read_json(current_directory + '/parameters/default_parameters.json')

        if not plot_parameters:
            self.Plot_Parameters = get_plot_params(current_directory + '/plot_params/default_plot.json')

        self._Species_for_SBML, self._Reactions_For_SBML, \
        self._Parameters_For_SBML, self._Mappings_for_SBML = Compiler.compile(model, names=names,
                                                                              volume_ml=self.Parameters['volume_ml'],
                                                                              type_of_model=self.Parameters["simulation_method"],
                                                                              verbose=False)

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
            self.Plot_Parameters['mode'] = 'deterministic'
        elif self.Parameters['simulation_method'].lower() == 'stochastic':
            self.Plot_Parameters['mode'] = 'stochastic'

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
            plot_data(self.Data['data'], self.Data['mappings'], self.Plot_Parameters)


if __name__ == '__main__':

    Mortal = Create(1)
    Model = MobsPy(Mortal)
    exit()

    A, B, C, D = Create(4)
    A(100) + B(200) >> C + D [0.1]
    My_Model = MobsPy(A | B | C | D, globals())
    My_Model.Parameters['simulation_method'] = 'stochastic'
    My_Model.run()
