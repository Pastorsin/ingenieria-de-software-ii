from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType

from accounts.models import CustomUser, UsuarioEstandar
from residencias.models import Residencia

from django.urls import reverse
from django.db import models

from datetime import date, timedelta, datetime


class EventoNoPermitido(Exception):
    pass


class CreditosInsuficientes(Exception):
    pass


class Semana(models.Model):

    residencia = models.ForeignKey(
        Residencia,
        on_delete=models.CASCADE
    )
    fecha_inicio = models.DateField(
        null=True,
        blank=True
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    estado_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    estado = GenericForeignKey(
        'content_type',
        'estado_id'
    )
    seguidores = models.ManyToManyField(
        CustomUser,
        related_name='seguidores',
    )
    comprador = models.ForeignKey(
        CustomUser,
        related_name='comprador',
        on_delete=models.SET_NULL,
        null=True
    )

    def inicializar_con(self, numero_semana):
        self.incializar_fecha(numero_semana)
        self.inicializar_estados()
        self.save()

    def incializar_fecha(self, numero_semana):
        self.fecha_inicio = self.generar_lunes(numero_semana)

    def generar_lunes(self, numero_semana):
        return self.lunes_actual() + timedelta(weeks=numero_semana)

    def lunes_actual(self):
        hoy = date.today()
        return hoy - timedelta(days=hoy.weekday())

    def inicializar_estados(self):
        Estado.crear(self)

    def estas_en_primer_mitad(self):
        semanas_totales = self.residencia.SEMANAS_TOTALES
        semanas_mitad = semanas_totales // 2
        return self.fecha_inicio < self.generar_lunes(semanas_mitad)

    def cambiar_estado(self, estado):
        if self.estado is not None:
            self.estado.eliminar()

        self.estado = estado
        self.estado_id = estado.pk
        self.save()

    def es_actualizable(self):
        return self.estado.es_actualizable()

    def es_adquirible(self):
        return self.estado.es_adquirible()

    def actualizar(self):
        self.estado.actualizar()

    def jueves(self):
        return self.fecha_inicio + timedelta(days=3)

    @property
    def fecha_fin(self):
        return self.fecha_inicio + timedelta(days=6)

    def esta_concluida(self):
        return date.today() >= self.fecha_inicio

    def fecha_abrir_subasta(self):
        lunes = self.fecha_inicio - timedelta(weeks=25)
        return lunes

    def fecha_cerrar_subasta(self):
        jueves = self.fecha_abrir_subasta() + timedelta(days=3)
        return jueves

    def dar_de_baja(self):
        return self.estado.dar_de_baja()

    def abrir_subasta(self):
        return self.estado.abrir_subasta()

    def cerrar_subasta(self):
        return self.estado.cerrar_subasta()

    def establecer_hotsale(self):
        pass

    def comprar(self):
        pass

    def detalle_estado(self):
        return self.estado.detalle()

    def esta_en_subasta(self):
        return self.estado.es_subasta()

    def establecer_comprador(self, usuario):
        self.comprador = usuario
        self.save()

    def precio_base(self):
        return self.residencia.precio_base

    def cancelar_reserva(self):
        self.comprador.usuarioestandar.incrementar_credito()
        self.eliminar_comprador()
        self.save()

    def eliminar_comprador(self):
        self.comprador = None

    def agregar_seguidor(self, usuario):
        self.seguidores.add(usuario)
        self.save()

    def eliminar_seguidor(self, usuario):
        self.seguidores.remove(usuario)
        self.save()

    def es_seguida_por(self, usuario):
        return usuario in self.seguidores.all()

    def notificar_seguidores(self, mensaje):
        for seguidor in self.seguidores.all():
            seguidor.agregar_notificacion(
                mensaje=mensaje,
                semana=self
            )

    def notificaciones(self):
        return self.notificacion_set.all()

    def notificacion_url(self):
        return self.estado.notificacion_url()

    def __str__(self):
        return '{} - {}'.format(
            self.fecha_inicio, self.fecha_fin)

    class Meta:
        unique_together = ('content_type', 'estado_id')


class Estado(models.Model):

    semanas = GenericRelation(
        Semana,
        content_type_field='content_type',
        object_id_field='estado_id'
    )
    esta_eliminado = models.BooleanField(
        default=False
    )

    @classmethod
    def crear(cls, semana):
        if semana.estas_en_primer_mitad():
            estado = EnEspera.objects.create()
        else:
            estado = CompraDirecta.objects.create()
        semana.cambiar_estado(estado)

    @property
    def semana(self):
        return self.semanas.first()

    # Querys
    def es_compra_directa(self):
        return False

    def es_subasta(self):
        return False

    def es_no_disponible(self):
        return False

    def es_en_espera(self):
        return False

    def es_reservada(self):
        return False

    def es_hotsale(self):
        return False

    def es_actualizable(self):
        return False

    # Eventos
    def dar_de_baja(self):
        no_disponible = NoDisponible.objects.create()
        self.semana.cambiar_estado(no_disponible)
        return 'Se ha dado de baja la semana correctamente'

    def detalle(self):
        raise NotImplementedError('Método abstracto, implementame')

    def abrir_subasta(self):
        raise NotImplementedError('Método abstracto, implementame')

    def cerrar_subasta(self):
        raise NotImplementedError('Método abstracto, implementame')

    def es_adquirible(self):
        return self.es_subasta() or \
            self.es_compra_directa() or \
            self.es_hotsale()

    def actualizar(self):
        pass

    def eliminar(self):
        self.eliminar = True

    # Modelo
    def __str__(self):
        raise NotImplementedError('Método abstracto, implementame')

    def get_absolute_url(self):
        return reverse(self.url(), args=[str(self.pk)])

    def notificacion_url(self):
        return self.get_absolute_url()

    def url(self):
        raise NotImplementedError('Método abstracto, implementame')

    class Meta:
        abstract = True


class NoDisponible(Estado):

    def __str__(self):
        return 'No disponible'

    def es_no_disponible(self):
        return True

    def dar_de_baja(self):
        raise EventoNoPermitido('La semana ya se encuentra dada de baja')

    def abrir_subasta(self):
        pass

    def cerrar_subasta(self):
        pass

    def detalle(self):
        return 'Ha pasado la fecha de ocupación de la semana'

    def get_absolute_url(self):
        return ''


class CompraDirecta(Estado):

    NOTIFICACION = 'Se ha puesto en subasta'

    def __str__(self):
        return 'Compra directa'

    def es_compra_directa(self):
        return True

    def dar_de_baja(self):
        super().dar_de_baja()

    def abrir_subasta(self):
        subasta = Subasta.objects.create()
        self.semana.notificar_seguidores(self.NOTIFICACION)
        self.semana.cambiar_estado(subasta)
        return 'Se ha puesto la semana en subasta correctamente'

    def cerrar_subasta(self):
        pass

    def detalle(self):
        fecha_subasta = self.semana.fecha_abrir_subasta()
        return 'La semana entrará en subasta el día {}'.format(
            fecha_subasta.strftime("%A %d %B %Y - %H:%Mhs.")
        )

    def es_actualizable(self):
        lunes_espejo = date.today() + timedelta(weeks=25)
        return self.semana.fecha_inicio == lunes_espejo

    def actualizar(self):
        self.abrir_subasta()

    def generar_reserva(self, comprador):
        self.decrementar_credito(comprador)
        return self._crear_reserva(comprador)

    def decrementar_credito(self, comprador):
        if comprador.usuarioestandar.tenes_creditos():
            comprador.usuarioestandar.decrementar_credito()
        else:
            raise CreditosInsuficientes()

    def _crear_reserva(self, comprador):
        self.semana.establecer_comprador(comprador)
        reservada = Reservada.objects.create(
            precio_actual=self.semana.precio_base()
        )
        self.semana.cambiar_estado(reservada)
        return reservada

    def url(self):
        return 'mostrar_compra_directa'


class Subasta(Estado):
    fecha_inicio = models.DateField(
        default=date.today
    )
    fecha_cierre = models.DateField(
        default=date.today() + timedelta(days=3),
        null=True,
        blank=True
    )
    # Notificaciones
    NOTIFICACION_CIERRE = 'Se ha cerrado la subasta. {}'
    NOTIFICACION_GANADOR = NOTIFICACION_CIERRE.format('¡Hay ganador!')
    NOTIFICACION_NO_GANADOR = NOTIFICACION_CIERRE.format('¡No hay ganador!')
    NOTIFICACION_PUJA = '¡Han superado tu puja!'
    NOTIFICACION_PUJADOR_GANADOR = '¡Ganaste! Felicitaciones'

    def __str__(self):
        return 'Subasta'

    def es_subasta(self):
        return True

    def precio_minimo(self):
        return self.precio_actual() + 0.1

    def precio_actual(self):
        if self.hay_pujas():
            return self.puja_actual().monto
        else:
            return self.semana.precio_base()

    @property
    def pujas(self):
        return Puja.objects.filter(subasta=self)

    def puja_actual(self):
        return self.pujas.all().first()

    def hay_pujas(self):
        return bool(self.pujas)

    @property
    def ganador_actual(self):
        return self.puja_actual().pujador

    def nueva_puja(self, pujador, monto):
        self.verificar_pujador(pujador)
        if self.mismo_pujador(pujador):
            self.puja_actual().notificar_pujador(
                mensaje=self.NOTIFICACION_PUJA,
                semana=self.semana
            )
        Puja.objects.create(
            pujador=pujador,
            monto=monto,
            subasta=self
        )

    def verificar_pujador(self, pujador):
        if not pujador.tenes_creditos():
            raise CreditosInsuficientes

    def mismo_pujador(self, pujador):
        return self.hay_pujas() and not self.puja_actual().pujador_es(pujador)

    def hay_ganador_actual(self):
        return self.hay_pujas()

    def el_ganador_es(self, usuario):
        return self.ganador_actual == usuario

    def get_absolute_url(self):
        return reverse('mostrar_subasta', args=[str(self.pk)])

    def dar_de_baja(self):
        raise EventoNoPermitido('No se puede dar de baja una subasta activa')

    def abrir_subasta(self):
        pass

    def cerrar_subasta(self):
        if self.hay_pujas_validas():
            self.notificar(
                mensaje=self.NOTIFICACION_GANADOR
            )
            self.puja_ganadora().notificar_pujador(
                mensaje=self.NOTIFICACION_PUJADOR_GANADOR,
                semana=self.semana
            )
            reservada = self.puja_ganadora().generar_reserva(
                self.semana
            )
            self.semana.cambiar_estado(reservada)
        else:
            self.notificar(
                mensaje=self.NOTIFICACION_NO_GANADOR
            )
            en_espera = EnEspera.objects.create()
            self.semana.cambiar_estado(en_espera)

    def notificar(self, mensaje):
        self.semana.notificar_seguidores(
            mensaje=mensaje
        )
        self.notificar_pujadores(
            mensaje=mensaje
        )

    def notificar_pujadores(self, mensaje):
        for puja in self.pujas:
            puja.notificar_pujador(
                mensaje=mensaje,
                semana=self.semana
            )

    def hay_pujas_validas(self):
        return bool(self.pujas_validas())

    def pujas_validas(self):
        return list(filter(
            lambda puja: puja.es_valida(),
            self.pujas
        ))

    def puja_ganadora(self):
        return self.pujas_validas()[0]

    def detalle(self):
        fecha_cerrar_subasta = self.semana.fecha_cerrar_subasta()
        return 'La semana cerrará la subasta el día {}'.format(
            fecha_cerrar_subasta.strftime("%A %d %B %Y - %H:%Mhs.")
        )

    def es_actualizable(self):
        jueves_espejo = date.today() + timedelta(weeks=25)
        return self.semana.jueves() == jueves_espejo

    def actualizar(self):
        self.cerrar_subasta()

    def url(self):
        return 'mostrar_subasta'


class Puja(models.Model):
    pujador = models.ForeignKey(
        UsuarioEstandar,
        on_delete=models.CASCADE
    )
    monto = models.FloatField(
    )
    subasta = models.ForeignKey(
        Subasta,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-monto']

    def __str__(self):
        return '{}, {} ${}'.format(
            self.subasta.semana,
            self.pujador,
            self.monto
        )

    def es_valida(self):
        return self.pujador.tenes_creditos()

    def generar_reserva(self, semana):
        reserva = Reservada.objects.create(
            precio_actual=self.monto
        )
        semana.establecer_comprador(
            usuario=self.comprador()
        )
        self.pujador.decrementar_credito()
        return reserva

    def notificar_pujador(self, mensaje, semana):
        self.comprador().eliminar_notificacion(mensaje, semana.residencia)
        self.comprador().agregar_notificacion(mensaje, semana)

    def comprador(self):
        return CustomUser.objects.get(pk=self.pujador.pk)

    def pujador_es(self, otro_pujador):
        return self.pujador == otro_pujador


class EnEspera(Estado):

    def __str__(self):
        return 'En espera'

    def es_en_espera(self):
        return True

    def dar_de_baja(self):
        super().dar_de_baja()

    def abrir_subasta(self):
        pass

    def cerrar_subasta(self):
        pass

    def establecer_hotsale(self, descuento):
        hotsale = Hotsale.objects.create(descuento=descuento)
        self.semana.cambiar_estado(hotsale)
        return hotsale

    def detalle(self):
        return 'Decida si poner en HotSale la semana'

    def es_actualizable(self):
        return self.semana.fecha_inicio == date.today()

    def actualizar(self):
        no_disponible = NoDisponible.objects.create()
        self.semana.cambiar_estado(no_disponible)

    def url(self):
        return 'mostrar_en_espera'

    def notificacion_url(self):
        return ''


class Reservada(Estado):
    precio_actual = models.FloatField(
        null=True,
        blank=True
    )

    def __str__(self):
        return 'Reservada'

    def es_reservada(self):
        return True

    def actualizar(self):
        pass

    def dar_de_baja(self):
        raise EventoNoPermitido('La semana se encuentra reservada')

    def abrir_subasta(self):
        pass

    def cerrar_subasta(self):
        pass

    def cancelar(self):
        self.semana.cancelar_reserva()
        self.semana.cambiar_estado(EnEspera.objects.create())

    def detalle(self):
        return 'Semana reservada por {} {} con un monto de ${}'.format(
            self.semana.comprador.first_name,
            self.semana.comprador.last_name,
            self.precio_actual)

    def url(self):
        return 'mostrar_reservada'


class Hotsale(Estado):
    descuento = models.FloatField(
        null=True,
        blank=True
    )

    def __str__(self):
        return 'Hotsale'

    def abrir_subasta(self):
        pass

    def cerrar_subasta(self):
        pass

    def es_hotsale(self):
        return True

    def es_actualizable(self):
        return self.semana.fecha_inicio == date.today()

    def actualizar(self):
        no_disponible = NoDisponible.objects.create()
        self.semana.cambiar_estado(no_disponible)

    def generar_reserva(self, comprador):
        self.semana.establecer_comprador(comprador)
        reservada = Reservada.objects.create(
            precio_actual=self.precio_actual
        )
        self.semana.cambiar_estado(reservada)
        return reservada

    def detalle(self):
        return 'Semana en Hotsale por ${}'.format(self.precio_actual)

    @property
    def precio_actual(self):
        precio_base = self.semana.precio_base()
        return precio_base - precio_base * self.descuento / 100

    def precio_ahorro(self):
        precio_base = self.semana.precio_base()
        return precio_base - self.precio_actual

    def url(self):
        return 'mostrar_hotsale'


class Notificacion(models.Model):
    mensaje = models.CharField(
        max_length=255
    )
    semana = models.ForeignKey(
        Semana,
        on_delete=models.CASCADE,
    )
    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
    )
    creacion = models.DateTimeField(
        default=datetime.now
    )
    leida = models.BooleanField(
        default=False
    )

    class Meta():
        ordering = ['-creacion']

    @property
    def residencia(self):
        return self.semana.residencia

    def get_absolute_url(self):
        return self.semana.notificacion_url()

    def __str__(self):
        return self.mensaje.lower()
