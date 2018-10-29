from abc import ABCMeta
from ipaddress import ip_network, _BaseNetwork
from typing import Iterable


class BaseStruct(object, metaclass=ABCMeta):
    __slots__ = ()


class SubnetQueue(BaseStruct):
    __slots__ = ('name', '_net', '_max_limit', 'is_access', 'queue_id')

    def __init__(self, name: str, network, max_limit=0.0,
                 is_access=True, queue_id=None):
        super().__init__()
        self.name = name
        self.network = network
        self.max_limit = max_limit
        self.is_access = is_access
        self.queue_id = queue_id

    def get_max_limit(self):
        return self._max_limit

    def set_max_limit(self, v):
        if isinstance(v, tuple):
            self._max_limit = v
        elif isinstance(v, str):
            s_in, s_out = v.split('/')
            self._max_limit = float(s_in), float(s_out)
        elif isinstance(v, (int, float)):
            sp = float(v)
            self._max_limit = sp, sp
        else:
            raise ValueError('Unexpected format for max_limit')

    max_limit = property(get_max_limit, set_max_limit)

    def get_network(self):
        return self._net

    def set_network(self, v):
        if isinstance(v, (str, int)):
            self._net = ip_network(v, strict=False)
        elif issubclass(v.__class__, _BaseNetwork):
            self._net = v
        else:
            raise ValueError('Unexpected format for network')

    network = property(get_network, set_network)

    def __eq__(self, other):
        return self.network == other.network and self.max_limit == other.max_limit

    def __hash__(self):
        return hash(str(self.max_limit) + str(self.network))

    def __repr__(self):
        return "net %s" % self.network


VectorQueue = Iterable[SubnetQueue]
