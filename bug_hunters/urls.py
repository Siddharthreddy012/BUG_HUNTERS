from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from competition import views as comp_views
from accounts import views as acc_views
from results import views as res_views

urlpatterns = [
    # Django standard admin
    path('admin/', admin.site.urls),

    # Core public pages
    path('', comp_views.home_view, name='home'),
    path('about/', comp_views.about_view, name='about'),
    path('rules/', comp_views.rules_view, name='rules'),
    path('rounds/', comp_views.rounds_overview_view, name='rounds_overview'),
    path('dashboard/', comp_views.dashboard_view, name='dashboard'),
    path('leaderboard/', res_views.leaderboard_view, name='leaderboard'),

    # Direct auth shortcuts
    path('register/', acc_views.register_view, name='register'),
    path('login/', acc_views.login_view, name='login'),
    path('logout/', acc_views.logout_view, name='logout'),

    # Modular apps
    path('accounts/', include('accounts.urls')),
    path('competition/', include('competition.urls')),
    path('results/', include('results.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
