from typing import Any

from django import forms

from .models import MAPPABLE_FIELDS

IGNORE_COLUMN = ''


class BatchUploadForm(forms.Form):
    file = forms.FileField(label='Файл каталога (CSV или .xlsx)')


class ColumnMappingForm(forms.Form):
    """Динамическая форма: по одному select-полю на каждую колонку файла."""

    def __init__(self, *args: Any, headers: list[str] | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        choices = [(IGNORE_COLUMN, '— игнорировать —')] + list(MAPPABLE_FIELDS.items())
        for index, header in enumerate(headers or []):
            self.fields[f'column_{index}'] = forms.ChoiceField(
                label=header or f'Колонка {index + 1}',
                choices=choices,
                required=False,
            )

    def get_mapping(self) -> dict[str, str]:
        """{'0': 'name', '2': 'price', ...} — только реально сопоставленные колонки."""
        mapping: dict[str, str] = {}
        for name, value in self.cleaned_data.items():
            if value:
                index = name.removeprefix('column_')
                mapping[index] = value
        return mapping


class RowImageForm(forms.Form):
    image = forms.ImageField(label='Картинка товара')


class RejectBatchForm(forms.Form):
    rejection_reason = forms.CharField(
        label='Причина отклонения', widget=forms.Textarea(attrs={'rows': 3}), required=False,
    )
