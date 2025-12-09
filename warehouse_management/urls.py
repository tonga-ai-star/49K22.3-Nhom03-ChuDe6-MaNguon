from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import logout
from django.shortcuts import redirect
def custom_logout(request):
    logout(request)
    return redirect('login')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('san-pham/', include('products.urls')),
    path('kho/', include('inventory.urls')),
    path('doi-tac/', include('partners.urls')),
    path('bao-cao/', include('reports.urls')),
    path('settings_app/', include('settings_app.urls')),
    path('logout/', custom_logout, name='logout'),
    path('debt/', include('debt.urls', namespace='debt')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
