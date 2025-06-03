"""
This module provides utility functions for configuring and managing loggers
within the personal agent package. The functions are used within the package to
convey logging information at a fine-grained level. The functions are completely
independent of the application and can be used in any Python project.

Author: Eric G. Suchanek, PhD
Last update: 2025-06-02 23:17:39
"""

import logging
import warnings

from rich.logging import RichHandler

from personal_agent.config.settings import LOG_LEVEL

DEFAULT_LOG_LEVEL = logging.WARNING


def set_logging_level_for_all_handlers(log_level: int):
    """
    Sets the logging level for all handlers of all loggers in the proteusPy package.

    :param log_level: The logging level to set.
    :type log_level: int
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    for logger_name in logging.Logger.manager.loggerDict:
        _logger = logging.getLogger(logger_name)
        _logger.setLevel(log_level)
        for handler in _logger.handlers:
            handler.setLevel(log_level)


def disable_stream_handlers_for_namespace(namespace: str):
    """
    Disables all stream handlers for all loggers under the specified namespace.

    :param namespace: The namespace whose stream handlers should be disabled.
    :type namespace: str
    """
    logger = logging.getLogger(namespace)
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            logger.removeHandler(handler)

    for logger_name in logging.Logger.manager.loggerDict:
        if logger_name.startswith(namespace):
            _logger = logging.getLogger(logger_name)
            for handler in _logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler):
                    _logger.removeHandler(handler)


def configure_master_logger(
    log_level: int = logging.ERROR,
    disabled: bool = False,
) -> None:
    """
    Configures the root logger with the specified settings.

    :param log_level: The logging level to set. Defaults to logging.ERROR.
    :type log_level: int
    :param disabled: If True, the logger will be disabled. Defaults to False.
    :type disabled: bool
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove all existing handlers
    # root_logger.handlers.clear()
    root_logger.disabled = disabled


def setup_logging_filters() -> None:
    """Set up logging configuration with Rich handler."""
    # Suppress warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="ollama")
    warnings.filterwarnings(
        "ignore", message=".*model_fields.*", category=DeprecationWarning
    )
    warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")
    warnings.filterwarnings(
        "ignore", category=ResourceWarning, message=".*subprocess.*"
    )

    # Reduce httpx logging verbosity to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)

    # Reduce Flask/Werkzeug logging verbosity to WARNING to reduce noise
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("flask").setLevel(logging.WARNING)
    logging.getLogger("flask.app").setLevel(logging.WARNING)
    logging.getLogger("werkzeug._internal").setLevel(logging.WARNING)

    # Also suppress other common noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return None


def setup_logging(
    name: str = __name__,
    level: int = LOG_LEVEL,
    propagate: bool = False,  # Default to False to avoid duplicates
) -> logging.Logger:
    """
    Returns a logger with the specified name, configured to use a RichHandler for console output.

    :param name: The name of the logger.
    :type name: str
    :param level: The logging level, defaults to LOG_LEVEL from config
    :type level: int
    :param propagate: Whether to propagate messages to parent loggers, defaults to False
    :type propagate: bool
    :return: Configured logger instance.
    :rtype: logging.Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Add RichHandler for console output
    rich_handler = RichHandler(rich_tracebacks=True)
    rich_formatter = logging.Formatter(
        "PersonalAgent: %(levelname)s %(asctime)s - %(name)s.%(funcName)s - %(message)s"
    )
    rich_handler.setLevel(level)
    rich_handler.setFormatter(rich_formatter)
    logger.addHandler(rich_handler)

    # Set propagation
    logger.propagate = propagate

    return logger


def set_logger_level(name, level):
    """
    Sets the logging level for the logger with the specified name.

    :param name: The name of the logger.
    :type name: str
    :param level: The logging level to set. Must be one of ["WARNING", "ERROR", "INFO", "DEBUG"].
    :type level: str
    :raises ValueError: If the provided level is not one of the allowed values.
    """
    level_dict = {
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }

    if level not in level_dict:
        raise ValueError(
            f"set_logger_level(): Invalid logging level: {level}. "
            "Must be one of ['WARNING', 'ERROR', 'INFO', 'DEBUG']"
        )

    _logger = logging.getLogger(name)
    _logger.setLevel(level_dict[level])

    for handler in _logger.handlers:
        handler.setLevel(level_dict[level])


def toggle_stream_handler(name, enable):
    """
    Enables or disables the StreamHandler for the logger with the specified name.

    :param name: The name of the logger.
    :type name: str
    :param enable: If True, enables the StreamHandler; if False, disables it.
    :type enable: bool
    """
    logger = logging.getLogger(name)
    stream_handler = None

    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            stream_handler = handler
            break

    if enable:
        if stream_handler is None:
            formatter = logging.Formatter(
                "PersonalAgent: %(levelname)-7s %(asctime)s - %(name)s.%(funcName)s - %(message)s"
            )
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logger.level)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
    else:
        if stream_handler is not None:
            logger.removeHandler(stream_handler)


def list_all_loggers():
    """
    Lists all loggers that have been created in the application.

    :return: List of logger names.
    :rtype: list
    """
    logger_dict = logging.Logger.manager.loggerDict
    loggers = [
        name
        for name, logger in logger_dict.items()
        if isinstance(logger, logging.Logger)
    ]
    return loggers


def list_handlers(name):
    """
    Lists the handlers for the logger with the specified name.

    :param name: The name of the logger.
    :type name: str
    :return: List of handler types and their configurations.
    :rtype: list
    """
    logger = logging.getLogger(name)
    handlers_info = []

    for handler in logger.handlers:
        handler_type = type(handler).__name__
        handler_info = {
            "type": handler_type,
            "level": logging.getLevelName(handler.level),
            "formatter": handler.formatter._fmt if handler.formatter else None,
        }
        handlers_info.append(handler_info)

    return handlers_info


def set_logger_level_for_module(pkg_name, level=""):
    """
    Set the logging level for all loggers within a specified package.

    This function iterates through all registered loggers and sets the logging
    level for those that belong to the specified package.

    :param pkg_name: The name of the package for which to set the logging level.
    :type pkg_name: str
    :param level: The logging level to set (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
                  If not specified, the logging level will not be changed.
    :type level: str, optional
    :return: A list of logger names that were found and had their levels set.
    :rtype: list
    """
    logger_dict = logging.Logger.manager.loggerDict
    registered_loggers = [
        name
        for name, logger in logger_dict.items()
        if isinstance(logger, logging.Logger) and name.startswith(pkg_name)
    ]
    for logger_name in registered_loggers:
        logger = logging.getLogger(logger_name)
        if level:
            logger.setLevel(level)

    return registered_loggers


if __name__ == "__main__":
    import doctest

    doctest.testmod()

# end of file
