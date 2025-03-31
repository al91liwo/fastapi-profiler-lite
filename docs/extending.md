# Extending FastAPI Profiler

FastAPI Profiler is designed to be extensible. This guide outlines the key extension points.

## Extension Points

### Custom Metrics

You can extend the `RequestProfiler` class to track additional metrics beyond the default ones. This allows you to monitor specific aspects of your application's performance that matter to your use case.

### Dashboard Customization

The dashboard UI can be extended with custom visualizations. By adding your own charts or modifying existing ones, you can create views that highlight the metrics most important to your team.

### Middleware Extensions

The profiler middleware can be extended to capture additional context about requests and responses. This is useful for correlating performance data with business metrics or user behavior.

### Plugin System

For more complex extensions, you can implement a plugin architecture that hooks into various points in the request lifecycle. This allows for modular, reusable extensions that can be shared across projects.

## When to Extend

Consider extending FastAPI Profiler when:

- You need to track domain-specific metrics
- You want to correlate performance with business outcomes
- You need to integrate with other monitoring systems
- You want to add custom alerting or thresholds

## Contributing Extensions

If you develop a useful extension, consider contributing it back to the project! See the [Contributing Guide](contributing.md) for details on how to submit your extensions for inclusion in the main project.
