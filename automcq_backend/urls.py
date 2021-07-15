from django.urls import include, path
from rest_framework import routers


router = routers.DefaultRouter()
# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    
    path('api/', include('api.urls')),


]
