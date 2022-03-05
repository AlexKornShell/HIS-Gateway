from django.contrib import admin
from .models import RequestToHIS

class RequestToHISAdmin(admin.ModelAdmin):
    readonly_fields = ('date_time',)

admin.site.register(RequestToHIS, RequestToHISAdmin)
