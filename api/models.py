from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django_mysql.models import ListCharField, ListTextField
from datetime import datetime
import os


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Quiz(models.Model):
    bubble_types = [('Circles', 'Circles'), ('Squares', 'Squares')]
    label_types = [('A-B-C', 'A-B-C'), ('i-ii-iii', 'i-ii-iii'), ('1-2-3', '1-2-3')]

    sheet_name = models.CharField(max_length=255, default="default_sheet")
    created = models.DateTimeField(auto_now_add=True)
    bubble = models.CharField(choices=bubble_types, max_length=100)
    questions = models.IntegerField(default=10)
    choices = models.IntegerField(default=4)
    choiceLabels = models.CharField(choices=label_types, max_length=100)
    failMark = models.IntegerField(default=0)
    pending_images = models.IntegerField(default=0)
    corrected_images = models.IntegerField(default=0)

    # list fields
    correctAnswers = ListCharField(
        base_field=models.CharField(max_length=3),
        max_length=255,
        default=['1']
    )

    marksAllocation = ListCharField(
        base_field=models.CharField(max_length=3),
        max_length=255,
        default=['2']
    )

    marksDistribution = ListTextField(
        base_field=models.CharField(max_length=255, blank=True, null=True, default=""),

        default=['2']
    )

    remarks = ListTextField(
        base_field=models.CharField(max_length=255, blank=True, null=True, default=""),

        default=['courage']
    )

    creator = models.ForeignKey('auth.User', related_name='quizes', on_delete=models.CASCADE)

    # less important nullable fields
    university = models.CharField(max_length=255, null=True, blank=True)
    school = models.CharField(max_length=255, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    classe = models.CharField(max_length=255, null=True, blank=True)
    course = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=100, null=True, blank=True)
    credit = models.IntegerField(default=4, null=True, blank=True)
    instructor = models.CharField(max_length=255, null=True, blank=True)

    # String representation of the quiz object
    def __str__(self):
        return self.sheet_name

    # quiz properties that are very useful to us

    class Meta:
        ordering = ['-created']


def nameFile(instance, filename):
    now = datetime.now()
    ext = '.' + filename.split('.')[-1]

    return os.path.join(settings.MEDIA_ROOT, 'images', 'sheets', 'sheet_{}'.format(instance.sheet_id),
                        instance.status, now.isoformat() + ext)


class SheetImage(models.Model):
    status_types = [('pending', 'pending'), ('corrected', 'corrected')]
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to=nameFile, blank=True, null=True)
    sheet = models.ForeignKey(Quiz, related_name="image", on_delete=models.CASCADE)
    status = models.CharField(choices=status_types, max_length=50, default='pending')


class Question(models.Model):
    sheet = models.ForeignKey(Quiz, related_name='question', on_delete=models.CASCADE)
    q_number = models.IntegerField(default=1)  # the number of the question on the sheet

    correct_ans = ListCharField(
        max_length=255,
        base_field=models.CharField(max_length=255, default="")  # the correct answers of the question
    )

    wrong_ans = ListCharField(
        max_length=255,
        base_field=models.CharField(max_length=255, default="")  # the wrong answers of the question
    )

    mark_distribution = ListCharField(
        max_length=255,
        base_field=models.CharField(max_length=100, blank=True, null=True, default="")  # correct answer percentages
    )

    total_mark = models.DecimalField(max_digits=6, decimal_places=2)  # the total mark for the question
    remark = models.TextField()  # any remark about the question


class Student(models.Model):
    code = models.CharField(max_length=100, primary_key=True)
    sheet = models.ForeignKey(Quiz, related_name='student', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()


class StudentQuestions(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    answered_correct = ListCharField(
        max_length=255,
        base_field=models.CharField(max_length=100, default="")  # the answers which were correctly chosen
    )

    answered_wrong = ListCharField(
        max_length=255,
        base_field=models.CharField(max_length=100, default="")  # the answers which were wrongly chosen
    )

    percentage_pass = models.DecimalField(max_digits=3, decimal_places=2)  # percentage of mark obtained
    mark = models.DecimalField(max_digits=6, decimal_places=2)  # the total mark obtained for the question


class Results(models.Model):
    sheet = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    mark = models.DecimalField(max_digits=6, decimal_places=2)
    total = models.DecimalField(max_digits=6, decimal_places=2)
