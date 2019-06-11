from django.views.generic import DetailView
from django.http import HttpResponseRedirect
from residencias.models import Residencia
from .models import Subasta, EnEspera, Reservada, CompraDirecta
from django.contrib import messages

# Create your views here.


class MostrarSubastaView(DetailView):

    model = Subasta
    template_name = 'mostrar_subasta.html'

    def post(self, request, *args, **kwargs):
        subasta = self.get_object()

        # if usuario_conectado.tiene_creditos():
        if True:
            usuario_conectado = request.user
            nuevo_monto = request.POST['monto']
            subasta.nueva_puja(usuario_conectado, nuevo_monto)
            mensaje_exito = 'Puja realizada con éxito!'
            messages.success(request, mensaje_exito)
        else:
            mensaje_error = 'Error! No tenés créditos suficientes para pujar'
            messages.error(request, mensaje_error)
        return HttpResponseRedirect(subasta.get_absolute_url())


class MostrarCompraDirectaView(DetailView):

    model = CompraDirecta
    template_name = 'mostrar_compra_directa.html'


class MostrarEnEsperaView(DetailView):

    model = EnEspera
    template_name = 'mostrar_en_espera.html'


class MostrarReservadaView(DetailView):

    model = Reservada
    template_name = 'mostrar_reservada.html'


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
