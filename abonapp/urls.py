from django.conf.urls import url, include
import views

urlpatterns = [

    url(r'^$', views.grouplist, name='abongroup_list_link'),
    url(r'^addgroup$', views.addgroup, name='addgroup_link'),
    url(r'^delgroup', views.delgroup, name='people_delgroup_link'),

    url(r'^(?P<gid>\d+)/', include('abonapp.urls_abon')),

    url(r'^log$', views.log_page, name='abonapp_log_link'),

    url(r'^del$', views.delentity, name='abonapp_del_link'),

    url(r'^pay$', views.terminal_pay, name='abonapp_terminalpay_link'),

    url(r'^debtors$', views.debtors, name='abonapp_debtors'),

    # Api's
    url(r'^api/abons$', views.abons)

]
