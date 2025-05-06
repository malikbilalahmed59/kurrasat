from django import forms
from .models import Document, DocumentAnalysis

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'content']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'content': forms.Textarea(attrs={'rows': 10}),
        }

class DocumentAnalysisForm(forms.ModelForm):
    class Meta:
        model = DocumentAnalysis
        fields = ['analysis_text', 'suggestions']