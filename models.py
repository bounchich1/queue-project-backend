from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class User(models.Model):
    id = fields.IntField(pk=True)
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=150, unique=True)
    password = fields.CharField(max_length=128)
    created_at = fields.DatetimeField(auto_now_add=True)

    class PydanticMeta:
        exclude = ("password_hash", "created_at")


class InfoQueue(models.Model):
    id = fields.IntField(pk=True)
    queued_person = fields.CharField(max_length=255, null=True)
    task_number = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class PydanticMeta:
        exclude = ('queued_person', 'created_at')


User_Pydantic = pydantic_model_creator(User, name="User")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)
InfoQueue_Pydantic = pydantic_model_creator(InfoQueue, name='InfoQueue')
InfoQueueIn_Pydantic = pydantic_model_creator(InfoQueue, name="InfoQueueIn", exclude_readonly=True)
