# AI Agent Development Workflow

## Overview

This document provides a comprehensive workflow for AI agents (Claude Code, GitHub Copilot, etc.) to implement features in the Media Analyzer project following industry best practices for agentic coding.

## Pre-Implementation Checklist

### 1. Context Gathering ✅
Before writing any code, AI agents must:

- [ ] **Read Feature Requirement**: Complete FR-XXX document in `docs/requirements/feature-specifications/`
- [ ] **Review Project Overview**: Read `PROJECT_OVERVIEW.md` for overall context
- [ ] **Check Coding Standards**: Review `CODING_STANDARDS.md` for quality requirements
- [ ] **Study API Reference**: Check `docs/API_REFERENCE.md` for interface contracts
- [ ] **Review Related ADRs**: Read relevant Architecture Decision Records from `docs/adr/`

### 2. Pattern Recognition 🔍
Identify the appropriate patterns and templates:

- [ ] **Feature Type**: Determine if this is a core operation, plugin, CLI command, etc.
- [ ] **Template Selection**: Choose primary template from `templates/` directory
- [ ] **Example Study**: Review similar implementations in `examples/` directory
- [ ] **Integration Points**: Identify where this feature connects to existing system

### 3. Technical Preparation 🛠️
Set up the implementation approach:

- [ ] **Architecture Review**: Understand how this fits into overall architecture
- [ ] **Dependency Check**: Identify required dependencies and imports
- [ ] **Test Strategy**: Plan testing approach based on feature requirements
- [ ] **Error Handling**: Plan error scenarios and handling strategy

## Implementation Workflow

### Phase 1: Foundation Setup

#### Step 1.1: Create File Structure

#### Step 1.2: Set Up Imports and Basic Structure
```python
"""
[Feature Name] Implementation

Implements: [List relevant ADRs]
See: docs/requirements/feature-specifications/FR-XXX-[feature-name].md

Architecture: Follows [relevant ADR patterns]
"""

# Standard library imports
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Third-party imports (if needed)
import click  # For CLI features
import pytest  # For testing

# Project imports

# Set up logger
logger = get_logger(__name__)
```

#### Step 1.3: Create Basic Class Structure
```python
class [FeatureName]([BaseClass]):
    """
    [Feature description following docstring standards]
    
    Implements: [ADR references]
    
    Args:
        [parameter]: [description]
        
    Raises:
        [ExceptionType]: [when this exception is raised]
        
    Example:
        ```python
        feature = FeatureName()
        result = feature.method()
        ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize [FeatureName] with optional configuration."""
        super().__init__()
        self.config = config or {}
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        
        # TODO: Add feature-specific initialization
```

### Phase 2: Core Implementation

#### Step 2.1: Implement Core Methods
```python
def core_method(self, param1: Type1, param2: Type2) -> ReturnType:
    """
    [Method description]
    
    Args:
        param1: [description]
        param2: [description]
        
    Returns:
        ReturnType: [description]
        
    Raises:
        ValidationError: [when validation fails]
        OperationError: [when operation fails]
    """
    with LogContext(method="core_method", param1=param1, param2=param2):
        start_time = time.perf_counter()
        
        try:
            self.logger.debug("Starting core method execution")
            
            # Input validation
            self._validate_inputs(param1, param2)
            
            # Core logic implementation
            result = self._perform_operation(param1, param2)
            
            # Result validation
            self._validate_result(result)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.info(
                "Core method completed successfully",
                execution_time_ms=execution_time,
                result_type=type(result).__name__
            )
            
            return result
            
        except ValidationError:
            self.logger.warning("Input validation failed")
            raise
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(
                "Core method failed",
                error_type=type(e).__name__,
                error_message=str(e),
                execution_time_ms=execution_time
            )
            raise OperationError(
                f"Failed to execute core method: {str(e)}",
                original_error=e,
                context={"param1": param1, "param2": param2}
            )
```

#### Step 2.2: Implement Validation Methods
```python
def _validate_inputs(self, param1: Type1, param2: Type2) -> None:
    """Validate input parameters."""
    if param1 is None:
        raise ValidationError(
            "param1 cannot be None",
            field="param1",
            provided_value=param1
        )
    
    if not isinstance(param2, ExpectedType):
        raise ValidationError(
            f"param2 must be {ExpectedType.__name__}",
            field="param2",
            provided_value=param2,
            expected_type=ExpectedType.__name__
        )
    
    # Add feature-specific validation
```

#### Step 2.3: Implement Error Handling
```python
def _handle_operation_error(self, error: Exception, context: Dict[str, Any]) -> None:
    """Handle operation errors with proper logging and context."""
    error_context = {
        "operation": self.__class__.__name__,
        "error_type": type(error).__name__,
        "error_message": str(error),
        **context
    }
    
    if isinstance(error, ValidationError):
        self.logger.warning("Validation error occurred", **error_context)
    elif isinstance(error, SecurityError):
        self.logger.critical("Security error detected", **error_context)
    else:
        self.logger.error("Unexpected error occurred", **error_context)
```

### Phase 3: Integration Implementation

#### Step 3.1: CLI Integration (if applicable)
```python
# In separate CLI module or as part of main CLI
@click.command()
@click.option('--param1', type=str, required=True, help='Parameter 1 description')
@click.option('--param2', type=str, required=True, help='Parameter 2 description')
@click.pass_context
def feature_command(ctx, param1: str, param2: str):
    """CLI command for [feature name]."""
    try:
        feature = FeatureName()
        result = feature.core_method(param1, param2)
        
        click.echo(f"Result: {result}")
        
    except CalculatorError as e:
        click.echo(f"Error: {e.user_message}", err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        ctx.exit(1)
```

#### Step 3.2: Plugin Integration (if applicable)
```python
def register_with_plugin_system(self, registry: OperationRegistry) -> None:
    """Register this feature with the plugin system."""
    try:
        registry.register_operation(self.name, self)
        self.logger.info(
            "Feature registered with plugin system",
            feature_name=self.name,
            registry_size=len(registry.operations)
        )
    except Exception as e:
        self.logger.error(
            "Failed to register with plugin system",
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise PluginError(
            f"Failed to register {self.name}: {str(e)}",
            plugin_name=self.name,
            original_error=e
        )
```

### Phase 4: Testing Implementation

#### Step 4.1: Unit Tests
```python
"""Unit tests for [FeatureName]."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from calculator.[module] import FeatureName
from calculator.core.exceptions import ValidationError, OperationError

class TestFeatureName:
    """Test class for FeatureName."""
    
    @pytest.fixture
    def feature(self):
        """Create FeatureName instance for testing."""
        return FeatureName()
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "param1": "test_value",
            "param2": 42
        }
    
    def test_initialization(self):
        """Test FeatureName initialization."""
        feature = FeatureName()
        assert feature is not None
        assert hasattr(feature, 'config')
        assert hasattr(feature, 'logger')
    
    def test_core_method_success(self, feature):
        """Test successful core method execution."""
        result = feature.core_method("valid_input", 123)
        assert result is not None
        # Add specific assertions based on expected behavior
    
    def test_core_method_validation_error(self, feature):
        """Test core method with invalid input."""
        with pytest.raises(ValidationError) as exc_info:
            feature.core_method(None, 123)
        
        assert "param1 cannot be None" in str(exc_info.value)
    
    def test_core_method_operation_error(self, feature):
        """Test core method operation failure."""
        with patch.object(feature, '_perform_operation', side_effect=Exception("Test error")):
            with pytest.raises(OperationError) as exc_info:
                feature.core_method("valid_input", 123)
        
        assert "Failed to execute core method" in str(exc_info.value)
        assert "Test error" in str(exc_info.value)
    
    @pytest.mark.parametrize("input1,input2,expected", [
        ("test1", 1, "expected_result1"),
        ("test2", 2, "expected_result2"),
        ("test3", 3, "expected_result3"),
    ])
    def test_core_method_parametrized(self, feature, input1, input2, expected):
        """Test core method with various inputs."""
        # Mock the internal method to return expected results
        with patch.object(feature, '_perform_operation', return_value=expected):
            result = feature.core_method(input1, input2)
            assert result == expected
    
    def test_logging_integration(self, feature, caplog):
        """Test that logging works correctly."""
        with caplog.at_level(logging.INFO):
            result = feature.core_method("valid_input", 123)
        
        # Check that appropriate log messages were created
        assert "Starting core method execution" in caplog.text
        assert "Core method completed successfully" in caplog.text
    
    def test_performance_requirements(self, feature):
        """Test that performance requirements are met."""
        import time
        
        start_time = time.perf_counter()
        result = feature.core_method("valid_input", 123)
        execution_time = (time.perf_counter() - start_time) * 1000
        
        # Ensure execution time meets requirements (adjust threshold as needed)
        assert execution_time < 100  # 100ms threshold
```

#### Step 4.2: Integration Tests


#### Step 4.3: Performance Tests

### Phase 5: Documentation Implementation

#### Step 5.1: Update API Documentation


### Usage Examples


#### Step 5.2: Update User Documentation
```markdown
# Update README.md or user documentation

## [Feature Name] Usage

### Description


#### Step 5.3: Update Architecture Documentation


### Phase 6: Quality Assurance

#### Step 6.1: Automated Quality Checks


#### Step 6.2: Security Review


#### Step 6.3: Performance Validation


### Phase 7: Deployment Preparation

#### Step 7.1: Configuration Management

#### Step 7.2: Migration Strategy
```python
# If feature changes existing functionality
def migrate_existing_data():
    """Migration strategy for existing data/configuration."""
    # Handle backward compatibility
    # Migrate existing configurations
    # Update existing data structures
    pass
```

#### Step 7.3: Rollback Plan
```python
# Rollback strategy
def rollback_feature():
    """Rollback plan if feature needs to be disabled."""
    # Disable feature in configuration
    # Restore previous functionality
    # Clean up feature-specific data
    pass
```

## Quality Gates Checklist

Before considering a feature complete, AI agents must verify:

### Code Quality Gates ✅
- [ ] **Type Checking**: 100% mypy compliance with strict mode
- [ ] **Linting**: 100% ruff compliance with project configuration
- [ ] **
