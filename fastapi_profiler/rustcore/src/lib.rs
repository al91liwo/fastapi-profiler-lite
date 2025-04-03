use pyo3::{pymodule, PyResult, Python};
use pyo3::types::PyModule;

mod stats_aggregator;
use stats_aggregator::PyAggregatedStats;

#[pymodule]
fn fastapi_profiler_rust(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyAggregatedStats>()?;
    Ok(())
}