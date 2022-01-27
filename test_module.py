from meta_class import *

if __name__ == '__main__':

    Age, Mood, Live, Phage, Infection = Create(5)

    # Rate test
    def rate(x):
        if x.happy:
            return 10
        else:
            return 5


    Age.young >> Age.old [rate]
    Mood.sad >> Mood.happy [5]
    Human = Age * Mood
    Human + Phage >> S0 [10]
    Human(200)  # Human.young.sad.live
    Simulator.compile(Human | Phage, globals(), type_of_model='stochastic')