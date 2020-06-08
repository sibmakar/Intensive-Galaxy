from django import forms
from django.core.mail import send_mail
import logging
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.forms import UsernameField
from . import models

logger = logging.getLogger(__name__)


class ContactForm(forms.Form):
    name = forms.CharField(label="Your Name", max_length=100)
    message = forms.CharField(max_length=600, widget=forms.Textarea)

    def send_mail(self):
        logger.info("Sending email to customer service")
        message = "From: {0}\n{1}".format(
            self.cleaned_data["name"], self.cleaned_data["message"]
        )
        send_mail(
            "Site message",
            message,
            "site@intensivegalaxy.domain",
            ["customerservice@intensivegalaxy.domain"],
            fail_silently=False,
        )


class UserCreationForm(DjangoUserCreationForm):
    class Meta(DjangoUserCreationForm.Meta):
        model = models.User
        fields = ("email",)
        field_classes = {"email": UsernameField}

    def send_mail(self):
        logger.info("Sending signup email for email=%s", self.cleaned_data["email"])
        message = "Welcome {}".format(self.cleaned_data["email"])
        send_mail(
            "Welcome to Intensive Galaxy",
            message,
            "site@intensive_galaxy.domain",
            [self.cleaned_data["email"]],
            fail_silently=True,
        )
