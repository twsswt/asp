'''
A nice API to build advice from.
@author probablytom
'''
from .weaver import IdentityAspect, weave_clazz
from functools import partial


class FlexibleAdvice(IdentityAspect):
    def __init__(self, target):
        super(FlexibleAdvice, self).__init__()
        self.preludes = []
        self.encores = []
        self.error_handlers = []
        self.around_functions = []
        self.target = target

    def prelude(self, attribute, context, *args, **kwargs):
        [prelude(attribute, context, *args, **kwargs) for prelude in self.preludes]

    def encore(self, attribute, context, result):
        [encore(attribute, context, result) for encore in self.encores]

    def error_handling(self, attribute, context, exception):

        if len(self.error_handlers) == 0:
            raise exception

        [handler(attribute, context, exception) for handler in self.error_handlers]

    def around(self, attribute, context, *args, **kwargs):

        def nest_around_call(nested_around, next_around):
            return partial(next_around, nested_around, context)

        nested_around = reduce(nest_around_call,
                               self.around_functions[::-1],
                               partial(super(FlexibleAdvice, self).around, attribute, context))

        return nested_around(*args, **kwargs)

    def apply_advice(self):
        weave_clazz(self.target.im_class, {self.target: self})


class AdviceBuilder(object):
    def __init__(self):
        self.advice = {}

    def add_prelude(self, target, prelude):
        specific_advice = self.advice.get(target, FlexibleAdvice(target))
        specific_advice.preludes.append(prelude)
        self.advice[target] = specific_advice
        return self

    def add_encore(self, target, encore):
        specific_advice = self.advice.get(target, FlexibleAdvice(target))
        specific_advice.encores.append(encore)
        self.advice[target] = specific_advice
        return self

    def add_error_handler(self, target, err_handler):
        specific_advice = self.advice.get(target, FlexibleAdvice(target))
        specific_advice.error_handlers.append(err_handler)
        self.advice[target] = specific_advice
        return self

    def add_around(self, target, around):
        specific_advice = self.advice.get(target, FlexibleAdvice(target))
        specific_advice.around_functions.append(around)
        self.advice[target] = specific_advice
        return self

    def apply(self):
        [aspect.apply_advice() for aspect in self.advice.values()]
