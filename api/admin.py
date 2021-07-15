from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Quiz, Image

# admin.site.register(UserAdmin)
admin.site.register(Quiz)
admin.site.register(Image)

