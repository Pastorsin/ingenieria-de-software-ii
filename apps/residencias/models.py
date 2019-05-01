from django.db import models
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
        return "{calle} {numero}, {pais}, {provincia}, {ciudad},".format(
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
    fecha_ocupacion = models.DateField(
        default=datetime.date.today
    )
    fecha_publicacion = models.DateField(
        default=datetime.date.today
    )
    ubicacion = models.OneToOneField(
        Ubicacion,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    foto = models.URLField()
    precioBase = models.FloatField()
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre
