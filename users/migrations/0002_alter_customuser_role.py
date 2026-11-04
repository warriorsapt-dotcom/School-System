from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('users', '0001_initial')]
    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('admin', 'Administrator'), ('principal', 'Principal / Head Teacher'), ('teacher', 'Teacher'), ('student', 'Student')], default='student', max_length=20),
        ),
    ]
