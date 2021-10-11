from django.contrib.auth.models import User, Group
from .models import Quiz, SheetImage, Student, Question, Results, StudentQuestions
from rest_framework import serializers
from django.db.models.query import QuerySet


class UserSerializer(serializers.ModelSerializer):
    quizes = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Quiz.objects.all())

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'quizes']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class QuestionSerializer(serializers.ModelSerializer):

    sheet_id = serializers.ReadOnlyField(source='sheet.id')
    correct_ans = serializers.ListField(child=serializers.CharField())
    wrong_ans = serializers.ListField(child=serializers.CharField())
    mark_distribution = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Question
        fields = '__all__'
        include = ['sheet_id']


class QuizSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.username')
    questions_data = QuestionSerializer(many=True, allow_null=True)

    class Meta:
        model = Quiz
        fields = '__all__'
        include = ['creator', 'questions_data']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions_data')
        sheet = Quiz.objects.create(**validated_data)

        q_serializer = QuestionSerializer(data=questions_data, many=True, allow_null=True)

        if q_serializer.is_valid(raise_exception=True):
            # sheet.save()
            q_serializer.save(sheet=sheet)
        return sheet

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions_data')
        sheet_id = instance.id

        instance.sheet_name = validated_data.get('sheet_name', instance.sheet_name)
        instance.created = validated_data.get('created', instance.created)
        instance.bubble = validated_data.get('bubble', instance.bubble)
        instance.questions = validated_data.get('questions', instance.questions)
        instance.choices = validated_data.get('choices', instance.choices)
        instance.choiceLabels = validated_data.get('choiceLabels', instance.choiceLabels)
        instance.failMark = validated_data.get('failMark', instance.failMark)
        instance.pending_images = validated_data.get('pending_images', instance.pending_images)
        instance.corrected_images = validated_data.get('corrected_images', instance.corrected_images)

        instance.university = validated_data.get('university', instance.university)
        instance.school = validated_data.get('school', instance.school)
        instance.department = validated_data.get('department', instance.department)
        instance.classe = validated_data.get('classe', instance.classe)
        instance.course = validated_data.get('course', instance.course)
        instance.code = validated_data.get('code', instance.code)
        instance.credit = validated_data.get('credit', instance.credit)
        instance.instructor = validated_data.get('instructor', instance.instructor)

        try:
            sheet = Quiz.objects.get(pk=sheet_id)

            q_serializer = QuestionSerializer(data=questions_data, many=True, allow_null=True)

            if q_serializer.is_valid(raise_exception=True):

                Question.objects.filter(sheet_id=sheet_id).delete()
                q_serializer.save(sheet=sheet)

                instance.save()
                return instance

        except Quiz.DoesNotExist:
            raise serializers.ValidationError('invalid sheet id', code=404)

    def to_representation(self, instance):
        return_data = super(QuizSerializer, self).to_representation(instance)
        # check the request is list view or detail view
        is_list_view = isinstance(self.instance, QuerySet)
        if not is_list_view:
            sheet_questions = Question.objects.filter(sheet_id=self.instance.id)
            q_serializer = QuestionSerializer(sheet_questions, many=True)
            extra_return_data = {'questions_data': q_serializer.data}
            return_data.update(extra_return_data)
        return return_data


class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = SheetImage

        fields = ('id', 'name', 'image', 'sheet', 'status')
        read_only_fields = ('id', 'name', 'sheet')


class StudentSerializer(serializers.ModelSerializer):
    sheet = serializers.ReadOnlyField(source='sheet.id')

    class Meta:
        model = Student
        fields = '__all__'
        include = ['sheet']


class ResultsSerializer(serializers.ModelSerializer):
    sheet = serializers.ReadOnlyField(source='sheet.sheet_name')
    student = StudentSerializer()

    class Meta:
        model = Results
        fields = '__all__'
        include = ['sheet', 'student']


class StudentQuestionsSerializer (serializers.ModelSerializer):
    student = StudentSerializer()
    answered_correct = serializers.ListField(child=serializers.CharField())
    answered_wrong = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = StudentQuestions
        fields = '__all__'
        include = ['student']


