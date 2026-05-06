from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('', views.index, name='index'),
    path('auth/', views.login_register_page, name='auth_page'),
    path('dashboard/', views.dashboard_page, name='dashboard_page'),
    path('feed/', views.alert_feed_page, name='feed_page'),
    path('create-alert/', views.create_alert_page, name='create_alert_page'),
    path('community/', views.community_grid_page, name='community_page'),
    path('contributions/', views.contribution_panel_page, name='contribution_page'),
    path('admin-dashboard/', views.admin_dashboard_page, name='admin_dashboard'),
    path('authority-dashboard/', views.authority_dashboard_page, name='authority_dashboard'),
    path('profile/', views.profile_page, name='profile_page'),
    path('guides/', views.guides_page, name='guides_page'),

    # Auth APIs
    path('api/register/', views.register_api, name='api_register'),
    path('api/login/', views.login_api, name='api_login'),
    path('api/logout/', views.logout_api, name='api_logout'),

    # Functional APIs
    path('api/alerts/', views.alerts_api, name='api_alerts'),
    path('api/alerts/<int:alert_id>/', views.delete_alert_api, name='api_delete_alert'),
    path('api/alerts/<int:alert_id>/comments/', views.comments_api, name='api_comments'),
    path('api/alerts/<int:alert_id>/status/', views.update_alert_status_api, name='api_update_alert_status'),
    path('api/contributions/', views.contributions_api, name='api_contributions'),
    path('api/community-panels/', views.api_community_panels, name='api_community_panels'),
    path('api/admin/stats/', views.api_admin_stats, name='api_admin_stats'),
    path('api/admin/verify-authority/', views.verify_authority_api, name='api_verify_authority'),
    path('api/admin/moderate/', views.admin_content_moderation_api, name='api_admin_moderate'),
    path('api/community/stats/', views.community_stats_api, name='api_community_stats'),
    path('api/local-needs/', views.local_needs_api, name='api_local_needs'),
    path('api/blood-requests/', views.blood_requests_api, name='api_blood_requests'),
    path('api/volunteers/', views.volunteers_api, name='api_volunteers'),
    path('api/contact/', views.api_contact_submit, name='api_contact_submit'),
    path('api/authority/stats/', views.api_authority_stats, name='api_authority_stats'),
]
