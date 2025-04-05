// Global state
let dashboardData = {};
let refreshInterval;
let apiPath = '';
let currentSortColumn = 'timestamp';
let currentSortDirection = 'desc';

// Chart instances
let responseTimeChart;
let requestsByMethodChart;
let endpointDistributionChart;
let statusCodeChart;

// Simple formatter for time display
const formatTime = (ms) => ms.toFixed(2);

// Format relative time for better readability
const formatTimeAgo = (timestamp) => {
    if (!timestamp) return '-';
    const date = new Date(parseInt(timestamp * 1000));
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);

    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return date.toLocaleString();
};

// Function to handle Tabler's tab system
function setupTablerTabs() {
    // Tabler uses Bootstrap's tab system which is already initialized via the CDN
    // We just need to handle our own tab content visibility when tabs are clicked
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (e) {
            // This event is fired after a tab is shown
            // We don't need to manually show/hide content as Bootstrap handles it
            
            // Update charts when tabs are shown
            if (e.target.getAttribute('href') === '#tab-overview') {
                updateCharts();
            } else if (e.target.getAttribute('href') === '#tab-endpoints') {
                updateEndpointDistributionChart();
            }
        });
    });
}

// Loading indicator functions
function showLoadingIndicator() {
    document.body.classList.add('layout-loading');
}

function hideLoadingIndicator() {
    document.body.classList.remove('layout-loading');
}

// Global flag to prevent updates during user interaction
let isUserInteracting = false;
let pendingDataUpdate = false;
let lastDataTimestamp = 0;

// Fetch dashboard data from API
async function fetchData() {
    try {
        // Don't show loading indicator if user is interacting
        if (!isUserInteracting) {
            showLoadingIndicator();
        }
        
        const response = await fetch(`${apiPath.replace('/profiles', '')}/api/dashboard-data`);
        if (!response.ok) {
            console.error('Failed to fetch data:', response.statusText);
            if (!isUserInteracting) hideLoadingIndicator();
            return false;
        }

        const newData = await response.json();
        
        // Check if we have new data
        const hasNewData = !dashboardData.timestamp || 
                          newData.timestamp > dashboardData.timestamp;
        
        if (hasNewData) {
            // Store the timestamp for comparison
            lastDataTimestamp = newData.timestamp;
            
            // Update data
            dashboardData = newData;
            
            // Only update UI if user is not interacting
            if (!isUserInteracting) {
                updateDashboard();
            } else {
                // Mark that we have pending updates
                pendingDataUpdate = true;
            }
        }
        
        // Record the update time
        chartState.lastUpdateTime = Date.now();
        
        if (!isUserInteracting) hideLoadingIndicator();
        
        return hasNewData;
    } catch (error) {
        console.error('Error fetching data:', error);
        if (!isUserInteracting) hideLoadingIndicator();
        return false;
    }
}

// Update all dashboard components with new data
function updateDashboard() {
    if (!dashboardData.timestamp) {
        console.log('No dashboard data available');
        return;
    }

    // Update all dashboard sections
    updateStats();
    updateSlowestEndpointsTable();
    updateEndpointsTable();
    updateRequestsTable();
    updateCharts();
}

// Update stat cards
function updateStats() {
    const stats = dashboardData.overview;
    document.getElementById('stat-total-requests').textContent = stats.total_requests;
    document.getElementById('stat-avg-response-time').textContent = formatTime(stats.avg_response_time) + ' ms';
    document.getElementById('stat-p90-response-time').textContent = formatTime(stats.p90_response_time) + ' ms';
    document.getElementById('stat-p95-response-time').textContent = formatTime(stats.p95_response_time) + ' ms';
    document.getElementById('stat-max-response-time').textContent = formatTime(stats.max_response_time) + ' ms';
    document.getElementById('stat-unique-endpoints').textContent = stats.unique_endpoints;
}

// Update slowest endpoints table
function updateSlowestEndpointsTable() {
    const slowestEndpoints = dashboardData.endpoints.slowest || [];
    const tableBody = document.getElementById('slowest-endpoints-table').querySelector('tbody');
    tableBody.innerHTML = '';

    slowestEndpoints.forEach(stat => {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td class="text-gray-700">${stat.method}</td>
            <td class="font-medium text-gray-900">${stat.path}</td>
            <td class="text-indigo-600 font-medium">${formatTime(stat.avg * 1000)} ms</td>
            <td class="text-red-600">${formatTime(stat.max * 1000)} ms</td>
            <td class="text-gray-500">${stat.count}</td>
        `;

        tableBody.appendChild(row);
    });

    if (slowestEndpoints.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-gray-500">No data available</td></tr>`;
    }
}

// Global pagination state
let paginationState = {
    endpointsPage: 1,
    endpointsPerPage: 10,
    requestsPage: 1,
    requestsPerPage: 10
};

// Update endpoints table with pagination and grouping
function updateEndpointsTable() {
    let endpointStats = [...dashboardData.endpoints.stats];
    const searchTerm = document.getElementById('endpoint-search')?.value?.toLowerCase() || '';

    // Apply search filter
    if (searchTerm) {
        endpointStats = endpointStats.filter(stat => 
            stat.path.toLowerCase().includes(searchTerm) || 
            stat.method.toLowerCase().includes(searchTerm)
        );
    }

    // Group endpoints by path pattern
    const groupedEndpoints = groupEndpointsByPattern(endpointStats);
    let groupedStats = [];
    
    // Convert grouped data to flat array for display
    Object.entries(groupedEndpoints).forEach(([pattern, endpoints]) => {
        // If there's only one endpoint in the group, just add it directly
        if (endpoints.length === 1) {
            groupedStats.push(endpoints[0]);
            return;
        }
        
        // For multiple endpoints with the same pattern, create a summary row
        const totalCount = endpoints.reduce((sum, ep) => sum + ep.count, 0);
        const avgTime = endpoints.reduce((sum, ep) => sum + (ep.avg * ep.count), 0) / totalCount;
        const maxTime = Math.max(...endpoints.map(ep => ep.max));
        const minTime = Math.min(...endpoints.map(ep => ep.min));
        
        // Get unique methods for this pattern
        const uniqueMethods = [...new Set(endpoints.map(ep => ep.method))].join(', ');
        
        // Add a summary row with the pattern
        groupedStats.push({
            method: uniqueMethods,
            path: pattern,
            avg: avgTime,
            max: maxTime,
            min: minTime,
            count: totalCount,
            isGroup: true,
            endpoints: endpoints
        });
    });
    
    // Apply sorting
    if (currentSortColumn) {
        groupedStats.sort((a, b) => {
            let valA, valB;

            switch(currentSortColumn) {
                case 'method': valA = a.method; valB = b.method; break;
                case 'path': valA = a.path; valB = b.path; break;
                case 'avg': valA = a.avg; valB = b.avg; break;
                case 'max': valA = a.max; valB = b.max; break;
                case 'min': valA = a.min; valB = b.min; break;
                case 'count': valA = a.count; valB = b.count; break;
                default: valA = a.avg; valB = b.avg;
            }

            if (typeof valA === 'string') {
                return currentSortDirection === 'asc' 
                    ? valA.localeCompare(valB) 
                    : valB.localeCompare(valA);
            } else {
                return currentSortDirection === 'asc' 
                    ? valA - valB 
                    : valB - valA;
            }
        });
    }

    const tableBody = document.getElementById('endpoints-table').querySelector('tbody');
    tableBody.innerHTML = '';
    
    // Calculate pagination
    const totalPages = Math.ceil(groupedStats.length / paginationState.endpointsPerPage);
    
    // Ensure current page is valid
    if (paginationState.endpointsPage > totalPages) {
        paginationState.endpointsPage = Math.max(1, totalPages);
    }
    
    // Get current page data
    const startIndex = (paginationState.endpointsPage - 1) * paginationState.endpointsPerPage;
    const endIndex = startIndex + paginationState.endpointsPerPage;
    const currentPageData = groupedStats.slice(startIndex, endIndex);

    // Render table rows
    currentPageData.forEach(stat => {
        const row = document.createElement('tr');
        
        // Add a class for group rows
        if (stat.isGroup) {
            row.classList.add('group-row');
        }

        row.innerHTML = `
            <td class="text-gray-700">${stat.method}</td>
            <td class="font-medium text-gray-900">${stat.path}</td>
            <td class="text-indigo-600 font-medium">${formatTime(stat.avg * 1000)} ms</td>
            <td class="text-red-600">${formatTime(stat.max * 1000)} ms</td>
            <td class="text-green-600">${formatTime(stat.min * 1000)} ms</td>
            <td class="text-gray-500">${stat.count}</td>
        `;

        tableBody.appendChild(row);
        
        // If this is a group row and it has endpoints, add a hidden expandable section
        if (stat.isGroup && stat.endpoints && stat.endpoints.length > 1) {
            const detailRow = document.createElement('tr');
            detailRow.classList.add('endpoint-details');
            detailRow.style.display = 'none';
            
            const detailCell = document.createElement('td');
            detailCell.colSpan = 6;
            detailCell.classList.add('p-0');
            
            let detailContent = `
                <div class="p-3 bg-gray-50">
                    <div class="text-sm font-medium mb-2">Endpoints in this group:</div>
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Method</th>
                                <th>Path</th>
                                <th>Avg Time</th>
                                <th>Count</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            stat.endpoints.forEach(endpoint => {
                detailContent += `
                    <tr>
                        <td>${endpoint.method}</td>
                        <td>${endpoint.path}</td>
                        <td>${formatTime(endpoint.avg * 1000)} ms</td>
                        <td>${endpoint.count}</td>
                    </tr>
                `;
            });
            
            detailContent += `
                        </tbody>
                    </table>
                </div>
            `;
            
            detailCell.innerHTML = detailContent;
            detailRow.appendChild(detailCell);
            tableBody.appendChild(detailRow);
            
            // Add click handler to toggle details
            row.style.cursor = 'pointer';
            row.addEventListener('click', () => {
                const isVisible = detailRow.style.display !== 'none';
                detailRow.style.display = isVisible ? 'none' : 'table-row';
            });
        }
    });

    if (groupedStats.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-gray-500">No data available</td></tr>`;
    }
    
    // Update pagination controls
    updatePaginationControls('endpoints-pagination', totalPages, paginationState.endpointsPage, (page) => {
        paginationState.endpointsPage = page;
        updateEndpointsTable();
    });
}

// Helper function to group endpoints by pattern
function groupEndpointsByPattern(endpoints) {
    const groups = {};
    
    endpoints.forEach(endpoint => {
        // Use the original path as the pattern by default
        // This ensures endpoints like /fast, /slow, /users are not grouped together
        let pattern = endpoint.path;
        
        // Only apply pattern matching for paths that look like they contain parameters
        if (pattern.includes('/') && 
            (
                // Has numeric segments that look like IDs
                /\/\d+/.test(pattern) || 
                // Has UUID-like segments
                /\/[0-9a-f]{8}-[0-9a-f]{4}/.test(pattern) ||
                // Has segments that look like slugs with IDs
                /\/[^/]+-[a-z0-9]{8,}/.test(pattern) ||
                // Has query parameters
                pattern.includes('?')
            )
        ) {
            // Replace numeric IDs with {id}
            pattern = pattern.replace(/\/\d+(?=\/|$)/g, '/{id}');
            
            // Replace UUIDs with {uuid}
            pattern = pattern.replace(/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?=\/|$)/gi, '/{uuid}');
            
            // Match CMS-style slugs (e.g., /blog-post-title-123abc/)
            pattern = pattern.replace(/\/[^/]+-[a-z0-9]{8,}(?=\/|$)/gi, '/{slug}');
            
            // Match query parameters in paths
            pattern = pattern.replace(/\?.*$/, '?{query}');
        }
        
        // Initialize group if it doesn't exist
        if (!groups[pattern]) {
            groups[pattern] = [];
        }
        
        // Add endpoint to group
        groups[pattern].push(endpoint);
    });
    
    return groups;
}

// Helper function to update pagination controls
function updatePaginationControls(containerId, totalPages, currentPage, onPageChange) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    if (totalPages <= 1) return;
    
    // Previous button
    const prevBtn = document.createElement('a');
    prevBtn.href = '#';
    prevBtn.className = 'page-link' + (currentPage === 1 ? ' disabled' : '');
    prevBtn.innerHTML = '<i class="ti ti-chevron-left"></i>';
    prevBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage > 1) onPageChange(currentPage - 1);
    });
    
    // Next button
    const nextBtn = document.createElement('a');
    nextBtn.href = '#';
    nextBtn.className = 'page-link' + (currentPage === totalPages ? ' disabled' : '');
    nextBtn.innerHTML = '<i class="ti ti-chevron-right"></i>';
    nextBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage < totalPages) onPageChange(currentPage + 1);
    });
    
    // Page info
    const pageInfo = document.createElement('span');
    pageInfo.className = 'mx-2';
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    
    // Append elements
    container.appendChild(prevBtn);
    container.appendChild(pageInfo);
    container.appendChild(nextBtn);
}

// Update requests table with pagination
function updateRequestsTable() {
    let recentRequests = [...dashboardData.requests.recent];
    const searchTerm = document.getElementById('request-search')?.value?.toLowerCase() || '';

    // Apply search filter
    if (searchTerm) {
        recentRequests = recentRequests.filter(profile => 
            profile.path.toLowerCase().includes(searchTerm) || 
            profile.method.toLowerCase().includes(searchTerm)
        );
    }

    // Apply sorting
    if (currentSortColumn) {
        recentRequests.sort((a, b) => {
            let valA, valB;

            switch(currentSortColumn) {
                case 'timestamp': valA = a.start_time; valB = b.start_time; break;
                case 'method': valA = a.method; valB = b.method; break;
                case 'path': valA = a.path; valB = b.path; break;
                case 'time': valA = a.total_time; valB = b.total_time; break;
                default: valA = a.start_time; valB = b.start_time;
            }

            if (typeof valA === 'string') {
                return currentSortDirection === 'asc' 
                    ? valA.localeCompare(valB) 
                    : valB.localeCompare(valA);
            } else {
                return currentSortDirection === 'asc' 
                    ? valA - valB 
                    : valB - valA;
            }
        });
    }

    const tableBody = document.getElementById('requests-table').querySelector('tbody');
    tableBody.innerHTML = '';
    
    // Calculate pagination
    const totalPages = Math.ceil(recentRequests.length / paginationState.requestsPerPage);
    
    // Ensure current page is valid
    if (paginationState.requestsPage > totalPages) {
        paginationState.requestsPage = Math.max(1, totalPages);
    }
    
    // Get current page data
    const startIndex = (paginationState.requestsPage - 1) * paginationState.requestsPerPage;
    const endIndex = startIndex + paginationState.requestsPerPage;
    const currentPageData = recentRequests.slice(startIndex, endIndex);

    // Render table rows
    currentPageData.forEach(profile => {
        const row = document.createElement('tr');

        // Define row color based on response time
        let timeClass = 'text-indigo-600';
        if (profile.total_time > 0.5) timeClass = 'text-red-600';
        else if (profile.total_time > 0.1) timeClass = 'text-yellow-600';
        
        // Add status code to the display
        const statusCode = profile.status_code || '-';
        let statusClass = 'text-gray-500';
        
        if (statusCode >= 200 && statusCode < 300) statusClass = 'text-green-600';
        else if (statusCode >= 300 && statusCode < 400) statusClass = 'text-blue-600';
        else if (statusCode >= 400 && statusCode < 500) statusClass = 'text-yellow-600';
        else if (statusCode >= 500) statusClass = 'text-red-600';

        row.innerHTML = `
            <td class="text-gray-500">${formatTimeAgo(profile.start_time)}</td>
            <td class="text-gray-700">${profile.method}</td>
            <td class="font-medium text-gray-900">${profile.path}</td>
            <td class="${statusClass} font-medium">${statusCode}</td>
            <td class="${timeClass} font-medium">${formatTime(profile.total_time * 1000)} ms</td>
        `;

        tableBody.appendChild(row);
    });

    if (recentRequests.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-gray-500">No data available</td></tr>`;
    }
    
    // Update pagination controls
    updatePaginationControls('requests-pagination', totalPages, paginationState.requestsPage, (page) => {
        paginationState.requestsPage = page;
        updateRequestsTable();
    });
}

// Update all charts
function updateCharts() {
    updateResponseTimeChart();
    updateRequestsByMethodChart();
    updateStatusCodeChart();
    updateEndpointDistributionChart();
}

// Update status code distribution chart with ApexCharts
function updateStatusCodeChart() {
    // Get status code distribution data
    const statusCodes = dashboardData.requests.status_codes || [];
    
    // Group status codes by category
    const categories = {
        '2xx': { label: 'Success (2xx)', count: 0, codes: {} },
        '3xx': { label: 'Redirection (3xx)', count: 0, codes: {} },
        '4xx': { label: 'Client Error (4xx)', count: 0, codes: {} },
        '5xx': { label: 'Server Error (5xx)', count: 0, codes: {} },
        'other': { label: 'Other', count: 0, codes: {} }
    };
    
    statusCodes.forEach(item => {
        const code = parseInt(item.status);
        const category = 
            code >= 200 && code < 300 ? '2xx' :
            code >= 300 && code < 400 ? '3xx' :
            code >= 400 && code < 500 ? '4xx' :
            code >= 500 && code < 600 ? '5xx' : 'other';
        
        categories[category].count += item.count;
        categories[category].codes[code] = item.count;
    });
    
    // Prepare data for chart
    const categoryData = Object.entries(categories)
        .filter(([_, data]) => data.count > 0)
        .map(([key, data]) => ({
            x: data.label,
            y: data.count,
            category: key,
            codes: data.codes
        }));
    
    // Color mapping
    const colorMap = {
        '2xx': '#16a34a',  // Green
        '3xx': '#3b82f6',  // Blue
        '4xx': '#fbbf24',  // Yellow
        '5xx': '#ef4444',  // Red
        'other': '#6b7280' // Gray
    };
    
    const colors = categoryData.map(item => colorMap[item.category]);
    
    if (statusCodeChart) {
        // Update existing chart
        statusCodeChart.updateSeries([{
            name: 'Status Codes',
            data: categoryData
        }]);
        statusCodeChart.updateOptions({
            colors: colors
        });
    } else {
        // Create a new chart
        const options = {
            series: [{
                name: 'Status Codes',
                data: categoryData.map(item => item.y)
            }],
            chart: {
                type: 'bar',
                height: 250,
                toolbar: {
                    show: false
                },
                events: {
                    dataPointSelection: function(event, chartContext, config) {
                        const dataPoint = categoryData[config.dataPointIndex];
                        showStatusCodeDetails(dataPoint.category, dataPoint.codes);
                    }
                }
            },
            plotOptions: {
                bar: {
                    distributed: true, // This enables different colors for each bar
                    borderRadius: 4,
                    dataLabels: {
                        position: 'top'
                    },
                    columnWidth: '60%'
                }
            },
            colors: colors,
            dataLabels: {
                enabled: true,
                formatter: function(val) {
                    return val;
                },
                offsetY: -20,
                style: {
                    fontSize: '12px',
                    colors: ["#304758"]
                }
            },
            xaxis: {
                categories: categoryData.map(item => item.x),
                title: {
                    text: 'Status Code Category'
                }
            },
            yaxis: {
                title: {
                    text: 'Count'
                },
                labels: {
                    formatter: function(val) {
                        return Math.round(val);
                    }
                }
            },
            tooltip: {
                y: {
                    formatter: function(value, { dataPointIndex }) {
                        const category = categoryData[dataPointIndex];
                        const codeCount = Object.keys(category.codes).length;
                        return `${value} requests across ${codeCount} status code${codeCount !== 1 ? 's' : ''}`;
                    }
                }
            }
        };

        statusCodeChart = new ApexCharts(document.getElementById('status-code-chart'), options);
        statusCodeChart.render();
    }
}

// Function to show status code details
function showStatusCodeDetails(category, codes) {
    // Create modal content
    let content = `<h3 class="text-lg font-medium mb-3">${category} Status Codes</h3>
                   <div class="space-y-2">`;
    
    Object.entries(codes).forEach(([code, count]) => {
        let statusText = getStatusText(parseInt(code));
        content += `<div class="flex justify-between">
                        <span class="font-medium">${code} (${statusText})</span>
                        <span>${count} requests</span>
                    </div>`;
    });
    
    content += '</div>';
    
    // Show modal using Tabler's modal component
    const modal = document.createElement('div');
    modal.className = 'modal modal-blur fade show';
    modal.style.display = 'block';
    modal.setAttribute('role', 'dialog');
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Status Code Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listener to close button
    modal.querySelector('.btn-close, .btn[data-bs-dismiss="modal"]').addEventListener('click', () => {
        modal.remove();
    });
    
    // Close when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Helper function to get status text
function getStatusText(code) {
    if (code >= 200 && code < 300) return 'Success';
    if (code >= 300 && code < 400) return 'Redirection';
    if (code >= 400 && code < 500) return 'Client Error';
    if (code >= 500) return 'Server Error';
    return 'Unknown';
}

// Store chart state and data
let chartState = {
    lastProfileCount: 0,
    currentChartData: [],
    lastUpdateTime: Date.now()
};

// Update response time chart with ApexCharts
function updateResponseTimeChart() {
    // Get time series data
    const responseTimesData = dashboardData.time_series?.response_times || [];
    
    // Check if we have new data
    const hasNewData = responseTimesData.length !== chartState.lastProfileCount;
    chartState.lastProfileCount = responseTimesData.length;
    
    // Filter data based on selected time range
    const timeRangeSelect = document.getElementById('time-range');
    const selectedMinutes = parseInt(timeRangeSelect.value);
    
    let filteredData = responseTimesData;
    if (selectedMinutes > 0) {
        const cutoffTime = Date.now() - (selectedMinutes * 60 * 1000);
        filteredData = responseTimesData.filter(p => 
            new Date(p.timestamp * 1000).getTime() >= cutoffTime
        );
    }
    
    // Prepare data points for ApexCharts
    const dataPoints = filteredData.map(p => ({
        x: new Date(p.timestamp * 1000).getTime(),
        y: p.value,
        key: p.key
    }));

    // Store the data for tooltip access
    chartState.currentChartData = responseTimesData;

    if (responseTimeChart) {
        // Only update if not currently interacting with this chart
        if (!isUserInteracting || !document.getElementById('response-time-chart').matches(':hover')) {
            responseTimeChart.updateSeries([{
                name: 'Response Time (ms)',
                data: dataPoints
            }], false, true); // Use quiet update to prevent animations during updates
        }
    } else {
        // Create a new chart
        const options = {
            series: [{
                name: 'Response Time (ms)',
                data: dataPoints
            }],
            chart: {
                type: 'area',
                height: 250,
                toolbar: {
                    show: true,
                    tools: {
                        download: true,
                        selection: true,
                        zoom: true,
                        zoomin: true,
                        zoomout: true,
                        pan: true,
                        reset: true
                    },
                    autoSelected: 'zoom'
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 300
                },
                zoom: {
                    enabled: true,
                    type: 'x',
                    autoScaleYaxis: true
                },
                events: {
                    mouseMove: function() {
                        isUserInteracting = true;
                    },
                    mouseLeave: function() {
                        isUserInteracting = false;
                        if (pendingDataUpdate) {
                            pendingDataUpdate = false;
                            updateDashboard();
                        }
                    }
                }
            },
            dataLabels: {
                enabled: false
            },
            stroke: {
                curve: 'smooth',
                width: 2.5,
                colors: ['#16a34a'] // Green color
            },
            fill: {
                type: 'gradient',
                gradient: {
                    shadeIntensity: 1,
                    opacityFrom: 0.15,
                    opacityTo: 0.01,
                    stops: [0, 100]
                },
                colors: ['#16a34a']
            },
            markers: {
                size: 0, // Hide markers by default for cleaner look
                hover: {
                    size: 5,
                    sizeOffset: 3
                }
            },
            xaxis: {
                type: 'datetime',
                labels: {
                    datetimeUTC: false,
                    format: 'HH:mm:ss'
                }
            },
            yaxis: {
                title: {
                    text: 'Response Time (ms)'
                },
                min: 0,
                labels: {
                    formatter: function(val) {
                        return val.toFixed(0); // Remove decimals from y-axis labels
                    }
                }
            },
            tooltip: {
                shared: true,
                intersect: false,
                x: {
                    format: 'HH:mm:ss'
                },
                y: {
                    formatter: function(value) {
                        return Math.round(value) + ' ms'; // Round to whole numbers
                    }
                },
                custom: function({ series, seriesIndex, dataPointIndex, w }) {
                    const data = w.config.series[seriesIndex].data[dataPointIndex];
                    const key = data.key || 'Unknown';
                    const value = Math.round(data.y); // Round to whole number
                    const time = new Date(data.x).toLocaleTimeString();
                    
                    return `<div class="apexcharts-tooltip-title">${key}</div>
                            <div class="apexcharts-tooltip-series-group">
                                <span class="apexcharts-tooltip-marker" style="background-color: #16a34a"></span>
                                <div class="apexcharts-tooltip-text">
                                    <div><strong>${value} ms</strong></div>
                                    <div class="apexcharts-tooltip-y-group">
                                        <span class="apexcharts-tooltip-text-y-label">Time: </span>
                                        <span class="apexcharts-tooltip-text-y-value">${time}</span>
                                    </div>
                                </div>
                            </div>`;
                }
            }
        };

        responseTimeChart = new ApexCharts(document.getElementById('response-time-chart'), options);
        responseTimeChart.render();
    }
}

// Update requests by method chart with ApexCharts
function updateRequestsByMethodChart() {
    // Get method distribution data
    const methodDistribution = dashboardData.endpoints.by_method || [];
    
    // Prepare data for chart
    const methods = methodDistribution.map(item => item.method);
    const counts = methodDistribution.map(item => item.count);
    
    // Standard colors for HTTP methods
    const colorMap = {
        'GET': '#16a34a',    // Green
        'POST': '#4f46e5',   // Indigo
        'PUT': '#fbbf24',    // Yellow
        'DELETE': '#ef4444', // Red
        'PATCH': '#a78bfa',  // Purple
        'OPTIONS': '#7c3aed', // Violet
        'HEAD': '#10b981'    // Emerald
    };
    
    const colors = methods.map(method => colorMap[method] || '#6b7280');
    
    if (requestsByMethodChart) {
        // Update existing chart
        requestsByMethodChart.updateSeries(counts);
        requestsByMethodChart.updateOptions({
            labels: methods,
            colors: colors
        });
    } else {
        // Create a new chart
        const options = {
            series: counts,
            chart: {
                type: 'donut',
                height: 250,
                animations: {
                    animateGradually: {
                        enabled: true,
                        delay: 150
                    },
                    dynamicAnimation: {
                        enabled: true,
                        speed: 350
                    }
                }
            },
            labels: methods,
            colors: colors,
            legend: {
                position: 'right',
                formatter: function(seriesName, opts) {
                    const count = opts.w.globals.series[opts.seriesIndex];
                    const total = opts.w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                    const percentage = Math.round((count / total) * 100);
                    return `${seriesName}: ${count} (${percentage}%)`;
                },
                offsetY: 0,
                height: 200,
                fontSize: '13px'
            },
            dataLabels: {
                enabled: false
            },
            plotOptions: {
                pie: {
                    donut: {
                        size: '60%',
                        labels: {
                            show: true,
                            name: {
                                show: true,
                                fontSize: '16px',
                                fontWeight: 600
                            },
                            value: {
                                show: true,
                                fontSize: '20px',
                                fontWeight: 400,
                                formatter: function(val) {
                                    return val;
                                }
                            },
                            total: {
                                show: true,
                                label: 'Total',
                                formatter: function(w) {
                                    return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                                }
                            }
                        }
                    }
                }
            },
            tooltip: {
                enabled: true,
                fillSeriesColor: false,
                theme: 'light',
                style: {
                    fontSize: '14px'
                },
                y: {
                    formatter: function(value, { seriesIndex, w }) {
                        const method = w.globals.labels[seriesIndex];
                        const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                        const percentage = Math.round((value / total) * 100);
                        return `${method}: ${value} requests (${percentage}%)`;
                    }
                }
            }
        };

        requestsByMethodChart = new ApexCharts(document.getElementById('requests-by-method-chart'), options);
        requestsByMethodChart.render();
    }
}

// Update endpoint distribution chart with ApexCharts
function updateEndpointDistributionChart() {
    // Get endpoint distribution data
    const endpointDistribution = dashboardData.endpoints.distribution || [];

    // Prepare data for chart
    const labels = endpointDistribution.map(stat => `${stat.method} ${stat.path}`);
    const requestCounts = endpointDistribution.map(stat => stat.count);
    const avgTimes = endpointDistribution.map(stat => stat.avg * 1000).map(val => Math.round(val)); // Round to whole numbers

    if (endpointDistributionChart) {
        // Update existing chart
        endpointDistributionChart.updateSeries([
            {
                name: 'Request Count',
                data: requestCounts
            },
            {
                name: 'Avg Time (ms)',
                data: avgTimes
            }
        ]);
        endpointDistributionChart.updateOptions({
            xaxis: {
                categories: labels
            }
        });
    } else {
        // Create a new chart
        const options = {
            series: [
                {
                    name: 'Request Count',
                    data: requestCounts,
                    type: 'column'
                },
                {
                    name: 'Avg Time (ms)',
                    data: avgTimes,
                    type: 'line'
                }
            ],
            chart: {
                height: 350,
                type: 'line',
                toolbar: {
                    show: true,
                    tools: {
                        download: true,
                        selection: false,
                        zoom: true,
                        zoomin: true,
                        zoomout: true,
                        pan: true,
                        reset: true
                    }
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    animateGradually: {
                        enabled: true,
                        delay: 150
                    },
                    dynamicAnimation: {
                        enabled: true,
                        speed: 350
                    }
                }
            },
            stroke: {
                width: [0, 4],
                curve: 'smooth'
            },
            plotOptions: {
                bar: {
                    columnWidth: '50%',
                    borderRadius: 4
                }
            },
            dataLabels: {
                enabled: false,
                enabledOnSeries: [1]
            },
            markers: {
                size: 5,
                colors: ['transparent', '#16a34a'],
                strokeColors: '#fff',
                strokeWidth: 2,
                hover: {
                    size: 7
                }
            },
            colors: ['#4f46e5', '#16a34a'], // Indigo for count, green for time
            xaxis: {
                categories: labels,
                labels: {
                    rotate: -45,
                    trim: true,
                    style: {
                        fontSize: '12px'
                    }
                },
                tooltip: {
                    enabled: false
                }
            },
            yaxis: [
                {
                    title: {
                        text: 'Request Count'
                    },
                    labels: {
                        formatter: function(val) {
                            return Math.round(val);
                        }
                    }
                },
                {
                    opposite: true,
                    title: {
                        text: 'Avg Time (ms)'
                    },
                    labels: {
                        formatter: function(val) {
                            return Math.round(val);
                        }
                    }
                }
            ],
            legend: {
                position: 'top',
                horizontalAlign: 'center'
            },
            tooltip: {
                shared: true,
                intersect: false,
                y: {
                    formatter: function(value, { seriesIndex, dataPointIndex, w }) {
                        if (seriesIndex === 0) {
                            return `${value} requests`;
                        } else {
                            return `${value} ms`;
                        }
                    }
                }
            }
        };

        endpointDistributionChart = new ApexCharts(document.getElementById('endpoint-distribution-chart'), options);
        endpointDistributionChart.render();
    }
}

// This function is replaced by setupTablerTabs()

// Set up table sorting
function setupTableSorting() {
    const tables = document.querySelectorAll('.data-table');

    tables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sort]');

        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-sort');

                // Toggle direction if same column, otherwise default to ascending
                if (column === currentSortColumn) {
                    currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSortColumn = column;
                    currentSortDirection = 'asc';
                }

                // Update tables
                updateEndpointsTable();
                updateRequestsTable();

                // Update sort indicators (could add visual indicators here)
            });
        });
    });
}

// Set up search functionality
function setupSearch() {
    const endpointSearch = document.getElementById('endpoint-search');
    if (endpointSearch) {
        endpointSearch.addEventListener('input', () => {
            updateEndpointsTable();
        });
    }

    const requestSearch = document.getElementById('request-search');
    if (requestSearch) {
        requestSearch.addEventListener('input', () => {
            updateRequestsTable();
        });
    }
}

// Set up refresh rate control
function setupRefreshControl() {
    const refreshRateSelect = document.getElementById('refresh-rate');
    const refreshBtn = document.getElementById('refresh-btn');

    // Global update interval configuration
    window.updateConfig = {
        enabled: true,
        interval: 1000 // Default interval in ms
    };

    // Handle refresh rate change
    refreshRateSelect.addEventListener('change', () => {
        const rate = parseInt(refreshRateSelect.value);

        // Update configuration
        if (rate > 0) {
            window.updateConfig.enabled = true;
            window.updateConfig.interval = rate;
            console.log(`Auto-refresh set to ${rate}ms`);
        } else {
            window.updateConfig.enabled = false;
            console.log('Auto-refresh disabled');
        }
    });

    // Handle manual refresh
    refreshBtn.addEventListener('click', () => {
        // Force update regardless of interaction state
        const wasInteracting = isUserInteracting;
        isUserInteracting = false;
        pendingDataUpdate = false;
        
        // Fetch data and update UI
        fetchData().then(() => {
            // Restore interaction state
            isUserInteracting = wasInteracting;
        });
    });
}

// No need for Chart.js configuration anymore

// Initialize dashboard
function initDashboard(dashboardApiPath) {
    // Set API path for data fetching
    apiPath = dashboardApiPath.replace(/\/+$/, '');  // Remove trailing slashes
    
    // Set up UI interactions
    setupTablerTabs();  // Use Tabler's tab system
    setupTableSorting();
    setupSearch();
    setupRefreshControl();
    setupInteractionTracking();
    setupTimeRangeSelector();

    // Initial data fetch
    fetchData();

    // Start optimized update loop using requestAnimationFrame
    startUpdateLoop();
}

// Set up time range selector
function setupTimeRangeSelector() {
    const timeRangeSelect = document.getElementById('time-range');
    if (timeRangeSelect) {
        timeRangeSelect.addEventListener('change', () => {
            updateResponseTimeChart();
        });
    }
}

// Optimized real-time updates using requestAnimationFrame
function startUpdateLoop() {
    let lastUpdate = 0;
    
    const update = (timestamp) => {
        // Only update if enabled and enough time has passed
        if (window.updateConfig.enabled && 
            document.visibilityState === 'visible' && 
            (!lastUpdate || timestamp - lastUpdate >= window.updateConfig.interval)) {
            
            // Don't update if user is interacting and we're not forcing an update
            if (!isUserInteracting) {
                fetchData();
                lastUpdate = timestamp;
            } else {
                pendingDataUpdate = true;
            }
        }
        requestAnimationFrame(update);
    };
    
    // Add visibility change listener to pause updates when tab is not visible
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && pendingDataUpdate) {
            fetchData();
            pendingDataUpdate = false;
        }
    });
    
    requestAnimationFrame(update);
}

// Track user interactions to prevent UI updates during hover/interaction
function setupInteractionTracking() {
    // Track mouse interactions on charts and tables
    const interactiveElements = [
        document.getElementById('response-time-chart'),
        document.getElementById('requests-by-method-chart'),
        document.getElementById('status-code-chart'),
        document.getElementById('endpoint-distribution-chart'),
        document.getElementById('slowest-endpoints-table'),
        document.getElementById('endpoints-table'),
        document.getElementById('requests-table')
    ];
    
    interactiveElements.forEach(element => {
        if (!element) return;
        
        element.addEventListener('mouseenter', () => {
            isUserInteracting = true;
        });
        
        element.addEventListener('mouseleave', () => {
            isUserInteracting = false;
            // Apply any pending updates when user stops interacting
            if (pendingDataUpdate) {
                pendingDataUpdate = false;
                updateDashboard();
            }
        });
    });
    
    // Also track focus on search inputs
    const searchInputs = [
        document.getElementById('endpoint-search'),
        document.getElementById('request-search')
    ];
    
    searchInputs.forEach(input => {
        if (!input) return;
        
        input.addEventListener('focus', () => {
            isUserInteracting = true;
        });
        
        input.addEventListener('blur', () => {
            isUserInteracting = false;
            if (pendingDataUpdate) {
                pendingDataUpdate = false;
                updateDashboard();
            }
        });
    });
}

// Export the init function for use in the HTML
window.initDashboard = initDashboard;

// Make sure initDashboard is globally available
if (typeof window !== 'undefined') {
    window.initDashboard = initDashboard;
}
