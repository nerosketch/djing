# -*- coding: utf-8 -*-
from .mod_mikrotik import MikrotikTransmitter
from .core import NasFailedResult, NasNetworkError
from .structs import TariffStruct, AbonStruct

# Transmitter мы будем импортировать в других местах
# Тут надо указать какой у нас будет NAS
# т.е. какой класс будет управлять доступом в интернет
Transmitter = MikrotikTransmitter
