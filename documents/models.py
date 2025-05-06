from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Document(models.Model):
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('archived', _('Archived')),
        ('pending', _('Pending')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents', verbose_name=_('User'))
    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'), blank=True, null=True)
    content = models.TextField(_('Content'), blank=True, null=True)
    file = models.FileField(_('File'), upload_to='documents/', blank=True, null=True)
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')

    def __str__(self):
        return self.title

class DocumentAnalysis(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='analyses', verbose_name=_('Document'))
    analysis_text = models.TextField(_('Analysis text'))
    suggestions = models.TextField(_('Suggestions'))
    analysis_date = models.DateTimeField(_('Analysis date'), auto_now_add=True)

    class Meta:
        verbose_name = _('Document analysis')
        verbose_name_plural = _('Document analyses')

    def __str__(self):
        return _("Analysis for {title}").format(title=self.document.title)