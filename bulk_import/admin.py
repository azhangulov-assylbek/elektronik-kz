from django.contrib import admin

from .models import ImportBatch, ImportRow


class ImportRowInline(admin.TabularInline):
    model = ImportRow
    extra = 0
    readonly_fields = ('row_number', 'raw_data', 'product', 'error')
    can_delete = False


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status',)
    search_fields = ('seller__email', 'seller__phone')
    inlines = [ImportRowInline]
