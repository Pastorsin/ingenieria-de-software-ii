import json
from django.views import View
from django.views.generic import DetailView
from django.template import loader
from django.http import HttpResponseRedirect, HttpResponse
from residencias.models import Residencia
from .models import Subasta, EnEspera, Reservada, CompraDirecta, Hotsale
from .models import CreditosInsuficientes, Semana
from django.contrib import messages
from django.urls import reverse


class MostrarSubastaView(DetailView):

    model = Subasta
    template_name = 'mostrar_subasta.html'

    MENSAJE_EXITO = 'Puja realizada con éxito!'
    MENSAJE_ERROR = 'Error! No tenés créditos suficientes para subastar'

    def post(self, request, *args, **kwargs):
        subasta = self.get_object()
        try:
            subasta.nueva_puja(
                pujador=request.user.usuarioestandar,
                monto=request.POST['monto']
            )
            messages.success(
                request,
                self.MENSAJE_EXITO
            )
        except CreditosInsuficientes:
            messages.error(
                request,
                self.MENSAJE_ERROR
            )
        return HttpResponseRedirect(subasta.get_absolute_url())


class MostrarCompraDirectaView(DetailView):

    model = CompraDirecta
    template_name = 'mostrar_compra_directa.html'

    MENSAJE_ERROR = 'No tenés suficientes créditos para realizar esta compra'
    MENSAJE_EXITO = '¡Semana reservada correctamente! Disfrute su estadía'

    def post(self, request, *args, **kwargs):
        compra_directa = self.get_object()
        comprador = self.request.user
        try:
            reserva = compra_directa.generar_reserva(comprador)
            messages.success(request, self.MENSAJE_EXITO)
            return HttpResponseRedirect(reserva.get_absolute_url())
        except CreditosInsuficientes:
            messages.error(request, self.MENSAJE_ERROR)
            return HttpResponseRedirect(compra_directa.get_absolute_url())


class MostrarEnEsperaView(DetailView):

    model = EnEspera
    template_name = 'mostrar_en_espera.html'

    def post(self, request, *args, **kwargs):
        en_espera = self.get_object()

        monto = request.POST['monto']
        hotsale = en_espera.establecer_hotsale(float(monto))

        mensaje_exito = 'Hotsale establecido correctamente'
        messages.success(request, mensaje_exito)

        return HttpResponseRedirect(hotsale.get_absolute_url())


class MostrarReservadaView(DetailView):

    model = Reservada
    template_name = 'mostrar_reservada.html'

    MENSAJE_EXITO = 'Reserva eliminada correctamente'

    def post(self, request, *args, **kwargs):
        reserva = self.get_object()
        reserva.cancelar()
        messages.success(request, self.MENSAJE_EXITO)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('mis_reservas')


class MostrarHotsaleView(DetailView):

    model = Hotsale
    template_name = 'mostrar_hotsale.html'

    def post(self, request, *args, **kwargs):
        hotsale = self.get_object()

        comprador = self.request.user
        reserva = hotsale.generar_reserva(comprador)

        mensaje_exito = '¡Semana reservada correctamente! Disfrute su estadía'
        messages.success(request, mensaje_exito)

        return HttpResponseRedirect(reserva.get_absolute_url())


class SemanasView(DetailView):
    model = Residencia
    template_name = 'listado_semanas.html'

    def get_context_data(self, **kwargs):
        context = super(SemanasView, self).get_context_data(**kwargs)
        self.residencia = self.get_object()
        if self.request.user.is_staff:
            context['listado_semanas'] = self.residencia.semanas
        else:
            context['listado_semanas'] = self.residencia.semanas_adquiribles()
        return context

    def get(self, request, *args, **kwargs):
        get = self.request.GET
        get_keys = list(get)
        if get_keys:
            self.__seguir_semana(
                get=get,
                semana_pk=get_keys.pop(),
                usuario=self.request.user
            )
        return super(SemanasView, self).get(request, *args, **kwargs)

    def __seguir_semana(self, get, semana_pk, usuario):
        semana = Semana.objects.get(pk=semana_pk)
        if get[semana_pk] == 'Seguir':
            semana.agregar_seguidor(self.request.user)
        else:
            semana.eliminar_seguidor(self.request.user)


class LeerNotificacionesView(View):

    def get(self, request, *args, **kwargs):
        usuario_conectado = self.request.user
        usuario_conectado.leer_notificaciones()
        return HttpResponse()


class NotificacionesSinLeer(View):

    def notificaciones_html(self):
        template = loader.get_template('listado_notificaciones.html')
        contexto = {
            'user': self.request.user
        }
        return template.render(contexto)

    def cantidad_notificaciones(self):
        usuario_conectado = self.request.user
        return usuario_conectado.notificaciones_sin_leer().count()

    def get(self, request, *args, **kwargs):
        contexto = {
            'notificaciones_html': self.notificaciones_html(),
            'cantidad': self.cantidad_notificaciones()
        }
        return HttpResponse(json.dumps(contexto))
