"""O-only wire budget; inherited Etcd transport and auth remain unchanged."""


class OneShotRequests:
    def __init__(self, request, emit):
        self.request = request
        self.emit = emit
        self.operations = []

    def __call__(self, endpoint, path, body, token=None):
        tracked = path in tuple('/v3/cluster/member/' + op for op in ('remove', 'add', 'promote'))
        if not tracked:
            return self.request(endpoint, path, body, token)
        operation = path.rsplit('/', 1)[-1]
        if operation in self.operations:
            raise RuntimeError('O duplicate wire membership POST forbidden')
        expected = ('remove', 'add', 'promote')[len(self.operations)] if len(self.operations) < 3 else None
        if operation != expected:
            raise RuntimeError('O out-of-order wire membership POST forbidden')
        self.operations.append(operation)
        self.emit('WIRE_REQUEST', operation=operation, endpoint=endpoint,
                  ordinal=len(self.operations))
        try:
            result = self.request(endpoint, path, body, token)
        except BaseException as error:
            self.emit('WIRE_ERROR', operation=operation, failure_type=type(error).__name__)
            raise
        self.emit('WIRE_RESPONSE', operation=operation, response_keys=sorted(result))
        return result
