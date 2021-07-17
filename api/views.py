from django.contrib.auth.models import User
from rest_framework import viewsets, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from api.serializers import UserSerializer, QuizSerializer, ImageSerializer
from .models import Quiz, SheetImage
from rest_framework import generics, permissions, mixins
from .permissions import IsOwnerOrReadOnly, IsAdminOrOwner, IsAdminOrUser
from rest_framework.authtoken.models import Token
from .sheets_correction.mcq_corrector import MCQCorrector
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Q
import os
import shutil


# for user in User.objects.all():
#     Token.objects.get_or_create(user=user)
#     print(user.username + "'s token created")


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    permission_classes = [IsAdminOrUser]


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
        try:
            Quiz.objects.get(sheet_name=sheet_name)
            raise exceptions.ValidationError({'error': "A sheet with this name already exists"}, code=400)
        except Quiz.DoesNotExist:
            serializer.save(creator=self.request.user)


class QuizDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrOwner]


# this function moves a sheet image which has been corrected from the pending directory to the corrected directory
def move_corrected_image(image: SheetImage):
    try:
        filename = image.image.name.split('/')[-1]
        im_path = image.image.path
        new_path = os.path.join(settings.MEDIA_ROOT,
                                'images', 'sheets', 'sheet_{}'.format(image.sheet.id),
                                'corrected', filename)

        # Create dir if necessary and move file
        if not os.path.exists(os.path.dirname(new_path)):
            os.makedirs(os.path.dirname(new_path))

        shutil.move(im_path, new_path)
        image.status = 'corrected'
        image.save()

    except FileNotFoundError as err:
        raise exceptions.ValidationError('Could not find the image file {} '.format(err), code=404)

    except OSError as err:
        raise exceptions.ValidationError('Could not move file to corrected folder ==> {} '.format(err), 400)


class SheetsCorrection(generics.ListCreateAPIView):
    queryset = SheetImage.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, *args, **kwargs):

        images = request.FILES.getlist('images')
        im_quiz = Quiz.objects.get(pk=request.data["sheet_id"])

        # instantiate mcq corrector
        mcq_corrector = MCQCorrector(sheet_instance=im_quiz)

        results = []

        for file in images:
            new_im = SheetImage(name="image-{}".format(str(im_quiz)), image=file, sheet=im_quiz)
            new_im.url = new_im.image.url
            new_im.save()
            im_quiz.pending_images += 1

            try:
                res = mcq_corrector.correct_sheet(new_im.image.path)
                results.append(res)
                move_corrected_image(new_im)

                im_quiz.pending_images -= 1
                im_quiz.corrected_images += 1

            except Exception as err:
                raise exceptions.ValidationError('One or more of the sheets is not well formatted ===> {}'.format(err),
                                                 code=400)

        return Response(data={'results': results}, status=200)


class ImagesList(generics.ListCreateAPIView):
    # queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            sheet = Quiz.objects.get(creator_id=user.id)
            return SheetImage.objects.filter(sheet_id=sheet.id)

        except Quiz.DoesNotExist:
            raise exceptions.ValidationError('You have no sheet with this id')

    def post(self, request, *args, **kwargs):

        images = request.FILES.getlist('images')
        im_quiz = Quiz.objects.get(pk=request.data["sheet_id"])

        imagelist = []
        for file in images:
            new_im = SheetImage(name="image-{}".format(str(im_quiz)), image=file, sheet=im_quiz, status='pending')
            new_im.url = new_im.image.url
            new_im.save()
            im_quiz.pending_images += 1
            imagelist.append(new_im)

        res = self.serializer_class(instance=imagelist, many=True, context={"request": request})
        return Response(res.data)


# view for batch correction of scripts
class SheetsBatchCorrect(generics.GenericAPIView):
    queryset = SheetImage.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        sheet_ids = request.data['sheets']
        sheets = Quiz.object.filter(pk__in=sheet_ids)
        corrector = MCQCorrector(Quiz())

        final_results = []

        sheet_index = 0
        for sheet in sheets:
            corrector.set_sheet(sheet)
            pending_images = SheetImage.objects.filter(Q(sheet_id=sheet.id) & Q(status='pending'))
            final_results.append({'sheet_id': sheet.id, 'sheet_name': sheet.name, 'results': [], 'errors': []})

            for image in pending_images:
                try:
                    res = corrector.correct_sheet(image.image.path)
                    final_results[sheet_index]['results'].append(res)

                    move_corrected_image(image)
                    sheet.pending_images -= 1
                    sheet.corrected_images += 1
                    sheet.save()

                except Exception as err:
                    final_results[sheet_index]['errors'].append(str(err))
                    continue

            sheet_index += 1

        return Response(final_results)


# class PendingSheetsLists(generics.ListAPIView):
#
