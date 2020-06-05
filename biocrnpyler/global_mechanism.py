#  Copyright (c) 2019, Build-A-Cell. All rights reserved.
#  See LICENSE file in the project root directory for details.

from warnings import warn

from .mechanism import Mechanism
from .chemical_reaction_network import Reaction, Species, ComplexSpecies
from typing import List, Union

#Global mechanisms are a lot like mechanisms. They are called only by mixtures
#  on a list of all species have been generated by components. Global mechanisms are meant
#  to work as universal mechanisms that function on each species or all species of some
#  type or with some attribute. Global mechanisms may only act on one species at a time.
#
#In order to decide which species a global mechanism acts upon, the filter_dict is used.
#       filter_dict[species.material_type / specie.attributes / species.name / repr(species)] = True / False
#  For each species, its material type, name, and attributes are sent through the filter_dict. If True
#  is returned, the GlobalMechanism will act on the species. If False is returned, the
#  the GlobalMechanism will not be called. If there are conflicts in the filter_dict, an error is raised.
#
#If the species's name, material type, and attributes are all not in the filter_dict, the GlobalMechanism will
#  be called if default_on == True and not called if default_on == False.
#Note that the above filtering is done automatically. Any parameters needed by the global mechanism must be
#  in the Mixture's parameter dictionary. These methods are assumed to take a single species
#  as input.
#
#An example of a global mechanism is degradation via dilution which is demonstrated in the Tests folder.
#
#GlobalMechanisms should be used cautiously or avoided alltogether - the order in which they are called
# may have to be carefully user defined in the subclasses of Mixture in order to ensure expected behavior.


"""Global mechanisms are a lot like mechanisms. They are called only by mixtures
   on a list of all species have been generated by components. Global mechanisms
   are meant to work as universal mechanisms that function on each species or
   all species of some material type or with some attribute. Global mechanisms
   may only act on one species at a time.

 In order to decide which species a global mechanism acts upon, the filter_dict
    is used.
        filter_dict[species.material_type / species.attributes] = True / False
   For each species, its material type or attributes are sent through the
   filter_dict. If True is returned, the GlobalMechanism will act on the
   species. If False is returned, the the GlobalMechanism will not be called.
   If filter_dict[attribute] is different from filter_dict[material_type],
   filter_dict[attribute] takes precedent. If multiple filter_dict[attribute]
   contradict for different attributes, an error is raised. 

   For ComplexSpecies, filter based upon all subspecies.type. If there is a conflict, 
   raise a warning and go with the default.

 If the species's name, material type, and attributes are all not in the
    filter_dict, the GlobalMechanism will be called if default_on == True and
    not called if default_on == False.

 Note that the above filtering is done automatically. Any parameters needed by
    the global mechanism must be in the Mixture's parameter dictionary. These
    methods are assumed to take a single species as input.

 An example of a global mechanism is degradation via dilution which is
    demonstrated in the Tests folder.

 GlobalMechanisms should be used cautiously or avoided alltogether - the order
    in which they are called may have to be carefully user defined in the
    subclasses of Mixture in order to ensure expected behavior.
"""


class GlobalMechanism(Mechanism):
    def __init__(self, name: str, mechanism_type = "", filter_dict = {},
                 default_on = False):
        self.filter_dict = filter_dict
        self.default_on = default_on
        Mechanism.__init__(self, name=name, mechanism_type=mechanism_type)

    def apply_filter(self, s: Species):
        """
        applies the filter dictionary to determine if a global mechanism acts on a species
        :param s:
        :return:
        """
        fd = self.filter_dict
        use_mechanism = None

        if isinstance(s, ComplexSpecies):
            species_list = [s]+s.species
        else:
            species_list = [s]

        for subs in species_list:
            for a in s.attributes+[subs.material_type, repr(subs), subs.name]:
                if a in fd:
                    if use_mechanism == None:
                        use_mechanism = fd[a]
                    elif use_mechanism != fd[a]:
                        raise AttributeError(f"species {repr(s)} has multiple attributes(or material type) which conflict with global mechanism filter {repr(self)}.")

        if use_mechanism is None:
            use_mechanism = self.default_on

        return use_mechanism

    def update_species_global(self, species_list: List[Species], parameters):
        new_species = []
        for s in species_list:
            use_mechanism = self.apply_filter(s)
            if use_mechanism:
                new_species += self.update_species(s, parameters)
        return new_species

    def update_reactions_global(self, species_list: List[Species], parameters):
        fd = self.filter_dict
        new_reactions = []
        for s in species_list:
            use_mechanism = self.apply_filter(s)
            if use_mechanism:
                new_reactions += self.update_reactions(s, parameters)

        return new_reactions

    def update_species(self, s, parameters):
        """
        All global mechanisms must use update_species functions with these inputs
        :param s:
        :param parameters:
        :return:
        """
        return []

    def update_reactions(self, s, parameters):
        """
        All global mechanisms must use update_reactions functions with these inputs
        :param s:
        :param parameters:
        :return:
        """
        return []

    def get_parameter(self, s, parameters, param_name):
        if (self.name, repr(s), param_name) in parameters:
            return parameters[(self.name, repr(s), param_name)]
        elif (self.mechanism_type, repr(s), param_name) in parameters:
            return parameters[(self.mechanism_type, repr(s), param_name)]
        elif (repr(s), param_name) in parameters:
            return parameters[(repr(s), param_name)]
        elif (self.name, param_name) in parameters:
            return parameters[(self.name, param_name)]
        elif (self.mechanism_type, param_name) in parameters:
            return parameters[(self.mechanism_type, param_name)]
        elif (param_name) in parameters:
            return parameters[param_name]
        else:
            raise ValueError(f"No parameter found for GlobalMechanism name: {self.name} type: {self.mechanism_type} species: {repr(s)} param: {param_name}")


class Dilution(GlobalMechanism):
    def __init__(self, name = "global_degredation_via_dilution",
                 mechanism_type = "dilution", filter_dict = {},
                 default_on = True):
        GlobalMechanism.__init__(self, name = name,
                                 mechanism_type = mechanism_type,
                                 default_on = default_on,
                                 filter_dict = filter_dict)

    def update_reactions(self, s: Species, parameters):
        k_dil = self.get_parameter(s, parameters, "kdil")
        rxn = Reaction([s], [], k_dil)
        return [rxn]





class AnitDilutionConstiutiveCreation(GlobalMechanism):
    """
    Global Mechanism to Constitutively Create Certain Species at the rate of dilution.
    Useful for keeping machinery species like ribosomes and polymerases at a constant concentration.
    """
    def __init__(self, name = "anti_dilution_constiuitive_creation",
                 material_type = "dilution", filter_dict = {},
                 default_on = True):
        GlobalMechanism.__init__(self, name = name,
                                 mechanism_type = material_type,
                                 default_on = default_on,
                                 filter_dict = filter_dict)

    def update_reactions(self, s, parameters):
        k_dil = parameters["kdil"]
        rxn = Reaction([], [s], k_dil)
        return [rxn]
