from nas_app.nas_managers.mod_mikrotik import MikrotikTransmitter
from nas_app.nas_managers.core import NasNetworkError, NasFailedResult
from nas_app.nas_managers.structs import SubnetQueue

# Указываем какие реализации NAS у нас есть, это будет использоваться в
# web интерфейсе
NAS_TYPES = (
    ('mktk', MikrotikTransmitter),
)
