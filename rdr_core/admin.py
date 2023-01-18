from django.contrib import admin
from .models import Rule, Case
# Register your models here.

admin.site.register(Rule)
admin.site.register(Case)

admin.site.site_header = "Ripple Down Rule Based Decision Intelligence for Mental Disorder Diagnosis"
admin.site.site_title = "Ripple Down Rule Based Decision Intelligence for Mental Disorder Diagnosis"
admin.site.index_title = "Welcome to RDR Mental Disorder Diagnosis System"
