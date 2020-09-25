from re import match


class ValidateError(Exception):
    pass


class Validator:
    _regex = ""
    _name = ""

    def __init__(self, _name, _regex):
        self._regex = _regex
        self._name = _name

    def validate(self, var):
        if not match(self._regex, var):
            raise ValidateError("{} validator unmatched {}".format(self._name, var))
