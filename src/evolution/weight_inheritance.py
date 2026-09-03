"""
Weight inheritance mechanism for ENSS.

Instead of retraining every evolved agent from scratch,
child architectures reuse compatible parameters from parents.
"""


class WeightInheritance:
    def inherit(self, parent_model, child_architecture):
        inherited = {}

        for name, param in parent_model.state_dict().items():
            if self.is_compatible(name, child_architecture):
                inherited[name] = param

        return inherited

    def is_compatible(self, parameter_name, architecture):
        # Placeholder compatibility matching.
        # Future versions will support tensor shape mapping
        # between Mamba, Attention and hybrid modules.
        return True
