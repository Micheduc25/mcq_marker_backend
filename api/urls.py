from django.urls import include, path
from rest_framework import routers
from api import views

# from rest_framework.authtoken import views as token_views

from .tokens import CustomAuthToken


router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'students', views.StudentViewSet, basename='students')


app_name = 'api'
urlpatterns = [

    # users endpoints
    # path('users/', views.UserList.as_view()),
    # path('users/<int:pk>/', views.UserDetail.as_view()),

    # quizes endpoints
    path('quizes/', views.QuizList.as_view()),
    path('quizes/<int:pk>', views.QuizDetail.as_view()),

    # sheet upload
    path('upload-sheets/', views.SheetsCorrection.as_view()),
    path('batch-correct/', views.SheetsBatchCorrect.as_view()),

    # images endpoint
    path('images/', views.ImagesList.as_view()),
    path('images/pending/', views.PendingSheetsLists.as_view()),

    # results endpoints
    path('results/', views.SheetResultsList.as_view()),
    path('student-results/', views.ResultDetailList.as_view()),


    # auth endpoints
    path('auth-token/', CustomAuthToken.as_view()),
    path('me/', views.CurrentUserView.as_view()),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('', include(router.urls)),

]
