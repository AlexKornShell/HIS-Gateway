from django.db import models
from django.urls import reverse
from django.utils import timezone


class RequestToHIS(models.Model):
    """
    Model representing a request.
    """
    source = models.CharField(max_length=50)
    url = models.CharField(max_length=50)
    method = models.CharField(max_length=10)
    date_time = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        """
        String for representing the Model object.
        """
        return 'Request from ' + str(self.source) + ' to ' + str(self.url)
    
    
    def get_absolute_url(self):
        """
        Returns the url to access a particular request instance.
        """
        return reverse('request-detail', args=[str(self.id)])