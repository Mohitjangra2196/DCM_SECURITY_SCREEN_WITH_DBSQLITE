# gatepass_app/urls.py
from django.urls import path, re_path, include
from . import views
from django.contrib.auth import views as auth_views

# DRF Imports
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'gatepasses', views.GatePassViewSet)


urlpatterns = [
    # Existing HTML-rendering URLs
    path('', views.home_screen, name='home_screen'),
    path('mark_out/', views.mark_out_screen, name='mark_out_screen'),
    path('mark_in/', views.mark_in_screen, name='mark_in_screen'),
    path('mark_in/create_manual/', views.create_manual_gatepass_entry, name='create_manual_gatepass_entry'),
    path('mark_out/create_manual_out/', views.create_manual_mark_out_entry, name='create_manual_mark_out_entry'),

    path('get_employee_details/', views.get_employee_details, name='get_employee_details'),

    # Distinct URLs for process_mark_out and markout_cross
    path('mark_out/process/<str:gatepass_no>/', views.process_mark_out, name='process_mark_out'),
    path('mark_out/cross/<str:gatepass_no>/', views.markout_cross, name='markout_cross'),
    path('mark_in/process/<str:gatepass_no>/', views.process_mark_in, name='process_mark_in'),
    #path('mark_in/cross/<str:gatepass_no>/', views.markin_cross, name='markout_cross'),


    # Old get_employee_details API (can be removed if replaced by DRF version)
    # path('api/get_employee_details/<str:emp_code>/', views.get_employee_details, name='get_employee_details_api'),

    # New DRF API Endpoints
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='gatepass_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]