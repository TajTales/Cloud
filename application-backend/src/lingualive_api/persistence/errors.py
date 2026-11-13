class PersistenceError(Exception):
    pass


class InvalidRecord(PersistenceError):
    pass


class Conflict(PersistenceError):
    pass


class Forbidden(PersistenceError):
    pass


class NotFound(PersistenceError):
    pass


class StorageUnavailable(PersistenceError):
    pass


class IntegrityFailure(PersistenceError):
    pass
