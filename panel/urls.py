from django.urls import path
from . import views
from .views import RequestToHISView

urlpatterns = [
    path('', views.index, name='index'),
    path('change_urls/', views.change_urls),
    path('check_servers/', views.check, {'url': 'servers_url'}),
    path('check_db/', views.check, {'url': 'db_url'}),
    path('his_requests/', RequestToHISView.as_view()),
    
    path('resource/', views.resource),
    path('resource/', views.resource),
    
    path('ui_connector/auth/', views.auth_request),
    
    path('ui_connector/patient/', views.patient),
    
    path('ui_connector/observations/', views.observations),
    path('ui_connector/diagnoses/', views.diagnoses),
    path('ui_connector/medications/', views.medications),
    
    path('ui_connector/slots/', views.slots),
    path('ui_connector/appointment/', views.appointment),
]