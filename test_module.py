from meta_class import *

if __name__ == '__main__':

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





