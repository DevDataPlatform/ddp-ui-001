from ninja import Field, Schema


class CreateDbtModelPayload(Schema):
    """
    schema to define the payload required to create a custom org task
    """

    name: str
    display_name: str
    config: dict
    op_type: str


class SyncSourcesSchema(Schema):
    """
    schema to sync sources from the schema
    """

    schema_name: str
    source_name: str