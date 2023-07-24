from django.contrib import admin
from .models import Project, Task
# Register your models here.


admin.site.site_header = "Coloby Admin"
admin.site.site_title = "Coloby Admin Area"
admin.site.index_title = "Welcome to the Coloby Admin Area"

admin.site.register(Project)
admin.site.register(Task)