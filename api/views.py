from django.contrib.auth.models import User
from rest_framework import viewsets, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from api.serializers import UserSerializer, QuizSerializer, ImageSerializer
from .models import Quiz, Image
from rest_framework import generics, permissions, mixins
from .permissions import IsOwnerOrReadOnly, IsAdminOrOwner
from rest_framework.authtoken.models import Token
from .sheets_correction.mcq_corrector import MCQCorrector

# for user in User.objects.all():
#     Token.objects.get_or_create(user=user)
#     print(user.username + "'s token created")


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    # permission_classes = [permissions.IsAuthenticated]


class CurrentUserView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, req, *args, **kwargs):
        user = UserSerializer(instance=req.user)
        return Response(user.data)


class QuizList(generics.ListCreateAPIView):
    # queryset = Quiz.objects.filter(creator_id=request.user.id)
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Quiz.objects.filter(creator_id=self.request.user.id)

    def perform_create(self, serializer):
        sheet_name = self.request.data['sheet_name']
        sheet_exists = False
        try:
            Quiz.objects.get(sheet_name=sheet_name)
            sheet_exists = True
        except Quiz.DoesNotExist:
            serializer.save(creator=self.request.user)
        finally:
            if sheet_exists:
                raise exceptions.ValidationError({'error': "A sheet with this name already exists"}, code=400)


class QuizDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrOwner]


class SheetsCorrection(generics.ListCreateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    def post(self, request, *args, **kwargs):

        images = request.FILES.getlist('images')
        im_quiz = Quiz.objects.get(pk=request.data["sheet_id"])

        # instantiate mcq corrector
        mcq_corrector = MCQCorrector(sheet_instance=im_quiz)

        results = []

        for file in images:
            new_im = Image(name="image-{}".format(str(im_quiz)), image=file, sheet=im_quiz)
            new_im.save()
            res = mcq_corrector.correct_sheet(new_im.image.path)
            results.append(res)

        return Response(data={'results': results}, status=200)


class ImagesView(generics.ListCreateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    def post(self, request, *args, **kwargs):

        images = request.FILES.getlist('images')
        im_quiz = Quiz.objects.get(pk=request.data["sheet_id"])

        for file in images:
            new_im = Image(name="image-{}".format(str(im_quiz)), image=file, sheet=im_quiz)
            new_im.save()


