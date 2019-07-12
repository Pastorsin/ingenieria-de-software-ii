from django.contrib import admin
from .models import CompraDirecta, Subasta, Semana, EnEspera, NoDisponible
from .models import Hotsale, Notificacion, Puja

admin.site.register(CompraDirecta)
admin.site.register(Subasta)
admin.site.register(Semana)
admin.site.register(EnEspera)
admin.site.register(NoDisponible)
admin.site.register(Hotsale)
admin.site.register(Notificacion)
admin.site.register(Puja)
