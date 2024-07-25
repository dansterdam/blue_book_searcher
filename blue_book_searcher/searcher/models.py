# cases/models.py
from django.db import models
from django.urls import reverse

class Case(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField(default='')
    location = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    witnesses = models.CharField(max_length=255)
    text_content = models.TextField()
    pdf = models.FileField(upload_to='casefiles/pdfs/',default='')

    def get_absolute_url(self):
        return reverse('case_detail', args=[self.id])
    
    def get_pdf_url(self):
        if self.pdf:
            return reverse('serve_pdf', args=[self.id])
        return ''
    
    def __str__(self):
        return self.title
