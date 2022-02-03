from mobspy import *

# TODO discuss jupiter double reaction issue
# TODO potential change
if __name__ == '__main__':

    # A1, B1, C1, D1 = Create(4)
    # A1(100) + B1(200) >> C1 + D1[0.01]
    # My_Model = MobsPy(A1 | B1 | C1 | D1, globals())
    # My_Model.Parameters['simulation_method'] = 'stochastic'
    # My_Model.compile()
    # exit()

    def infection(r1, r2):
        if r1.old:
            return 0.02
        else:
            return 0.01

    Age, Infection, Virus = Create(3)
    Age.young >> Age.old [0.5]
    Infection.not_infected + Virus >> Infection.infected [infection]
    Bacteria = Age*Infection
    Bacteria(100), Virus(300)
    My_Model = MobsPy(Bacteria | Virus, globals())
    My_Model.Parameters['simulation_method'] = 'stochastic'
    My_Model.run()
    exit()



    # def hi(**kargs):
    #   a = kargs.get('a')
    #    b = kargs.get('b')
    #    print(a, b)

    # hi(a=10, b=None)