>Перед началом обязательно, хотя бы поверхностно, ознакомиться с документацией к
[Django](https://docs.djangoproject.com).

## Добавление поддерживаемого устройства (Свича)
Для того чтоб добавить новый тип устройства с которым потом сможет работать биллинг нужно открыть файл *devapp/dev_types.py*
и переопределить 2 интерфейса. Первый это *BasePort* для порта свича, а второй *DevBase* для самого свича соответственно.

Разберём этот процесс на примере готовой реализации для Eltex.

```python
class EltexPort(BasePort):

    def __init__(self, snmpWorker, *args, **kwargs):
        BasePort.__init__(self, *args, **kwargs)
        if not issubclass(snmpWorker.__class__, SNMPBaseWorker):
            raise TypeError
        self.snmp_worker = snmpWorker

    # выключаем этот порт
    def disable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % ('.1.3.6.1.2.1.2.2.1.7', self.num),
            2
        )

    # включаем этот порт
    def enable(self):
        self.snmp_worker.set_int_value(
            "%s.%d" % ('.1.3.6.1.2.1.2.2.1.7', self.num),
            1
        )
```
Тут в инициилизации мы передаём все базовые параметры базовому конструктору, и дополнительный аргумент snmpWorker
для работы по SNMP. *snmpWorker* это объект реализованного интерфейса SNMPBaseWorker, далее я опишу где мы его реализуем.
Для порта надо переопределить 2 метода: *disable* и *enable* понятно для чего, чтоб включать и отключать порт.

Шаблон реализации можно даже не менять, просто укажите вместо строки .1.3.6.1.2.1.2.2.1.7 нужный SNMP OID для включения порта.
К этой строке будет добавляться номер порта который нужно включить.
Для отключения так-же по аналогии.

Теперь реализация для свича:
```python
class EltexSwitch(DLinkDevice):

    @staticmethod
    def description():
        return _('Eltex switch')

    def get_ports(self):
        #nams = self.get_list('.1.3.6.1.4.1.171.10.134.2.1.1.100.2.1.3')
        stats = self.get_list('.1.3.6.1.2.1.2.2.1.7')
        oper_stats = self.get_list('.1.3.6.1.2.1.2.2.1.8')
        #macs = self.get_list('.1.3.6.1.2.1.2.2.1.6')
        speeds = self.get_list('.1.3.6.1.2.1.31.1.1.1.15')
        res = []
        for n in range(28):
            res.append(EltexPort(self,
                n+1,
                '',#nams[n] if len(nams) > 0 else _('does not fetch the name'),
                True if int(stats[n]) == 1 else False,
                '',#macs[n] if len(macs) > 0 else _('does not fetch the mac'),
                int(speeds[n]) if len(speeds) > 0 and int(oper_stats[n]) == 1 else 0,
            ))
        return res

    def get_device_name(self):
        return self.get_item('.1.3.6.1.2.1.1.5.0')

    def uptime(self):
        uptimestamp = safe_int(self.get_item('.1.3.6.1.2.1.1.3.0'))
        tm = RuTimedelta(timedelta(seconds=uptimestamp/100)) or RuTimedelta(timedelta())
        return tm

    @staticmethod
    def has_attachable_to_subscriber():
        return False

    @staticmethod
    def is_use_device_port():
        return False
```
Метод **@description** Просто отображает человекопонятное название вашего устройства в биллинге.
Заметьте что строка на английском и заключена в процедуру **_** (это ugettext_lazy, см. в импорте вверху файла),
это локализация для текущего языка. Про локализацию можно почитать в соответствующем разделе [django translation](https://docs.djangoproject.com/en/1.9/topics/i18n/translation/).

Метод **@get_ports** чаще всего редко изменяется по алгоритму, так что вам, в большенстве случаев, достаточно добавить
нужные SNMP OID в соответствующие места процедуры. Но вы вольны реализовать ваш метод получения портов
как вам угодно, главное чтоб возвращался список объектов определённого выше класса порта для этого свича.
В данном случае возвращается список объектов *EltexPort*.

Метод **@get_device_name** получает по SNMP имя устройства, просто укажите в вашей реализации нужный OID.

Метод **@uptime**, понятно что возвращает, укажите нужный OID. Вернётся тип *RuTimedelta*, это не тип Django, я сам его реализовал
для локализации временного промежутка на русский.

Статический метод **@has_attachable_to_subscriber** возвращает правду если это устройство можно привязать к абоненту.
Например у Dlink стоит True потому что Dlink стоит во многих местах на доступе, и его порты принадлежат
абонентам при авторизации.

Статический метод **@is_use_device_port** используется в DHCP чтоб понять что мы используем для привязки к абоненту всё устройство или
только порт устройства. Например, если у устройства только 1 порт абонента (PON ONU), то нужно вернуть True, во всех остальных случаях False.

Реализация SNMPBaseWorker по сути не нужна, класс абстрактных методов не имеет.
Потому когда наследуем наследуемся от *DevBase* то в базовые классы добавим и SNMPBaseWorker, как это сделано в *DLinkDevice*:
```python
class DLinkDevice(DevBase, SNMPBaseWorker):

    def __init__(self, ip, snmp_community, ver=2):
        DevBase.__init__(self)
        SNMPBaseWorker.__init__(self, ip, snmp_community, ver)
```
А далее просто передадим параметры для конструкторов обоих базовых классов.

Вы, наверное, обратили внимание, что *EltexSwitch* наследован от *DLinkDevice*, это потому что некоторые методы идентичны,
и реализация для обоих свичей похожа.

>П.С. Не изучайте как пример реализацию для PON, она, как по мне, костыльна. Это связано с тем что PON сильно отличается от
>принципа работы обычного свича, и чтоб подружить свичи и PON был реализован такой костыль.


## Добавим платёжную систему
Для того чтоб добавить платёжную систему добавьте в файл *abonapp/pay_systems.py* процедуру которая будет принимать
request, далее он пригодится в теле вашей процедуры. это тот самый request который передаётся в *view*. Пустая процедура, возвращающая xml, будет выглядеть так:

```python
def my_custom_pay_system(request):
    return "<?xml version='1.0' encoding='UTF-8'?>\n" \
           "<pay-response>Pay ok</pay-response>\n"
```

Затем импортируйте её в процедуру *terminal_pay* в файле views.py каталога abonapp.
Для примера это будет выглядеть так:

```python
@atomic
def terminal_pay(request):
    from .pay_systems import my_custom_pay_system
    ret_text = my_custom_pay_system(request)
    return HttpResponse(ret_text)
```

Проследите чтоб ваша процедура не вызывала исключений, обрабатывайте всё внутри тела процедуры.
Про декоратор **@atomic** вы можете прочитать в документации к [Django](https://docs.djangoproject.com/en/1.9/topics/db/transactions).
В кратце этот декоратор защищает от незавешённых транзакций, например при высокой нагрузке.


## Реализация своего NAS
Сейчас биллинг работает с Mikrotik в роли устройства для доступа абонентов в интернет.
Как можно реализовать такой-же для вашего роутера, например на GNU/Linux.

Создадим файл *agent/mod_linux.py* и реализуем потомка для интерфейса *BaseTransmitter*.
Методы вашего класса будут вызываться биллингом для взаимодействия с сервером доступа абонентов в интернет(NAS).

```python
from .core import BaseTransmitter, NasFailedResult, NasNetworkError

class LinuxTransmitter(BaseTransmitter):

    def add_user_range(self, user_list):
        """добавляем список абонентов в NAS"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def remove_user_range(self, users):
        """удаляем список абонентов"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def add_user(self, user, *args):
        """добавляем абонента"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def remove_user(self, user):
        """удаляем абонента"""

    @abstractmethod
    @check_input_type(AbonStruct)
    def update_user(self, user, *args):
        """
        Чтоб обновить абонента можно изменить всё кроме его uid, по uid абонент будет найден.
        Это значит что вы можете передать объект user класса AbonStruct, где только uid будет указывать на абонента,
        а остальные поля будут содержать новое значение.
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def add_tariff_range(self, tariff_list):
        """
        Пока не используется, зарезервировано.
        Добавляет список тарифов в NAS
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def remove_tariff_range(self, tariff_list):
        """
        Пока не используется, зарезервировано.
        Удаляем список тарифов по уникальным идентификаторам
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def add_tariff(self, tariff):
        """
        Пока не используется, зарезервировано.
        Добавляем тариф
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def update_tariff(self, tariff):
        """
        Пока не используется, зарезервировано.
        Чтоб обновить тариф надо изменить всё кроме его tid, по tid тариф будет найден
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def remove_tariff(self, tid):
        """
        :param tid: id тарифа в среде NAS сервера чтоб удалить по этому номеру
        Пока не используется, зарезервировано.
        """

    @abstractmethod
    @check_input_type(TariffStruct)
    def ping(self, host, count=10):
        """
        :param host: ip адрес в текстовом виде, например '192.168.0.1'
        :param count: количество пингов
        :return: None если не пингуется, иначе кортеж, в котором (сколько вернулось, сколько было отправлено)
        """

    @abstractmethod
    def read_users(self):
        """
        Читаем пользователей с NAS
        :return: список AbonStruct
        """
```

Для того чтоб биллинг знал о вашем классе надо указать его в *agent/\_\_init\_\_.py*.
Замените
>from .mod_mikrotik import MikrotikTransmitter

На это
>from .mod_mikrotik import LinuxTransmitter

И укажите ваш класс
> Transmitter = MikrotikTransmitter

Получится примерно такое содержимое:

```python
from .mod_mikrotik import LinuxTransmitter
from .core import NasFailedResult, NasNetworkError
from .structs import TariffStruct, AbonStruct

Transmitter = LinuxTransmitter
```

Для примера, как вы наверное уже догадались, можно посмотреть реализацию для Mikrotik в файле *agent/mod_mikrotik.py*

Чтобы выводить в биллинге различные сообщения об ошибках есть 2 типа исключений: *NasFailedResult* и *NasNetworkError*.
NasNetworkError, как понятно из названия, вызывается при проблемах в сети. А NasFailedResult при ошибочных кодах возврата из модуля на сервере NAS.

Биллинг прослушивает эти исключения при выполнении, и при возбуждении этих исключений отображает текст ошибки на экране пользователя.

При переопределении базового класса пожалуйста не забывайте вызвать базовый метод чтоб отработали декораторы методов интерфейса, этот декоратор проверяет тип входных данных.
Динамическая типизация python иногда подкладывает свинью в том смысле что можно передать не то что вы хотели бы передать, потому типы лучше проконтролировать, и тогда интерпретатор станет вашим другом помошником :)

Когда я прошу вызвать базовый метод, я имею ввиду это:
```python
...
def add_user_range(self, user_list):
    super(LinuxTransmitter, self).add_user_range(user_list)
    # ваш код
...
```

Кстати, не все методы обязательно реализовывать, некоторые из них зарезервированы на будущие цели, в комментариях к их прототипам в интерфейсе *BaseTransmitter* это сказано.
Поэтому просто переопределите эти зарезервированные методы как пустые, например метод *add_tariff_range* нигде в биллинге пока не вызывается. так что можно определить его пустым.
```python
def add_tariff_range(self, tariff_list):
    pass
```
