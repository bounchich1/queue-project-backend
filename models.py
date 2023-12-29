from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class User(models.Model):
    id = fields.IntField(pk=True)
    first_name = fields.CharField(max_length=100, null=True)
    last_name = fields.CharField(max_length=100, null=True)
    email = fields.CharField(max_length=150, unique=True, null=True)
    password = fields.CharField(max_length=60, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        exclude = ["password"]


class InfoQueue(models.Model):
    position = fields.IntField()
    first_name = fields.CharField(max_length=100, null=True)
    last_name = fields.CharField(max_length=100, null=True)
    task_number = fields.IntField()
    subject_number = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class PydanticMeta:
        exclude = []


User_Pydantic = pydantic_model_creator(User, name="User")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True, exclude=('created_at',))
InfoQueue_Pydantic = pydantic_model_creator(InfoQueue, name='InfoQueue')
InfoQueueIn_Pydantic = pydantic_model_creator(InfoQueue, name="InfoQueueIn", exclude_readonly=True,
                                              exclude=('created_at',
                                                       'modified_at',
                                                       'first_name',
                                                       'last_name',
                                                       'position'))
