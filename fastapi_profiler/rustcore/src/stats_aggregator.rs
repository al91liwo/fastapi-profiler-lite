use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EndpointStats {
    pub method: String,
    pub path: String,
    pub count: usize,
    pub total: f64,
    pub min: f64,
    pub max: f64,
    pub response_times: Vec<f64>,
    pub rt_idx: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EndpointSummary {
    pub method: String,
    pub path: String,
    pub count: usize,
    pub avg: f64,
    pub min: f64,
    pub max: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MethodDistribution {
    pub method: String,
    pub count: usize,
}

#[pyclass]
pub struct PyAggregatedStats {
    endpoints: HashMap<String, EndpointStats>,
    methods: HashMap<String, usize>,
    total_requests: usize,
    total_time: f64,
    max_time: f64,
    response_buffer: Vec<f64>,
    buffer_size: usize,
    buffer_idx: usize,
    sorted_times: Option<Vec<f64>>,
}

// Implementation of Python methods for PyAggregatedStats
#[pymethods]
impl PyAggregatedStats {
    #[new]
    pub fn new(buffer_size: Option<usize>) -> Self {
        let buffer_size = buffer_size.unwrap_or(10000);
        PyAggregatedStats {
            endpoints: HashMap::new(),
            methods: HashMap::new(),
            total_requests: 0,
            total_time: 0.0,
            max_time: 0.0,
            response_buffer: vec![0.0; buffer_size],
            buffer_size,
            buffer_idx: 0,
            sorted_times: None,
        }
    }

    pub fn update(&mut self, profile: String) -> PyResult<()> {
        match serde_json::from_str(&profile) {
            Ok(profile_json) => {
                self.update_from_json(&profile_json);
                Ok(())
            },
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid JSON: {}", e)))
        }
    }
    
    pub fn update_stats(&mut self, method: &str, path: &str, time_secs: f64) -> PyResult<()> {
        self.update_internal(method, path, time_secs);
        Ok(())
    }
    
    pub fn update_batch(&mut self, requests: Vec<(&str, &str, f64)>) -> PyResult<()> {
        for (method, path, time_secs) in requests {
            self.update_internal(method, path, time_secs);
        }
        Ok(())
    }

    pub fn get_percentile(&mut self, percentile: f64) -> f64 {
        let valid_times: Vec<f64> = self.response_buffer
            .iter()
            .filter(|&&t| t > 0.0)
            .cloned()
            .collect();
        
        if valid_times.is_empty() {
            return 0.0;
        }
        
        if self.sorted_times.is_none() {
            let mut sorted = valid_times.clone();
            sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
            self.sorted_times = Some(sorted);
        }
        
        let sorted_times = self.sorted_times.as_ref().unwrap();
        let idx = ((percentile / 100.0) * sorted_times.len() as f64) as usize;
        let idx = idx.min(sorted_times.len() - 1);
        sorted_times[idx]
    }

    pub fn get_endpoint_stats(&self) -> PyResult<String> {
        let summaries: Vec<EndpointSummary> = self.endpoints
            .values()
            .map(|stats| EndpointSummary {
                method: stats.method.clone(),
                path: stats.path.clone(),
                count: stats.count,
                avg: stats.total / stats.count as f64,
                min: stats.min,
                max: stats.max,
            })
            .collect();
            
        match serde_json::to_string(&summaries) {
            Ok(json) => Ok(json),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Serialization error: {}", e)))
        }
    }

    pub fn get_slowest_endpoints(&self, limit: Option<usize>) -> PyResult<String> {
        let mut summaries: Vec<EndpointSummary> = self.endpoints
            .values()
            .map(|stats| EndpointSummary {
                method: stats.method.clone(),
                path: stats.path.clone(),
                count: stats.count,
                avg: stats.total / stats.count as f64,
                min: stats.min,
                max: stats.max,
            })
            .collect();
            
        summaries.sort_by(|a, b| b.avg.partial_cmp(&a.avg).unwrap_or(std::cmp::Ordering::Equal));
        summaries.truncate(limit.unwrap_or(5));
        
        match serde_json::to_string(&summaries) {
            Ok(json) => Ok(json),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Serialization error: {}", e)))
        }
    }

    pub fn get_method_distribution(&self) -> PyResult<String> {
        let distribution: Vec<MethodDistribution> = self.methods
            .iter()
            .map(|(method, count)| MethodDistribution {
                method: method.clone(),
                count: *count,
            })
            .collect();
            
        match serde_json::to_string(&distribution) {
            Ok(json) => Ok(json),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Serialization error: {}", e)))
        }
    }

    pub fn get_endpoint_distribution(&self, limit: Option<usize>) -> PyResult<String> {
        let mut summaries: Vec<EndpointSummary> = self.endpoints
            .values()
            .map(|stats| EndpointSummary {
                method: stats.method.clone(),
                path: stats.path.clone(),
                count: stats.count,
                avg: stats.total / stats.count as f64,
                min: stats.min,
                max: stats.max,
            })
            .collect();
            
        summaries.sort_by(|a, b| b.count.cmp(&a.count));
        summaries.truncate(limit.unwrap_or(10));
        
        match serde_json::to_string(&summaries) {
            Ok(json) => Ok(json),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Serialization error: {}", e)))
        }
    }

    pub fn get_avg_response_time(&self) -> f64 {
        if self.total_requests == 0 {
            return 0.0;
        }
        self.total_time / self.total_requests as f64
    }

    pub fn get_total_requests(&self) -> usize {
        self.total_requests
    }

    pub fn get_max_time(&self) -> f64 {
        self.max_time
    }

    pub fn get_unique_endpoints(&self) -> usize {
        self.endpoints.len()
    }
}

impl PyAggregatedStats {
    fn update_from_json(&mut self, profile: &serde_json::Value) {
        let method = profile["method"].as_str().unwrap_or("UNKNOWN").to_string();
        let path = profile["path"].as_str().unwrap_or("/").to_string();
        let time_value = profile["total_time"].as_f64().unwrap_or(0.0);
        
        self.update_internal(&method, &path, time_value);
    }
    
    fn update_internal(&mut self, method: &str, path: &str, time_value: f64) {
        let key = format!("{} {}", method, path);
        
        let endpoint = self.endpoints.entry(key).or_insert_with(|| EndpointStats {
            method: method.to_string(),
            path: path.to_string(),
            count: 0,
            total: 0.0,
            min: f64::INFINITY,
            max: 0.0,
            response_times: vec![0.0; 100],
            rt_idx: 0,
        });
        
        endpoint.count += 1;
        endpoint.total += time_value;
        endpoint.min = endpoint.min.min(time_value);
        endpoint.max = endpoint.max.max(time_value);
        
        endpoint.response_times[endpoint.rt_idx] = time_value;
        endpoint.rt_idx = (endpoint.rt_idx + 1) % 100;
        
        *self.methods.entry(method.to_string()).or_insert(0) += 1;
        
        self.total_requests += 1;
        self.total_time += time_value;
        self.max_time = self.max_time.max(time_value);
        
        self.response_buffer[self.buffer_idx] = time_value;
        self.buffer_idx = (self.buffer_idx + 1) % self.buffer_size;
        
        self.sorted_times = None;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_update_stats() {
        let mut stats = PyAggregatedStats::new(Some(1000));
        
        stats.update_stats("GET", "/test", 0.5).unwrap();
        
        assert_eq!(stats.get_total_requests(), 1);
        assert_eq!(stats.get_avg_response_time(), 0.5);
        assert_eq!(stats.get_max_time(), 0.5);
        
        let endpoint_stats = serde_json::from_str::<Vec<EndpointSummary>>(&stats.get_endpoint_stats().unwrap()).unwrap();
        assert_eq!(endpoint_stats.len(), 1);
        assert_eq!(endpoint_stats[0].method, "GET");
        assert_eq!(endpoint_stats[0].path, "/test");
        assert_eq!(endpoint_stats[0].count, 1);
        assert_eq!(endpoint_stats[0].avg, 0.5);
    }

    #[test]
    fn test_percentiles() {
        let mut stats = PyAggregatedStats::new(Some(1000));
        
        for i in 1..=100 {
            stats.update_stats("GET", "/test", i as f64 / 100.0).unwrap();
        }
        
        assert_eq!(stats.get_percentile(50.0), 0.5);
        assert_eq!(stats.get_percentile(90.0), 0.9);
        assert_eq!(stats.get_percentile(95.0), 0.95);
        assert_eq!(stats.get_percentile(100.0), 1.0);
    }

    #[test]
    fn test_batch_update() {
        let mut stats = PyAggregatedStats::new(Some(1000));
        
        let batch = vec![
            ("GET", "/users", 0.1),
            ("POST", "/items", 0.2),
            ("PUT", "/orders", 0.3),
        ];
        
        stats.update_batch(batch).unwrap();
        
        assert_eq!(stats.get_total_requests(), 3);
        assert_eq!(stats.get_unique_endpoints(), 3);
        
        let method_distribution = serde_json::from_str::<Vec<MethodDistribution>>(&stats.get_method_distribution().unwrap()).unwrap();
        assert_eq!(method_distribution.len(), 3);
    }
}
