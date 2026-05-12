class DBError(Exception):
    ...

class NotFoundError(DBError):

    def __init__(self, klass_, **kwargs):
        args_ = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        super(NotFoundError, self).__init__(f"{klass_.__name__} not found with params: {args_}")

class BadRequestError(DBError):
    ...

class InvalidEnumValueError(BadRequestError):

    def __init__(self, type_, enum_type_cls):
        super(InvalidEnumValueError, self).__init__(f"{type_} is not a valid {enum_type_cls.__name__}")
