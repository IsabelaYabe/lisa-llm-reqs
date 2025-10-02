__version__ = "0.1.0"

from .models import Research, ResearchPaper
from .base import WebDriverConfig
from .base_source import BaseSource
from .ieee import IEEESources
from .acm import ACMSources

__all__ = ["__version__", "Research", "ResearchPaper", "WebDriverConfig", "BaseSource", "IEEESources", "ACMSources"]