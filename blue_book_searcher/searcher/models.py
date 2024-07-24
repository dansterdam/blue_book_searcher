# cases/models.py
from django.db import models
from django.urls import reverse

class Case(models.Model):
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    witnesses = models.CharField(max_length=255)
    text_content = models.TextField()
    #pdf = models.FileField(upload_to='pdfs/')

    def get_absolute_url(self):
        return reverse('case_detail', args=[self.id])
    
    def __str__(self):
        return self.title
