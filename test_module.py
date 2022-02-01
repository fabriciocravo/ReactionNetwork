from meta_class import *

# TODO sad going to sad
# TODO Talk to Thomas and Mathias
if __name__ == '__main__':

    Ager, Mood, Live, Phage, Food = Create(5)

    def eating(r1):
        if r1.young:
            return 20
        else:
            return 10

    # TODO fix this
    Ager.young >> Ager.old [10]
    Food.hungry >> Food.satified [eating]
    Bacteria = Ager*Food
    Bacteria + Phage >> S0 [10]
    Ecoli = Bacteria*S1
    LactoBasil = Bacteria*S1
    Simulator.compile(Ecoli| LactoBasil | Phage, globals(), type_of_model='deterministic')
    
    exit()












    print('Model one')
    Age, Mood = Create(2)


    # Rate test
    def rate(x):
        if x.happy:
            return 10
        else:
            return 5

    Mood.sad >> Mood.happy [10]
    Age.young >> Age.old [rate]
    Default_RR[ S0 >> Age [20] ]
    Human = Age*Mood
    Simulator.compile(Human, globals(), type_of_model='stochastic')

    print('\n \n \n \n')

    print('Model two')
    Age, Mood = Create(2)

    Mood.sad >> Mood.happy[10]
    Age.young >> Age.old[rate]
    S0 >> Age[20]
    Human = Age * Mood

    Simulator.compile(Human, globals(), type_of_model='stochastic')

    print('\n \n \n \n')





