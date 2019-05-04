from django.db import models
from django.urls import reverse
import datetime


class Ubicacion(models.Model):
    pais = models.CharField(
        max_length=255
    )
    provincia = models.CharField(
        max_length=255
    )
    ciudad = models.CharField(
        max_length=255
    )
    calle = models.CharField(
        max_length=255
    )
    numero = models.IntegerField()

    def __str__(self):
        return "{calle} {numero}, {pais}, {provincia}, {ciudad}".format(
            pais=self.pais,
            provincia=self.provincia,
            ciudad=self.ciudad,
            calle=self.calle,
            numero=self.numero
        )


class Residencia(models.Model):
    nombre = models.CharField(
        max_length=255
    )
    semana_ocupacion = models.IntegerField(default=None)
    fecha_publicacion = models.DateField(
        default=datetime.date.today
    )
    foto = models.URLField()
    precio_base = models.FloatField(
        verbose_name="Precio"
    )
    descripcion = models.TextField(
        verbose_name="Descripción"
    )
    ubicacion = models.OneToOneField(
        Ubicacion,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    def __str__(self):
        return self.nombre

<<<<<<< HEAD
    def get_nombre(self):
        return self.nombre    

    class Meta:
        ordering = ['-fecha_publicacion', 'precio_base']
=======
    def get_absolute_url(self):
        return reverse('detalle_residencia', args=[str(self.id)])
>>>>>>> 9ef629c4b2c2efb1b4638a7d3ab7b844f785e2cd
