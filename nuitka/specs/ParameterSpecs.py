#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" This module maintains the parameter specification classes.

These are used for function, lambdas, generators. They are also a factory
for the respective variable objects. One of the difficulty of Python and
its parameter parsing is that they are allowed to be nested like this:

(a,b), c

Much like in assignments, which are very similar to parameters, except
that parameters may also be assigned from a dictionary, they are no less
flexible.

"""

from nuitka import Variables
from nuitka.PythonVersions import python_version
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)


class TooManyArguments(Exception):
    def __init__(self, real_exception):
        Exception.__init__(self)

        self.real_exception = real_exception

    def getRealException(self):
        return self.real_exception


class ParameterSpec(object):
    # These got many attributes, in part duplicating name and instance of
    # variables, pylint: disable=too-many-instance-attributes

    __slots__ = (
        "name",
        "owner",
        "normal_args",
        "normal_variables",
        "list_star_arg",
        "is_list_star_arg_single",
        "dict_star_arg",
        "list_star_variable",
        "dict_star_variable",
        "default_count",
        "kw_only_args",
        "kw_only_variables",
        "pos_only_args",
        "pos_only_variables",
        "type_shape",
    )

    @counted_init
    def __init__(
        self,
        ps_name,
        ps_normal_args,
        ps_pos_only_args,
        ps_kw_only_args,
        ps_list_star_arg,
        ps_dict_star_arg,
        ps_default_count,
        ps_is_list_star_arg_single=False,
        type_shape=None,
    ):
        if type(ps_normal_args) is str:
            if ps_normal_args == "":
                ps_normal_args = ()
            else:
                ps_normal_args = ps_normal_args.split(",")

        if type(ps_kw_only_args) is str:
            if ps_kw_only_args == "":
                ps_kw_only_args = ()
            else:
                ps_kw_only_args = ps_kw_only_args.split(",")

        assert None not in ps_normal_args

        self.owner = None

        self.name = ps_name
        self.normal_args = tuple(ps_normal_args)
        self.normal_variables = None

        assert (
            ps_list_star_arg is None or type(ps_list_star_arg) is str
        ), ps_list_star_arg
        assert (
            ps_dict_star_arg is None or type(ps_dict_star_arg) is str
        ), ps_dict_star_arg

        assert type(ps_is_list_star_arg_single) is bool, ps_is_list_star_arg_single

        self.list_star_arg = ps_list_star_arg if ps_list_star_arg else None
        self.is_list_star_arg_single = ps_is_list_star_arg_single
        self.dict_star_arg = ps_dict_star_arg if ps_dict_star_arg else None

        self.list_star_variable = None
        self.dict_star_variable = None

        self.default_count = ps_default_count

        self.kw_only_args = tuple(ps_kw_only_args)
        self.kw_only_variables = None

        self.pos_only_args = tuple(ps_pos_only_args)
        self.pos_only_variables = None

        self.type_shape = type_shape

    if isCountingInstances():
        __del__ = counted_del()

    def makeClone(self):
        return ParameterSpec(
            ps_name=self.name,
            ps_normal_args=self.normal_args,
            ps_pos_only_args=self.pos_only_args,
            ps_kw_only_args=self.kw_only_args,
            ps_list_star_arg=self.list_star_arg,
            ps_dict_star_arg=self.dict_star_arg,
            ps_default_count=self.default_count,
            type_shape=self.type_shape,
        )

    def getDetails(self):
        return {
            "ps_name": self.name,
            "ps_normal_args": ",".join(self.normal_args),
            "ps_pos_only_args": self.pos_only_args,
            "ps_kw_only_args": ",".join(self.kw_only_args),
            "ps_list_star_arg": (
                self.list_star_arg if self.list_star_arg is not None else ""
            ),
            "ps_dict_star_arg": (
                self.dict_star_arg if self.dict_star_arg is not None else ""
            ),
            "ps_default_count": self.default_count,
            "type_shape": self.type_shape,
        }

    def checkParametersValid(self):
        arg_names = self.getParameterNames()

        # Check for duplicate arguments, could happen.
        for arg_name in arg_names:
            if arg_names.count(arg_name) != 1:
                return "duplicate argument '%s' in function definition" % arg_name

        return None

    def __repr__(self):
        parts = [str(normal_arg) for normal_arg in self.pos_only_args]
        if parts:
            parts.append("/")

        parts += [str(normal_arg) for normal_arg in self.normal_args]

        if self.list_star_arg is not None:
            parts.append("*%s" % self.list_star_arg)

        if self.dict_star_variable is not None:
            parts.append("**%s" % self.dict_star_variable)

        if parts:
            return "<ParameterSpec '%s'>" % ",".join(parts)
        else:
            return "<NoParameters>"

    def setOwner(self, owner):
        if self.owner is not None:
            return

        self.owner = owner
        self.normal_variables = []

        for normal_arg in self.normal_args:
            if type(normal_arg) is str:
                normal_variable = Variables.ParameterVariable(
                    owner=self.owner, parameter_name=normal_arg
                )
            else:
                assert False, normal_arg

            self.normal_variables.append(normal_variable)

        if self.list_star_arg:
            self.list_star_variable = Variables.ParameterVariable(
                owner=owner, parameter_name=self.list_star_arg
            )
        else:
            self.list_star_variable = None

        if self.dict_star_arg:
            self.dict_star_variable = Variables.ParameterVariable(
                owner=owner, parameter_name=self.dict_star_arg
            )
        else:
            self.dict_star_variable = None

        self.kw_only_variables = [
            Variables.ParameterVariable(owner=self.owner, parameter_name=kw_only_arg)
            for kw_only_arg in self.kw_only_args
        ]

        self.pos_only_variables = [
            Variables.ParameterVariable(owner=self.owner, parameter_name=pos_only_arg)
            for pos_only_arg in self.pos_only_args
        ]

    def getDefaultCount(self):
        return self.default_count

    def hasDefaultParameters(self):
        return self.getDefaultCount() > 0

    def getTopLevelVariables(self):
        return self.pos_only_variables + self.normal_variables + self.kw_only_variables

    def getAllVariables(self):
        result = list(self.pos_only_variables)
        result += self.normal_variables
        result += self.kw_only_variables

        if self.list_star_variable is not None:
            result.append(self.list_star_variable)

        if self.dict_star_variable is not None:
            result.append(self.dict_star_variable)

        return result

    def getParameterNames(self):
        result = list(self.pos_only_args + self.normal_args)

        result += self.kw_only_args

        if self.list_star_arg is not None:
            result.append(self.list_star_arg)

        if self.dict_star_arg is not None:
            result.append(self.dict_star_arg)

        return tuple(result)

    def getStarListArgumentName(self):
        return self.list_star_arg

    def isStarListSingleArg(self):
        return self.is_list_star_arg_single

    def getListStarArgVariable(self):
        return self.list_star_variable

    def getStarDictArgumentName(self):
        return self.dict_star_arg

    def getDictStarArgVariable(self):
        return self.dict_star_variable

    def getKwOnlyVariables(self):
        return self.kw_only_variables

    def allowsKeywords(self):
        # Abstract method, pylint: disable=no-self-use
        return True

    def getKeywordRefusalText(self):
        return "%s() takes no keyword arguments" % self.name

    def getArgumentNames(self):
        return self.pos_only_args + self.normal_args

    def getArgumentCount(self):
        return len(self.normal_args) + len(self.pos_only_args)

    def getKwOnlyParameterNames(self):
        return self.kw_only_args

    def getKwOnlyParameterCount(self):
        return len(self.kw_only_args)

    def getPosOnlyParameterCount(self):
        return len(self.pos_only_args)

    def getTypeShape(self):
        return self.type_shape


def matchCall(
    func_name,
    args,
    kw_only_args,
    star_list_arg,
    star_list_single_arg,
    star_dict_arg,
    num_defaults,
    num_pos_only,
    positional,
    pairs,
    improved=False,
):
    """Match a call arguments to a signature.

    Args:
        func_name - Name of the function being matched, used to construct exception texts.
        args - normal argument names
        kw_only_args -  keyword only argument names (Python3)
        star_list_arg - name of star list argument if any
        star_dict_arg - name of star dict argument if any
        num_defaults - amount of arguments that have default values
        num_pos_only - amount of arguments that must be given by position
        positional - tuple of argument values given for simulated call
        pairs - tuple of pairs arg argument name and argument values
        improved - (bool) should we give better errors than CPython or not.
    Returns:
        Dictionary of argument name to value mappings
    Notes:
        Based loosely on "inspect.getcallargs" with corrections.
    """

    assert isinstance(positional, tuple), positional
    assert isinstance(pairs, (tuple, list)), pairs

    assigned_tuple_params = set()
    result = {}
    pairs_dict = dict(pairs)

    def assign(arg, value):
        if isinstance(arg, str):
            result[arg] = value
        else:
            for subarg in arg:
                try:
                    subvalue = value.pop(0)
                except IndexError:
                    raise TooManyArguments(ValueError("need more values to unpack"))
                assign(subarg, subvalue)
            if value:
                raise TooManyArguments(ValueError("too many values to unpack"))

    def isAssigned(arg):
        if isinstance(arg, str):
            return arg in result
        return arg in assigned_tuple_params

    num_pos = len(positional)
    num_total = num_pos + len(pairs)
    num_args = len(args)

    for arg, value in zip(args, positional):
        assign(arg, value)

    if python_version >= 0x300 and not star_dict_arg:
        for pair in pairs:
            try:
                (args + kw_only_args).index(pair[0])
            except ValueError:
                message = (
                    "'{}' is an invalid keyword argument for {}()"
                    if improved or python_version >= 0x370
                    else "'{}' is an invalid keyword argument for this function".format(
                        pair[0], func_name
                    )
                )
                raise TooManyArguments(TypeError(message))

    if star_list_arg:
        if num_pos > num_args:
            value = positional[-(num_pos - num_args) :]
            assign(star_list_arg, value)

            if star_list_single_arg and len(value) > 1:
                raise TooManyArguments(
                    TypeError(
                        "{} expected at most 1 arguments, got {}".format(
                            func_name, len(value)
                        )
                    )
                )
        else:
            assign(star_list_arg, ())
    elif num_args and num_args < num_total:
        raise TooManyArguments(
            TypeError(
                "{} expected {} arguments, got {}".format(
                    func_name, num_args, num_total
                )
            )
        )
    elif num_args == 0 and num_total:
        if star_dict_arg:
            if num_pos:
                raise TooManyArguments(
                    TypeError(
                        "{}() takes exactly 0 arguments ({})".format(
                            func_name, num_total
                        )
                    )
                )
        else:
            raise TooManyArguments(
                TypeError("{}() takes no arguments ({})".format(func_name, num_total))
            )

    for arg in args + kw_only_args:
        if isinstance(arg, str) and arg in pairs_dict:
            if isAssigned(arg):
                raise TooManyArguments(
                    TypeError(
                        "{}() got multiple values for keyword argument '{}'".format(
                            func_name, arg
                        )
                    )
                )
            assign(arg, pairs_dict.pop(arg))

    if num_defaults > 0:
        for arg in (args + kw_only_args)[-num_defaults:]:
            if not isAssigned(arg):
                assign(arg, None)

    if star_dict_arg:
        assign(star_dict_arg, list(pairs_dict.items()))
    elif pairs_dict:
        unexpected = next(iter(pairs_dict))

        if improved:
            message = "{}() got an unexpected keyword argument '{}'".format(
                func_name, unexpected
            )
        else:
            message = "'{}' is an invalid keyword argument for this function".format(
                unexpected
            )

        raise TooManyArguments(TypeError(message))

    unassigned_args = [arg for arg in (args + kw_only_args) if not isAssigned(arg)]

    if unassigned_args:
        raise TooManyArguments(
            TypeError(
                "{} missing required argument(s): '{}'".format(
                    func_name, ", ".join(unassigned_args)
                )
            )
        )

    return result


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
