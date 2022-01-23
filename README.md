# INTRODUCTION

This is the main code responsible for constructing the necessary tools for the creation of a model. The paper explains the base structure in detail but I will give a brief introduction here. Also, please look at the example models.

The model consists of combining base species through multiplication to create more complex ones. Each base species can only contain one set of characteristics and they will be used as a base for the reactions.

To create more complex species one must use multiplication. This way the species will "inherit" all sets of characteristics from the previous species. It is important to say that the characteristics will not be directly added to the more complex species set, but instead, the more complex species will point to the ones that construct it using a set of references. Moreover, each species points to itself. Therefore it will have a number of sets of characteristics associated with it equal to the number of elements multiplied to form it + one (itself).

The sets must be independent, which means that all sets of characteristics must not contain a characteristic in common.

To add characteristics just use Species_Object. characteristic, if it has never been used it will be added to the object. For reactions - Just type Species_Base.characteristics + Species_base ... >> Species_base. Once the model compiles all species that have been created for this base species will be considered in the reaction. This works for more complex species and reactions.

Regarding the reactants, the dot is used to filter what characteristics will be present on the reactants species. For the products, this will be the characteristic to be transformed. Wich means that all characteristics that belong to the same set will be transformed into it.

# SCRIPT meta_class.py

Create - creates multiple instances of the species objects

Species - Species Object creator. It stores everything needed for a simulation to occur. If contains:

	self._name - Name of the species. It is initially named as the number of instances, but it is automatically named to the variable name after the model is compiled
	self._characteristics - The set of characteristics of this species object
	self._references - If created by multiplication all the species multiplied to create it. If complex species are multiplied ALL the references will be combined here
	self.first_characteristic - First, characteristic added to the species - Used for quantity setting
	self._reactions - All the reactions the species is inside of
self._species_counts - Initial values or concentrations

Reacting_Species - If a species is involved in an operation for a reaction it automatically creates an object of this class. The objects of this class combine to form reactions.

Reactions - The reactions themselves with reactants and products

Simulator - The model compiler that prepares everything for the conversion into an SBML file in future scripts

ParallelSpecies - Used if several species want to be simulated in Parallel

# SCRIPT meta_class_utils.py

Contains functions used by the meta_class to construct the string species combinations and other structures necessary for the SBML file. Species objects represent multiple strings that will be used in the SBML file. Each species object creates around 2^n strings containing all combinations of characteristics possible ( so you don't have to write this exponential monster by yourself )

Also, this constructs the orthogonal vector structure. These are simply two dictionaries where the species point to their set of characteristics and each characteristic point to their species. This is used to easily transform species strings for reactions.

# SCRIPT reaction_construction_nb.py

This contains all the functions necessary for constructing the reactions that will be converted to strings for the SBML document. It processes all the user's inputs to create an exponentially complex number of reactions according to their commands

# SCRIPT order_operators.py (advanced) ]

This allows the user to edit the assignment of string species strings transformations so it does not follow any of the base types proposed in the paper. To explain it briefly take the following model:

Age.young >> Age.old
Mood.sad >> Mood.happy
Human = Age*Mood
2*Human >> Human

Here we have a reaction where only one of the humans survives due to competition. We take a round-robin approach to determine which one will survive (which means the first one will). Reaction operators allow us to change that default order.

# SCRIPT function_rate_code.py

Instead of assigning integers, the user can assign functions to the reactions so that the rate will depend on the characteristics of the reactants. This is the code responsible for that

