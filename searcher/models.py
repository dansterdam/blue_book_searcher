# cases/models.py
from django.db import models
from django.urls import reverse
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class Case(models.Model):
    title = models.TextField(default="")
    summary = models.TextField(default="")
    location = models.TextField(default="")
    date = models.CharField()
    interesting_points = models.TextField(default="")
    sighted_object = models.TextField(default="")
    number_of_witnesses = models.TextField(default="")
    witness_description = models.TextField(default="")
    text_content = models.TextField()
    pdf = models.FileField(storage=S3Boto3Storage())

    def get_absolute_url(self):
        return reverse("case_detail", args=[self.id])

    def get_pdf_url(self):
        if self.pdf:
            return self.pdf.url
        return None

    def __str__(self):
        return self.title
