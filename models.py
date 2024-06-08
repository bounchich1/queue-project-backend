from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class User(models.Model):
    id = fields.UUIDField(pk=True, auto_generate=True)
    first_name = fields.CharField(max_length=100, null=True)
    last_name = fields.CharField(max_length=100, null=True)
    group_id = fields.UUIDField(null=True)
    email = fields.CharField(max_length=150, unique=True, null=True)
    password = fields.CharField(max_length=60, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    subscription_expires = fields.DatetimeField(null=True)
    role = fields.CharField(max_length=50, null=False, default="user")

    class Meta:
        exclude = ["password"]


class InfoQueue(models.Model):
    user_id = fields.UUIDField()
    position = fields.IntField()
    group_id = fields.UUIDField()
    first_name = fields.CharField(max_length=100, null=True)
    last_name = fields.CharField(max_length=100, null=True)
    task_number = fields.IntField()
    subject_number = fields.UUIDField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class PydanticMeta:
        exclude = []


class Subjects(models.Model):
    id = fields.UUIDField(pk=True, auto_generate=True)
    group_id = fields.UUIDField()
    subject_full_name = fields.CharField(max_length=155, null=True)
    subject_short_name = fields.CharField(max_length=15, null=True)


class Tokens(models.Model):
    token = fields.CharField(max_length=100, null=False)
    remaining_activations = fields.IntField(null=False)
    group_id = fields.UUIDField()
    expires = fields.DatetimeField(null=False)
    owner_id = fields.UUIDField()


class Subscription(models.Model):
    expires = fields.DatetimeField(null=False)
    created_at = fields.DatetimeField()
    months = fields.IntField(null=False)
    group_population = fields.IntField(null=False)
    group_id = fields.UUIDField()
    owner_id = fields.UUIDField()
    tier = fields.IntField(null=False)


class Groups(models.Model):
    group_number = fields.CharField(null=False, max_length=15)
    group_id = fields.UUIDField(pk=True, auto_generate=True)


User_Pydantic = pydantic_model_creator(User, name="User")
UserOut_Pydantic = pydantic_model_creator(User, name='UserOut', exclude=('password', 'created_at'))
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True, exclude=('created_at',
                                                                                              'group_id',
                                                                                              'subscription_expires',
                                                                                              'role'))
InfoQueue_Pydantic = pydantic_model_creator(InfoQueue, name='InfoQueue')
InfoQueueIn_Pydantic = pydantic_model_creator(InfoQueue, name="InfoQueueIn", exclude_readonly=True,
                                              exclude=('created_at',
                                                       'modified_at',
                                                       'first_name',
                                                       'last_name',
                                                       'position',
                                                       'user_id',
                                                       'group_id',))
Subjects_Pydantic = pydantic_model_creator(Subjects, name="Subjects")
SubjectsIn_Pydantic = pydantic_model_creator(Subjects, name="SubjectsIn", exclude_readonly=True,
                                             exclude=('group_id', 'id'))
SubjectsUpd_Pydantic = pydantic_model_creator(Subjects, name="SubjectsUpd", exclude=('group_id',))
Tokens_Pydantic = pydantic_model_creator(Tokens, name="Tokens")
TokensIn_Pydantic = pydantic_model_creator(Tokens, name="TokensIn", exclude_readonly=True)


Subscription_Pydantic = pydantic_model_creator(Subscription, name="Subscription")
SubscriptionIn_Pydantic = pydantic_model_creator(Subscription, name="SubscriptionIn", exclude_readonly=True,
                                                 exclude=('created_at', 'owner_id', 'expires', 'group_id'))

Groups_Pydantic = pydantic_model_creator(Groups, name="Groups")
GroupsIn_Pydantic = pydantic_model_creator(Groups, name="GroupsIn", exclude_readonly=True, exclude=('group_id',))
