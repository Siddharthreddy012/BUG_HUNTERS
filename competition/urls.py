from django.urls import path
from . import views

urlpatterns = [
    # Competition examination rounds
    path('round1/', views.round1_view, name='round1'),
    path('round2/', views.round2_view, name='round2'),
    path('round3/', views.round3_view, name='round3'),

    # APIs
    path('api/log-violation/', views.api_log_violation, name='api_log_violation'),
    path('api/run-code/', views.api_test_run_code, name='api_test_run_code'),

    # Admin Portal
    path('portal/admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('portal/admin/participant/<int:user_id>/', views.admin_participant_detail_view, name='admin_participant_detail'),
    path('portal/admin/verify-round/<int:round_id>/', views.admin_verify_round_action, name='admin_verify_round'),
    path('portal/admin/override/<int:user_id>/', views.admin_manual_qualification_override, name='admin_override'),
    path('portal/admin/settings/', views.admin_settings_view, name='admin_settings'),
    path('portal/admin/questions/', views.admin_questions_view, name='admin_questions'),
]

