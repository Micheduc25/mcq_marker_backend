from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django_mysql.models import ListCharField, ListTextField


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

    marksDistribution = ListCharField(
        base_field=models.CharField(max_length=3),
        max_length=255,
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
        return str(self.course) + str(self.id)

    # quiz properties that are very useful to us

    class Meta:
        ordering = ['-created']


def nameFile(instance, filename):
    return '/'.join(['images', 'quiz_{}'.format(instance.sheet_id), str(instance.name), filename])


class Image(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to=nameFile, blank=True, null=True)
    sheet = models.ForeignKey(Quiz, related_name="image", on_delete=models.CASCADE)

