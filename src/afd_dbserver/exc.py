class DBError(Exception):
    ...

class NotFoundError(DBError):

    def __init__(self, klass_, **kwargs):
        args_ = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        super(NotFoundError, self).__init__(f"{klass_.__name__} not found with params: {args_}")

class BadRequestError(DBError):
    ...


