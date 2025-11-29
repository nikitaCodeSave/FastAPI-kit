import structlog

# Для разработки — красивый консольный вывод
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.dev.ConsoleRenderer(colors=True),  # Финальный
    ]
)

# Для production — JSON
# structlog.configure(
#     processors=[
#         structlog.processors.add_log_level,
#         structlog.processors.TimeStamper(fmt="iso"),
#         structlog.processors.JSONRenderer(),  # Финальный
#     ]
# )


logger = structlog.get_logger()
user = "nikita"
logger.info("hello, %s!", user=user)
