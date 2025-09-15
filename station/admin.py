from django.contrib import admin
from .models import Station

# Register your models here.

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('stationName', 'description', 'department')
    list_filter = ('department', 'stationName')
    search_fields = ('stationName', 'description')
    ordering = ('stationName',)
    
    fieldsets = (
        ('岗位信息', {
            'fields': ('stationName', 'description', 'department')
        }),
    )
