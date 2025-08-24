# ADR-002: Plugin Architecture

## Status
Accepted

## Context
The media analyzer needs to support extensibility through plugins to allow for custom processors, new file formats, and alternative processing strategies without modifying the core codebase.

## Decision
We will implement a plugin system with the following key features:

1. **Plugin Structure**
```
media_analyzer/
├── plugins/
│   ├── base.py          # Plugin base classes
│   ├── registry.py      # Plugin registration
│   └── interfaces/      # Plugin interfaces
plugins/
├── custom_processor/    # Example external plugin
└── alternative_model/   # Example external plugin
```

2. **Plugin Types**
- Processors (audio, text)
- Models (analysis, recognition)
- Output Formatters
- Resource Providers

3. **Plugin Lifecycle**
- Discovery
- Registration
- Initialization
- Execution
- Cleanup

4. **Integration Patterns**
```python
class PluginBase(Protocol):
    """Base interface for all plugins."""
    @property
    def name(self) -> str:
        """Plugin identifier."""
        ...
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Plugin initialization."""
        ...
    
    def cleanup(self) -> None:
        """Resource cleanup."""
        ...
```

## Consequences

### Positive
- Easy extensibility
- Clean separation
- Version independence
- Community contributions
- Isolated testing

### Negative
- Versioning complexity
- Interface maintenance
- Performance overhead
- Security considerations

## Implementation Notes

1. **Plugin Registration**
   ```python
   class PluginRegistry:
       def __init__(self) -> None:
           self._plugins: Dict[str, Type[PluginBase]] = {}
   
       def register(self, plugin_class: Type[PluginBase]) -> None:
           """Register a plugin class."""
           self._plugins[plugin_class.name] = plugin_class
   
       def get_plugin(self, name: str) -> Optional[Type[PluginBase]]:
           """Get plugin by name."""
           return self._plugins.get(name)
   
   # Usage
   @plugin_registry.register
   class CustomProcessor(ProcessorPlugin):
       name = "custom_processor"
       # Implementation
   ```

2. **Plugin Discovery**
   ```python
   def discover_plugins(plugin_dir: str) -> None:
       """Discover and load plugins from directory."""
       sys.path.append(plugin_dir)
       for item in os.listdir(plugin_dir):
           if not item.endswith('.py'):
               continue
           
           module = importlib.import_module(
               item[:-3]  # Remove .py extension
           )
           
           # Plugin classes will self-register
           # through the @plugin_registry.register decorator
   ```

3. **Plugin Usage**
   ```python
   class Analyzer:
       def __init__(self, config: Dict[str, Any]) -> None:
           self.plugins = load_plugins(config)
   
       def process_file(self, file_path: str) -> AnalysisResult:
           processor = self.get_processor_for_file(file_path)
           with processor:  # Handles initialization and cleanup
               return processor.process(file_path)
   
       def get_processor_for_file(self, file_path: str) -> ProcessorPlugin:
           ext = os.path.splitext(file_path)[1].lower()
           processor_class = self.plugins.get_plugin_for_extension(ext)
           if not processor_class:
               raise ValueError(f"No processor for {ext} files")
           return processor_class()
   ```

4. **Plugin Configuration**
   ```python
   class PluginConfig(TypedDict):
       enabled: bool
       settings: Dict[str, Any]
       resources: Dict[str, str]
   
   def load_plugin_config() -> Dict[str, PluginConfig]:
       with open('plugins.yaml') as f:
           return yaml.safe_load(f)
   ```

## References
- Python Plugin Architecture Patterns
- [Core Architecture](ADR-001-core-architecture.md)
- [Type Safety](ADR-005-type-safety.md)
- [Testing Strategy](ADR-006-testing-strategy.md)
