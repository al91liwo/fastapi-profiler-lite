use pyo3::{pymodule, PyResult, Python};
use pyo3::types::PyModule;

mod stats_aggregator;
use stats_aggregator::PyAggregatedStats;

#[pymodule]
fn rustcore(_py: Python<'_>, m: &PyModule) -> PyResult<()> {  // Changed name to match Cargo.toml
    m.add_class::<PyAggregatedStats>()?;
    Ok(())
}