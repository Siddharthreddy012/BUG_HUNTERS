from django.urls import path
from . import views

urlpatterns = [
    path('my-result/', views.my_results_view, name='my_results'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('export/csv/', views.export_results_csv, name='export_results_csv'),
    path('export/excel/', views.export_results_excel, name='export_results_excel'),
]

