"""bpod-rig utility functions"""
import inspect
from typing import Callable, Any

def get_default_params(*functions: Callable) -> dict[str, Any]:
    """This function takes one or more functions and returns a dictionary of default parameters.

    Knowing which parameters in a function accept default arguments is useful
    for **kwargs parsing. This function uses inspect to find the parameters in a function's
    signature and adds those with default values to a dictionary.

    The 'self' parameter and required parameters are not returned

    Example function signature:
        def func1(self, param1, param2 = 'foo', param3 = 'baz')

    The resultant dictionary from get_default_params(func1) will be:
    {
        'param2': 'foo',
        'param3': 'baz',
    }

    Parameters
    ----------
    functions : *Callable
        One or more functions that accept default arguments

    Returns
    -------
    dict[str, Any]
        Dictionary of parameters with default values and those values for all
        functions

    """
    return {
        param: value.default
        for func in functions for param, value in inspect.signature(func).parameters.items()
        if value is not inspect.Parameter.empty and
        param != "self"
    }



