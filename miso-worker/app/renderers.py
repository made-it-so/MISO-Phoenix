import orjson
from rest_framework.renderers import BaseRenderer

class ORJSONRenderer(BaseRenderer):
    """
    Renderer which serializes to JSON using the high-performance orjson library.
    """
    media_type = 'application/json'
    format = 'json'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render  into JSON, returning a bytestring.
        """
        if data is None:
            return b''

        # orjson.dumps returns bytes, which is what the render method expects.
        # Using specific options for datetime handling to ensure consistency.
        # OPT_NAIVE_UTC: Assumes naive datetimes are in UTC.
        # OPT_UTC_Z: Appends 'Z' to UTC datetimes.
        return orjson.dumps(
            data,
            option=orjson.OPT_NAIVE_UTC | orjson.OPT_UTC_Z
        )
