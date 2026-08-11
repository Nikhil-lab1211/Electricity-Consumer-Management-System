# user_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    
    # Bills
    path('bills/', views.bill_view, name='bills'),
    path('check-bill/', views.check_bill, name='check_bill'),
    path('pay-bill/<int:bill_id>/', views.pay_bill, name='pay_bill'),
    
    # Complaints
    path('file-complaint/', views.file_complaint, name='file_complaint'),
    path('view-complaints/', views.view_complaints, name='view_complaints'),
    
    # Outages
    path('report-outage/', views.report_outage, name='report_outage'),
    path('view-outages/', views.view_outages, name='view_outages'),
    
    # Consumption
    path('track-consumption/', views.track_consumption, name='track_consumption'),
    
    # API endpoints
    path('api/check-bill/', views.check_bill_api, name='check_bill_api'),
    path('api/pay-bill/', views.pay_bill_api, name='pay_bill_api'),
    path('api/report-outage/', views.report_outage_api, name='report_outage_api'),
    path('api/track-consumption/', views.track_consumption_api, name='track_consumption_api'),
]