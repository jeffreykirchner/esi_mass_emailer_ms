from django.contrib import admin

from main.models import Parameters, MassEmail

# Register your models here.

admin.site.register(Parameters)

#Instruction set
class MassEmailAdmin(admin.ModelAdmin):
    '''
    list of emails sent
    '''
     
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    list_display = ['message_subject','app','memo']

    readonly_fields = ('app', 'message_subject', 'message_text', 'user_list', 'email_result', 'memo','timestamp','updated')


      

admin.site.register(MassEmail, MassEmailAdmin)
