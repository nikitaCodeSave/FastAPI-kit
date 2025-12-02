"""
Фабрики тестовых данных.

Фабрики для создания тестовых данных. Рассмотрите использование:
- polyfactory: https://github.com/litestar-org/polyfactory
- factory_boy: https://github.com/FactoryBoy/factory_boy

Пример с polyfactory:

    from polyfactory.factories.pydantic_factory import ModelFactory
    from src.example.schemas import ExampleCreate

    class ExampleCreateFactory(ModelFactory):
        __model__ = ExampleCreate

    # Использование:
    example_data = ExampleCreateFactory.build()
"""

from src.example.schemas import ExampleCreate


def make_example_create(
    title: str = "Test Example",
    description: str | None = "Test description",
) -> ExampleCreate:
    """Создать схему ExampleCreate для тестирования."""
    return ExampleCreate(title=title, description=description)
