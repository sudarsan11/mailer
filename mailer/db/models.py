from django.db import models

class User(models.Model):
    email = models.CharField(max_length=254, unique=True)
    username = models.CharField(max_length=254, unique=True)

class Message(models.Model):
    message_id = models.TextField(unique=True)
    thread_id = models.TextField(unique=True)
    history_id = models.TextField()
    size_estimate = models.IntegerField()
    internal_date = models.DateTimeField()
    snippet = models.TextField()
    user_id = models.ManyToManyField(User, through='UserMessage')
    labels = models.ManyToManyField('Label', related_name='labels')    

class UserMessage(models.Model):

    class UserTypes(models.TextChoices):
        SENDER = "SENDER"
        RECIPIENT = "RECIPIENT"

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    message_id = models.ForeignKey(Message, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=40, choices=UserTypes.choices)

class Label(models.Model):
    class LabelTypes(models.TextChoices):
        SYSTEM = "SYSTEM"
        USER = "USER"

    name = models.CharField(max_length=100, unique=True)
    label_name = models.CharField(max_length=100, unique=True)
    label_type = models.CharField(max_length=20, choices=LabelTypes.choices)
    message_list_visibility = models.CharField(max_length=100, null=True)
    label_list_visibility = models.CharField(max_length=100, null=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

class MessageHeaderValues(models.Model):
    message_id = models.ForeignKey(Message, on_delete=models.CASCADE)
    header = models.CharField(max_length=100)
    value = models.TextField()

    class Meta:
        unique_together = ('message_id', 'header', 'value',)
