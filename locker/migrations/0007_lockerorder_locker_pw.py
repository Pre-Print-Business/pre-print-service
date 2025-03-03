# Generated by Django 4.2.3 on 2025-03-01 11:24

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("locker", "0006_rename_locket_status_lockerorder_locker_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="lockerorder",
            name="locker_pw",
            field=models.CharField(
                default="1234",
                max_length=4,
                validators=[
                    django.core.validators.RegexValidator(
                        message="비밀번호는 4자리 숫자여야 합니다.", regex="^\\d{4}$"
                    )
                ],
                verbose_name="사물함 비밀번호",
            ),
        ),
    ]
