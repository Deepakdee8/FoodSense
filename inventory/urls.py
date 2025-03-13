"""
URL configuration for ilp_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index,name = 'index'),
    path('inventory/', views.inventory,name = 'inventory'),
    path('threshold/', views.threshold_levels,name = 'threshold_levels'),
    path('realtime/', views.realtime_inventory,name = 'realtime_inventory'),
    path('purchase/', views.purchase_details,name = 'purchase_details'),
    path('order/', views.order_details,name = 'order_details'),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('upload_to_cloud/', views.upload_to_cloud, name='upload_to_cloud'),
    path('api/least-quantity-items/', views.get_least_quantity_items, name='least_quantity_items'),
    path("api/receive_autoorder/", views.receive_autoorder, name="receive_autoorder"),
    path('add_item/', views.add_item, name='add_item'),
    path('edit_item/<int:item_id>/', views.edit_item, name='edit_item'),
    path('delete_item/<int:item_id>/', views.delete_item, name='delete_item'),

] 
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)