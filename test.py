from mobspy import *

if __name__ == '__main__':

    A, B, C, D = Create(4)
    A(100) + B(200) >> C + D[0.1]
    My_Model = MobsPy(A | B | C | D, globals())
    My_Model.Parameters['simulation_method'] = 'stochastic'
    My_Model.run()