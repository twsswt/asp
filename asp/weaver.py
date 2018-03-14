"""
Core weaving functionality.
@author twsswt
"""
import inspect

from inspect import getmembers


_reference_get_attributes = dict()


class IdentityAspect(object):

    def prelude(self, attribute, context, *args, **kwargs):
        pass

    def encore(self, attribute, context, result):
        pass


identity = IdentityAspect()


def weave_clazz(clazz, advice):
    """
    Applies aspects specified in the supplied advice dictionary to methods in the supplied class.

    Weaving is applied dynamically at runtime by intercepting invocations of __getattribute__ on target objects.
    The method requested by the __getattribute__ call is weaved using the aspect specified in the supplied advice
    dictionary (which maps method references to aspects) before returning it to the requester.

    An aspect value may itself be a dictionary of object filter->aspect mappings.  In this case, the dictionary is
    searched for a filter that matches the target (self) object specified in the __getattribute__ call.

    :param clazz : the class to weave.
    :param advice : the dictionary of method reference->aspect mappings to apply for the class.
    """

    if clazz not in _reference_get_attributes:
        _reference_get_attributes[clazz] = clazz.__getattribute__

    def __weaved_getattribute__(self, item):
        attribute = object.__getattribute__(self, item)

        if item[0:2] == '__':
            return attribute

        elif inspect.ismethod(attribute):

            def wrap(*args, **kwargs):

                reference_function = attribute.im_func
                # Ensure that advice key is unbound method for instance methods.
                advice_key = getattr(attribute.im_class, attribute.func_name)

                aspect = advice.get(advice_key, identity)

                aspect.prelude(attribute, self, *args, **kwargs)

                # Execute the intercepted method.
                result = reference_function(self, *args, **kwargs)
                aspect.encore(attribute, self, result)
                return result

            wrap.func_name = attribute.func_name

            return wrap

        elif inspect.isfunction(attribute):

            def wrap(*args, **kwargs):

                reference_function = attribute
                advice_key = reference_function
                aspect = advice.get(advice_key, identity)

                aspect.prelude(attribute, self, *args, **kwargs)

                # Execute the intercepted function.
                result = reference_function(*args, **kwargs)
                aspect.encore(attribute, self, result)
                return result

            return wrap

        else:
            return attribute

    clazz.__getattribute__ = __weaved_getattribute__


def weave_module(mod, advice):
    """
    Weaves specified advice in the supplied dictionary to methods in the supplied module.  All member classes and
    functions are inspected in turn, with the specified advice being applied to each.
    :param mod : the module to weave.
    :param advice : the dictionary of method->aspect mappings to apply.
    """
    for _, member in getmembers(mod):
        if inspect.isclass(member):
            weave_clazz(member, advice)


def unweave_class(clazz):
    if clazz in _reference_get_attributes:
        clazz.__getattribute__ = _reference_get_attributes[clazz]


def unweave_all_classes():
    for clazz in _reference_get_attributes.keys():
        unweave_class(clazz)
