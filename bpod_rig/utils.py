"""bpod-rig utility functions."""

import inspect
from typing import Any, Callable


def get_func_params(
    *functions: Callable, optional_only: bool = False
) -> dict[str, Any]:
    """Function takes one or more functions and returns a dictionary parameters.

    Knowing the keyword-based parameters for a function is useful for **kwargs parsing.
    This function uses inspect to retrieve the parameters in a function's signature and
    adds to a dictionary. This function can also filter for parameters that have
    default values and are optional.

    The 'self' parameter is not returned

    Example function signature:
        def func1(self, param1, param2 = 'foo', param3 = 'baz')

    The resultant dictionary from get_default_params(func1) will be:
    {
        'required': ['param1'],
        'param2': 'foo',
        'param3': 'baz',
    }

    The resultant dictionary from get_default_params(func1, optional_only) will be:
    {
        'required': [],
        'param2': 'foo',
        'param3': 'baz',
    }

    Parameters
    ----------
    functions : *Callable
        One or more functions that accept default arguments

    optional_only : bool (optional)
        Only return parameters with default values defined in the signature

    Returns
    -------
    dict[str, Any]
        Dictionary of parameters

        If the parameter is required, it is stored in a list with key 'required'
        If the parameter is optional, it is stored as param_name : default_value
    """
    params = {
        "required": [],
    }

    for func in functions:
        sig = inspect.signature(func)
        for param, value in sig.parameters.items():
            if value.default == inspect.Parameter.empty:
                if optional_only:
                    continue
                params["required"].append(param)

            if param != "self":
                params[param] = value.default

    return params
