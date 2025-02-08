from peewee import DatabaseProxy, Model, AutoField


db = DatabaseProxy()


class BaseModel(Model):
    id = AutoField()

    class Meta:
        database = db
