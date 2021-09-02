from django.contrib.auth.models import User, Group
from .models import Quiz, SheetImage, Student, Question
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    quizes = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Quiz.objects.all())

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'quizes']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class QuizSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.username')
    correctAnswers = serializers.ListField(child=serializers.CharField())
    marksAllocation = serializers.ListField(child=serializers.CharField())
    remarks = serializers.ListField(child=serializers.CharField(allow_blank=True), )
    marksDistribution = serializers.ListField(child=serializers.CharField(), )

    class Meta:
        model = Quiz
        fields = '__all__'
        include = ['creator']


class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = SheetImage

        fields = ('id', 'name', 'image', 'sheet', 'status')
        read_only_fields = ('id', 'name', 'sheet')


class StudentSerializer(serializers.ModelSerializer):
    sheet_id = serializers.ReadOnlyField(source='sheet.id')

    class Meta:
        model = Student
        fields = '__all__'
        include = ['sheet_id']


class QuestionSerializer(serializers.ModelSerializer):

    sheet_id = serializers.ReadOnlyField(source='sheet.id')
    correct_ans = serializers.ListField(child=serializers.CharField())
    wrong_ans = serializers.ListField(child=serializers.CharField())
    mark_distribution = serializers.ListField(child=serializers.CharField())
    dis = serializers.JSONField()

    class Meta:
        model = Question
        fields = '__all__'
        include = ['sheet_id']
