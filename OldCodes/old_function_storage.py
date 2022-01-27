
def separate_into_orthogonal_reactions(Reactions, Ref_characteristics_to_object, with_products = False):
    """
        This function separates reactions into completely orthogonal ones
        For instance, lets say red and blue belong to the same set of Species Characteristics

        Age.young >> Age.old [3]
        Mood.sad >> Mood.happy [5]
        Human = Age*Mood
        Human.blue.yellow >> Human.red  [20]

        This would mean Human.blue >> Human.red and Human.yellow >> Human.red
        This function creates two new reaction objects with that
        This function was designed so a user can reference multiple characteristics from the same Species
        To group reactions

        It does by transforming the reactions in a list and reading two reactions if there is ever
        a reference to two characteristics that belong to the same Species

        It works in a similar fashion for products. Generating both reactions
    """
    Reaction_List = list(Reactions)

    cont_while = True
    while cont_while:

        reaction = Reaction_List.pop(0)

        for i, reactant in enumerate(reaction.reactants):
            characteristics = reactant['characteristics']

            check_for_duplicates = {}
            for cha in characteristics:

                try:
                    old_cha = check_for_duplicates[Ref_characteristics_to_object[cha]]

                    # DEEP COPY DOES NOT WORK DIRECTLY, WE NEED TO CREATE A NEW OBJECT
                    reaction1 = copy_reaction(reaction)
                    reaction2 = copy_reaction(reaction)

                    reaction1.reactants[i]['characteristics'].remove(old_cha)
                    reaction2.reactants[i]['characteristics'].remove(cha)

                    Reaction_List.append(reaction1)
                    Reaction_List.append(reaction2)

                    break

                except KeyError:
                    check_for_duplicates[Ref_characteristics_to_object[cha]] = cha

            cont_while = False

    if not with_products:
        return set(Reaction_List)

    cont_while = True
    while cont_while:

        reaction = Reaction_List.pop(0)

        for i, product in enumerate(reaction.products):
            characteristics = product['characteristics']

            check_for_duplicates = {}
            for cha in characteristics:

                try:
                    old_cha = check_for_duplicates[Ref_characteristics_to_object[cha]]

                    # DEEP COPY DOES NOT WORK DIRECTLY, WE NEED TO CREATE A NEW OBJECT
                    reaction1 = copy_reaction(reaction)
                    reaction2 = copy_reaction(reaction)

                    reaction1.products[i]['characteristics'].remove(old_cha)
                    reaction2.products[i]['characteristics'].remove(cha)

                    Reaction_List.append(reaction1)
                    Reaction_List.append(reaction2)

                    break

                except KeyError:
                    check_for_duplicates[Ref_characteristics_to_object[cha]] = cha

            cont_while = False

    return set(Reaction_List)
