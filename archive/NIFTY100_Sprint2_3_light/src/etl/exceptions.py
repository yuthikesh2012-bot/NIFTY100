class ETLError(Exception):
    """Base ETL exception."""

class FileValidationError(ETLError):
    pass

class HeaderDetectionError(ETLError):
    pass
