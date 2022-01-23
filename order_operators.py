from copy import deepcopy
import meta_class_utils


class __Operator_Base:

    # Assign order structure
    def __getitem__(self, item):
        item.order = self

    # Transform product function
    @staticmethod
    def transform_species_string(species_string, characteristics_to_transform,
                                 ref_object_to_characteristics,
                                 ref_characteristics_to_object):

        species_to_return = deepcopy(species_string)
        for characteristic in characteristics_to_transform:
            replaceable_characteristics = ref_object_to_characteristics[ref_characteristics_to_object[characteristic]]

            for rep_cha in replaceable_characteristics:
                species_to_return = species_to_return.replace('.' + rep_cha, '.' + characteristic)

        return species_to_return

    @staticmethod
    def find_all_string_references_to_born_species(species, characteristics, Species_string_dictionary):
        to_return = []
        for key in Species_string_dictionary:
            if species in key.get_references():
                for species_string in Species_string_dictionary[key]:
                    species_string_split = species_string.split('.')
                    if all(char in species_string_split for char in characteristics):
                        to_return.append(species_string)
        return to_return

    @staticmethod
    def find_all_default_references_to_born_species(species, characteristics, Species_string_dictionary,
                                                    Ref_object_to_characteristics,
                                                    Ref_characteristics_to_object):
        to_return = []

        characteristics_to_find = meta_class_utils.complete_characteristics_with_first_values(species, characteristics,
                                                                                            Ref_characteristics_to_object)
        characteristics_to_find.remove(species.get_name())
        characteristics_to_find.union(characteristics)

        for key in Species_string_dictionary:
            if species in key.get_references():
                for species_string in Species_string_dictionary[key]:
                    species_string_split = species_string.split('.')
                    if all(char in species_string_split for char in characteristics_to_find):
                        to_return.append(species_string)

        return to_return


class __Round_Robin_Base(__Operator_Base):

    def __call__(self, order_dictionary, product_species,
                 Species_string_dictionary,
                 Ref_object_to_characteristics,
                 Ref_characteristics_to_object):

        round_robin_index = {}
        for species in [e['species'] for e in product_species]:
            round_robin_index[species] = 0

        products = []
        for species, characteristics in [(e['species'], e['characteristics']) for e in product_species]:

            # Simple round robin
            try:
                species_to_transform_string = order_dictionary[species][round_robin_index[species]]
                round_robin_index[species] = (round_robin_index[species] + 1) % len(order_dictionary[species])

                # Return in list of lists format for combination later
                products.append([self.transform_species_string(species_to_transform_string, characteristics,
                                                               Ref_object_to_characteristics,
                                                               Ref_characteristics_to_object)])

            # If the species is not on the reactants - order_dictionary
            except KeyError:
                products.append(self.find_all_string_references_to_born_species(species,
                                                                                characteristics,
                                                                                Species_string_dictionary))

        return products


# Define class to override the operators
Round_Robin_RO = __Round_Robin_Base()


class __RR_Default_Base(__Operator_Base):

    # Here is the default order requested by Thomas
    def __call__(self, order_dictionary, product_species,
                 Species_string_dictionary,
                 Ref_object_to_characteristics,
                 Ref_characteristics_to_object):

        round_robin_index = {}
        for species in [e['species'] for e in product_species]:
            round_robin_index[species] = 0

        products = []
        for species, characteristics in [(e['species'], e['characteristics']) for e in product_species]:

            # Simple round robin
            try:
                species_to_transform_string = order_dictionary[species][round_robin_index[species]]
                round_robin_index[species] = (round_robin_index[species] + 1) % len(order_dictionary[species])

                # Return in list of lists format for combination later
                products.append([self.transform_species_string(species_to_transform_string, characteristics,
                                                               Ref_object_to_characteristics,
                                                               Ref_characteristics_to_object)])

            # If the species is not on the reactants - order_dictionary
            except KeyError:
                products.append(self.find_all_default_references_to_born_species(species,
                                                                                 characteristics,
                                                                                 Species_string_dictionary,
                                                                                 Ref_object_to_characteristics,
                                                                                 Ref_characteristics_to_object))

        return products


Default_RR = __RR_Default_Base()
