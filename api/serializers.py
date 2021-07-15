from django.contrib.auth.models import User, Group
from .models import Quiz, Image
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
        model = Image
        fields = ('id', 'name', 'image', 'sheet')
        read_only_fields = ('id', 'name', 'sheet')
