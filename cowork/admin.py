from django.contrib import admin
from .models import *
# Register your models here.


admin.site.site_header = 'Coloby Admin'
admin.site.site_title = 'Coloby Admin'

admin.site.register(Message)
admin.site.register(Room)
admin.site.register(Task)
admin.site.register(User)


