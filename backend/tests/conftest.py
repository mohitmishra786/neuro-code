"""
NeuroCode Test Configuration.

Pytest fixtures and configuration.
Requires Python 3.11+.
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_python_code() -> str:
    """Sample Python code for testing."""
    return '''"""Sample module docstring."""

import os
from typing import List, Optional

class BaseClass:
    """A base class."""
    
    class_var: int = 42
    
    def __init__(self, name: str) -> None:
        """Initialize the class."""
        self.name = name
        self._private = None
    
    def method(self, value: int) -> str:
        """A simple method."""
        return str(value * 2)


class DerivedClass(BaseClass):
    """A derived class."""
    
    def __init__(self, name: str, count: int = 0) -> None:
        super().__init__(name)
        self.count = count
    
    async def async_method(self) -> List[str]:
        """An async method."""
        return [self.name] * self.count
    
    @property
    def display_name(self) -> str:
        """Property example."""
        return f"{self.name} ({self.count})"


def standalone_function(x: int, y: int = 10) -> int:
    """A standalone function."""
    result = x + y
    return result


async def async_generator(n: int):
    """Async generator function."""
    for i in range(n):
        yield i


# Module-level constants
CONSTANT_VALUE = 100
_PRIVATE_CONSTANT = "secret"
'''


@pytest.fixture
def temp_python_file(tmp_path: Path, sample_python_code: str) -> Path:
    """Create a temporary Python file for testing."""
    file_path = tmp_path / "sample.py"
    file_path.write_text(sample_python_code)
    return file_path


@pytest.fixture
def temp_package(tmp_path: Path, sample_python_code: str) -> Path:
    """Create a temporary Python package for testing."""
    package_dir = tmp_path / "sample_package"
    package_dir.mkdir()
    
    # Create __init__.py
    init_file = package_dir / "__init__.py"
    init_file.write_text('"""Package init."""\n\nfrom .module import DerivedClass\n')
    
    # Create module.py
    module_file = package_dir / "module.py"
    module_file.write_text(sample_python_code)
    
    # Create subpackage
    subpackage_dir = package_dir / "sub"
    subpackage_dir.mkdir()
    
    sub_init = subpackage_dir / "__init__.py"
    sub_init.write_text('"""Subpackage."""\n')
    
    sub_module = subpackage_dir / "helper.py"
    sub_module.write_text('''"""Helper module."""

def helper_function(value: str) -> str:
    """A helper function."""
    return value.upper()
''')
    
    return package_dir
