from mobspy import *

# TODO discuss jupiter double reaction issue
# TODO potential change
if __name__ == '__main__':

    A1, B1, C1, D1, X = Create(5)

    for a in ['b', 'c', 'd']:
        A1.c(a) + B1 >> Zero[23]
    print(A1.get_characteristics())
    exit()

    A1(100) + B1(200) >> C1 + D1[0.01]

    My_Model = Simulation(A1 | B1 | C1 | D1, globals())
    My_Model.configure_parameters_from_json('./parameters/example_parameters.json')
    My_Model.run()
    exit()

    def infection(r1):
        if r1.old:
            return 0.02
        else:
            return 0.01

    Age, Infection, Virus = Create(3)
    Age.young >> Age.old [0.5]
    Default_RR[Infection.not_infected + Virus >> Infection.infected [infection]]
    Bacteria = Age*Infection
    Bacteria(100), Virus(300)
    my_simulation = Simulation(Bacteria | Virus, globals())
    my_simulation.Parameters['simulation_method'] = 'stochastic'
    my_simulation.Parameters['plot'] = False
    my_simulation.run()
    my_simulation.plot_stochastic()
    exit()



    # def hi(**kargs):
    #   a = kargs.get('a')
    #    b = kargs.get('b')
    #    print(a, b)

    # hi(a=10, b=None)