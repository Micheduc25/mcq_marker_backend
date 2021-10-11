from django.contrib.auth.models import User
from rest_framework import viewsets, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from api.serializers import UserSerializer, QuizSerializer, ImageSerializer, StudentSerializer, ResultsSerializer, StudentQuestionsSerializer
from .models import Quiz, SheetImage, Question, Student, StudentQuestions, Results
from rest_framework import generics, permissions, mixins
from .permissions import IsOwnerOrReadOnly, IsAdminOrOwner, IsAdminOrUser
from rest_framework.authtoken.models import Token
from .sheets_correction.mcq_corrector import MCQCorrector
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Q, Max
import os
import shutil
from collections import namedtuple


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


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer

    permission_classes = [IsAdminOrUser]

    def perform_create(self, serializer):
        if serializer.is_valid(raise_exception=True):
            try:
                sheet = Quiz.objects.get(pk=self.request.GET.get('sheet_id'))
                serializer.save(sheet=sheet)

            except Quiz.DoesNotExit:
                raise exceptions.ValidationError("Sheet not found", code=404)

    def get_queryset(self):
        return Student.objects.filter(sheet_id=self.request.GET.get('sheet_id')).order_by('name')


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
def move_corrected_image(image: SheetImage, sheet: Quiz):
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

        sheet.pending_images -= 1
        sheet.corrected_images += 1

        sheet.save()

    except FileNotFoundError as err:
        raise exceptions.ValidationError('Could not find the image file {} '.format(err), code=404)

    except OSError as err:
        raise exceptions.ValidationError('Could not move file to corrected folder ==> {} '.format(err), 400)


class SheetsCorrection(generics.ListCreateAPIView):
    queryset = SheetImage.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, *args, **kwargs):
        # we collect the image files and find the sheet they correspond to
        images = request.FILES.getlist('images')
        im_quiz = Quiz.objects.get(pk=request.data["sheet_id"])

        # we attribute a session to this correction batch
        session = 1

        sheet_results = Results.objects.filter(sheet_id=im_quiz.id)
        if len(sheet_results) > 0:
            latest_session = sheet_results.aggregate(Max("session"))['session__max']
            session = latest_session + 1

        sheet_questions = Question.objects.filter(sheet_id=im_quiz.id)

        # instantiate mcq corrector
        mcq_corrector = MCQCorrector(sheet_instance=im_quiz, sheet_questions=sheet_questions, session=session)

        results = []

        for file in images:
            new_im = SheetImage(name="image-{}".format(str(im_quiz)), image=file, sheet=im_quiz)
            new_im.url = new_im.image.url
            new_im.save()
            im_quiz.pending_images += 1

            try:
                res = mcq_corrector.correct_sheet(new_im.image.path)
                results.append(res)
                move_corrected_image(new_im, im_quiz)

            except Exception as err:
                raise exceptions.ValidationError('{}'.format(err),
                                                 code=400)

        return Response(data={'results': results}, status=200)


# API view to upload images to be saved or to get all images belonging to a creator
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

        im_quiz.save()
        res = self.serializer_class(instance=imagelist, many=True, context={"request": request})
        return Response(res.data)


# view for batch correction of scripts
class SheetsBatchCorrect(generics.GenericAPIView):
    queryset = SheetImage.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        sheet_ids = request.data['sheets']
        sheets = Quiz.objects.filter(pk__in=sheet_ids)
        corrector = MCQCorrector(Quiz())

        final_results = []

        sheet_index = 0
        for sheet in sheets:
            corrector.set_sheet(sheet)
            pending_images = SheetImage.objects.filter(Q(sheet_id=sheet.id) & Q(status='pending'))
            final_results.append({'sheet_id': sheet.id, 'sheet_name': sheet.sheet_name, 'results': [], 'errors': []})

            for image in pending_images:
                try:
                    res = corrector.correct_sheet(image.image.path)
                    final_results[sheet_index]['results'].append(res)

                    move_corrected_image(image, sheet)

                except Exception as err:
                    final_results[sheet_index]['errors'].append(str(err))
                    continue

            sheet_index += 1

        return Response(final_results)


class PendingSheetsLists(generics.ListAPIView):
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        sheet_id = self.request.query_params['sheet_id']
        try:
            return SheetImage.objects.filter(Q(sheet_id=sheet_id) & Q(status='pending'))

        except SheetImage.DoesNotExist:
            raise exceptions.ValidationError("could not find required images", code=404)

        except Quiz.DoesNotExist:
            raise exceptions.ValidationError("sheet for these images not found", code=404)

        except Exception as err:
            raise exceptions.ValidationError("{}".format(err), code=500)


class SheetResultsList(generics.ListAPIView):
    serializer_class = ResultsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        sheet_id = self.request.query_params['sheet_id']
        # session = self.request.query_params['session']
        # print(f"session===>{session}")
        # Q(session=session) &

        try:
            return Results.objects.filter(Q(sheet_id=sheet_id) &
                                          Q(sheet__creator_id=self.request.user.id))

        except Results.DoesNotExist:
            raise exceptions.ValidationError("could not find any corresponding results", code=404)
        except Exception as err:
            raise exceptions.ValidationError("{}".format(err), code=500)


# view to obtain the detailed results for a student
class ResultDetailList(generics.ListAPIView):
    serializer_class = StudentQuestionsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        sheet_id = self.request.query_params['sheet_id']
        student_code = self.request.query_params['code']
        session = self.request.query_params['session']

        try:
            return StudentQuestions.objects.filter(Q(student__sheet_id=sheet_id)
                                                   & Q(student__code=student_code)
                                                   & Q(session=session)
                                                   )

        except StudentQuestions.DoesNotExist:
            raise exceptions.ValidationError("could not find any corresponding results", code=404)
        except Exception as err:
            raise exceptions.ValidationError("{}".format(err), code=500)


class StudentResultsList(generics.ListAPIView):
    serializer_class = StudentQuestionsSerializer

    def get_queryset(self):
        sheet_id = self.request.query_params['sheet_id']

        session = self.request.query_params['session']
        # print(f"session is ====> {session}")

        try:
            return StudentQuestions.objects.filter(Q(student__sheet_id=sheet_id) & Q(session=session))

        except StudentQuestions.DoesNotExist:
            raise exceptions.ValidationError("could not find any corresponding results", code=404)
        except Exception as err:
            raise exceptions.ValidationError("{}".format(err), code=500)




