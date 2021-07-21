from django.urls import include, path
from rest_framework import routers
from django.conf.urls.static import static
from django.conf import settings


router = routers.DefaultRouter()
# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    
    path('api/', include('api.urls')),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
