from django import forms
from .models import Store, Product, Assistant


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'kind', 'description', 'price', 'available']
        widgets = {'description': forms.Textarea(attrs={'rows': 3}),
                   'price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'})}


class AssistantForm(forms.ModelForm):
    class Meta:
        model = Assistant
        fields = ['name', 'greeting', 'tone']
        widgets = {'greeting': forms.Textarea(attrs={'rows': 3})}


class QuestionForm(forms.Form):
    question = forms.CharField(label='پیام شما', max_length=500,
                              widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'مثلاً قیمت قهوه عربیکا چقدر است؟'}))
