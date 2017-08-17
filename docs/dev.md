## Добавление поддерживаемого устройства (Свича)


## Добавим платёжную систему
Для того чтоб добавить платёжную систему добавьте в файл *pay_systems* каталога abonapp
процедуру которая будет принимать request, далее он пригодится в теле вашей процедуры.
Пустая процедура, возвращающая xml, будет выглядеть так:

    def my_custom_pay_system(request):
        return "<?xml version='1.0' encoding='UTF-8'?>\n" \
               "<pay-response>Pay ok</pay-response>\n"

Затем импортируйте её в процедуру *terminal_pay* в файле views.py каталога abonapp.
Для примера это будет выглядеть так:

    @atomic
    def terminal_pay(request):
        from .pay_systems import my_custom_pay_system
        ret_text = my_custom_pay_system(request)
        return HttpResponse(ret_text)

Проследите чтоб ваша процедура вы вызывала исключений, обрабатывайте всё внутри тела процедуры.
Про декоратор **@atomic** вы можете прочитать в документации к [Django](https://docs.djangoproject.com/en/1.9/topics/db/transactions).
В кратце этот декоратор защищает от незавешённых транзакций, например при высокой нагрузке.

