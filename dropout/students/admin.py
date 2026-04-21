from django.contrib import admin

from accounts.models import User

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "course",
        "gender",
        "age_at_enrollment",
        "target",
        "mentor",
        "parent",
        "scholarship_holder",
        "debtor",
        "tuition_fees_up_to_date",
    )
    list_filter = (
        "target",
        "course",
        "gender",
        "scholarship_holder",
        "debtor",
        "mentor",
        "parent",
    )
    search_fields = (
        "id",
        "course",
        "nacionality",
        "mentor__username",
        "parent__username",
    )
    list_editable = ("mentor",)
    list_per_page = 50
    list_select_related = ("mentor", "parent")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mentor":
            kwargs["queryset"] = User.objects.filter(role=User.ROLE_MENTOR).order_by(
                "username", "first_name", "last_name"
            )
            kwargs["empty_label"] = "— Choose mentor —"
        if db_field.name == "parent":
            kwargs["queryset"] = User.objects.filter(role=User.ROLE_PARENT).order_by(
                "username", "first_name", "last_name"
            )
            kwargs["empty_label"] = "— Choose parent —"
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name in ("mentor", "parent") and formfield:
            formfield.label_from_instance = lambda obj: User.natural_display(obj)
        return formfield
