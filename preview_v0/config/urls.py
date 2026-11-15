from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.static import serve
from django.conf import settings
from merchant import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.index, name='index'),
    path('stores/new/', views.store_form, name='store_new'),
    path('s/<int:store_id>/', views.overview, name='overview'),
    path('s/<int:store_id>/edit/', views.store_form, name='store_edit'),
    path('s/<int:store_id>/products/new/', views.product_form, name='product_new'),
    path('s/<int:store_id>/products/<int:product_id>/edit/', views.product_form, name='product_edit'),
    path('s/<int:store_id>/products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('s/<int:store_id>/assistant/', views.assistant, name='assistant'),
    path('s/<int:store_id>/chat/', views.chat, name='chat'),
    path('s/<int:store_id>/conversations/', views.conversations, name='conversations'),
    path('s/<int:store_id>/settings/', views.settings, name='settings'),
    path('assets/<path:path>', serve, {'document_root': settings.BASE_DIR / 'assets'}),
]
