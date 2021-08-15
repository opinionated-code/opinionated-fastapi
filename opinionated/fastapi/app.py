"""Default app module used if there isn't a custom one defined and referenced in the settings object.

This module defines an 'app' variable that is a default instance of the OpinionatedFastAPI class.
If an application wants to define custom behaviour, it can create its own app.py and sub-class OpinionatedFastAPI,
otherwise this module provides a sensible default option.
"""

from opinionated.fastapi.bootstrap import OpinionatedFastAPI

app = OpinionatedFastAPI()
