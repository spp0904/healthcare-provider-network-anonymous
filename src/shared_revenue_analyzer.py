#!/usr/bin/env python3
"""
Shared Revenue Network Analyzer - Fully Anonymous Version
========================================================

Privacy-safe shared patient revenue analysis using fully anonymous data.
NO real provider identifiers, addresses, or contact information.
"""

import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import os
import json
from collections import defaultdict
from enhanced_provider_network import EnhancedProviderNetwork

class SharedRevenueNetworkAnalyzer(EnhancedProviderNetwork):
    def __init__(self, claims_file=None, npi_data_file=None):
        """Initialize with fully anonymous data files"""
        claims_file = claims_file or "data/synthetic_healthcare_claims_fully_anonymous.csv"
        npi_data_file = npi_data_file or "data/michigan_providers_fully_anonymous.csv"
        super().__init__(claims_file, npi_data_file)
        
    def calculate_shared_revenue_network(self, min_shared_patients=1):
        """Calculate network based on revenue from shared patients only"""
        print(f"💰 Creating shared revenue network (min {min_shared_patients} shared patients)...")
        
        # Find patients with multiple providers
        patient_providers = self.df.groupby('person_alias')['servicing_provider_npi_number'].apply(list).reset_index()
        multi_provider_patients = patient_providers[patient_providers['servicing_provider_npi_number'].apply(len) > 1]
        print(f"   Found {len(multi_provider_patients)} patients with multiple providers")
        
        # For each provider pair, calculate revenue ONLY from shared patients
        shared_metrics = defaultdict(lambda: {
            'shared_patients': 0,
            'shared_revenue': 0.0,
            'patient_revenues': []
        })
        
        for _, row in multi_provider_patients.iterrows():
            providers = list(set(row['servicing_provider_npi_number']))  # Remove duplicates
            patient_id = row['person_alias']
            
            # Get all claims for this patient
            patient_claims = self.df[self.df['person_alias'] == patient_id]
            total_patient_revenue = patient_claims['allowed_amount'].sum()
            
            # Create provider pairs and record shared patient revenue
            for i in range(len(providers)):
                for j in range(i+1, len(providers)):
                    p1, p2 = sorted([providers[i], providers[j]])
                    key = (p1, p2)
                    
                    shared_metrics[key]['shared_patients'] += 1
                    shared_metrics[key]['shared_revenue'] += total_patient_revenue
                    shared_metrics[key]['patient_revenues'].append(total_patient_revenue)
        
        # Create network
        G = nx.Graph()
        
        for (p1, p2), metrics in shared_metrics.items():
            if metrics['shared_patients'] >= min_shared_patients:
                # Get provider names
                name1 = self.provider_names.get(p1, f"Provider {p1}")
                name2 = self.provider_names.get(p2, f"Provider {p2}")
                
                # Calculate additional metrics
                avg_revenue_per_shared_patient = metrics['shared_revenue'] / metrics['shared_patients']
                
                # Get individual provider metrics
                p1_info = self.get_provider_info(name1)
                p2_info = self.get_provider_info(name2)
                
                # Calculate what percentage of each provider's revenue comes from shared patients
                p1_shared_pct = (metrics['shared_revenue'] / max(p1_info.get('total_revenue', 1), 1)) * 100
                p2_shared_pct = (metrics['shared_revenue'] / max(p2_info.get('total_revenue', 1), 1)) * 100
                
                G.add_edge(name1, name2,
                          shared_patients=metrics['shared_patients'],
                          shared_revenue=metrics['shared_revenue'],
                          avg_revenue_per_shared_patient=avg_revenue_per_shared_patient,
                          provider1_npi=p1,
                          provider2_npi=p2,
                          provider1_shared_pct=p1_shared_pct,
                          provider2_shared_pct=p2_shared_pct,
                          provider1_specialty=p1_info.get('specialty', 'Unknown'),
                          provider2_specialty=p2_info.get('specialty', 'Unknown'))
        
        print(f"   Network: {G.number_of_nodes()} providers, {G.number_of_edges()} connections")
        return G
    
    def convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    def create_enhanced_shared_revenue_html(self, G, output_file):
        """Create enhanced HTML with shared revenue controls"""
        
        # Calculate layout
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        
        # Get top providers by total connections for better layout
        top_providers = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)[:120]
        G_subset = G.subgraph(top_providers).copy()
        
        print(f"📊 Working with subset: {G_subset.number_of_nodes()} providers, {G_subset.number_of_edges()} connections")
        
        # Recalculate layout for subset
        pos = nx.spring_layout(G_subset, k=2, iterations=50, seed=42)
        
        # Prepare data
        nodes_data = []
        edges_data = []
        
        # Collect node data
        for node in G_subset.nodes():
            x, y = pos[node]
            info = self.get_provider_info(node)
            
            # Calculate shared revenue metrics for this node
            shared_revenue_total = 0
            shared_patients_total = 0
            connections = []
            
            for neighbor in G_subset.neighbors(node):
                edge_data = G_subset[node][neighbor]
                shared_revenue_total += edge_data['shared_revenue']
                shared_patients_total += edge_data['shared_patients']
                connections.append({
                    'neighbor': neighbor,
                    'shared_patients': edge_data['shared_patients'],
                    'shared_revenue': edge_data['shared_revenue'],
                    'avg_revenue': edge_data['avg_revenue_per_shared_patient'],
                    'specialty': edge_data['provider2_specialty'] if node == G_subset[node][neighbor]['provider1_npi'] else edge_data['provider1_specialty']
                })
            
            # Calculate percentage of revenue from shared patients
            total_revenue = info.get('total_revenue', 1)
            shared_revenue_pct = (shared_revenue_total / max(total_revenue, 1)) * 100
            
            nodes_data.append({
                'id': node,
                'x': x,
                'y': y,
                'specialty': info.get('specialty', 'Unknown'),
                'total_patients': info.get('unique_patients', 0),
                'total_revenue': total_revenue,
                'shared_patients': shared_patients_total,
                'shared_revenue': shared_revenue_total,
                'shared_revenue_pct': shared_revenue_pct,
                'connections': connections,
                'degree': G_subset.degree(node)
            })
        
        # Collect edge data
        for edge in G_subset.edges(data=True):
            node1, node2, data = edge
            x0, y0 = pos[node1]
            x1, y1 = pos[node2]
            
            edges_data.append({
                'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                'shared_patients': data['shared_patients'],
                'shared_revenue': data['shared_revenue'],
                'avg_revenue': data['avg_revenue_per_shared_patient'],
                'node1': node1,
                'node2': node2,
                'provider1_specialty': data['provider1_specialty'],
                'provider2_specialty': data['provider2_specialty']
            })
        
        # Convert numpy types for JSON serialization
        nodes_data = self.convert_numpy_types(nodes_data)
        edges_data = self.convert_numpy_types(edges_data)
        
        # Create HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Provider Network - Shared Patient Revenue Analysis</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ display: flex; gap: 20px; }}
        .main-content {{ flex: 1; }}
        .controls {{ width: 300px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: fit-content; }}
        .control-group {{ margin-bottom: 20px; }}
        .control-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
        .control-group input, .control-group select {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
        .privacy-notice {{ background: #e8f5e9; border: 1px solid #4caf50; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .privacy-notice h3 {{ margin-top: 0; color: #2e7d32; }}
        .stats {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px; }}
        #connectionTable {{ margin-top: 20px; max-height: 400px; overflow-y: auto; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; position: sticky; top: 0; }}
        .high-revenue {{ background-color: #ffebee; }}
        .medium-revenue {{ background-color: #fff3e0; }}
        .low-revenue {{ background-color: #f3e5f5; }}
    </style>
</head>
<body>
    <div class="privacy-notice">
        <h3>🛡️ Fully Anonymous Healthcare Data</h3>
        <p><strong>Privacy Protection:</strong> This visualization uses completely anonymized data with no real provider identifiers, addresses, or contact information. All NPIs, names, and locations are synthetic.</p>
    </div>
    
    <div class="container">
        <div class="main-content">
            <div id="networkPlot" style="width:100%; height:600px;"></div>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label>View Mode:</label>
                <select id="viewMode" onchange="updateVisualization()">
                    <option value="shared">Shared Revenue Only</option>
                    <option value="total">Total Revenue</option>
                </select>
            </div>
            
            <div class="control-group">
                <label>Min Shared Patients:</label>
                <input type="range" id="minSharedPatients" min="1" max="20" value="1" onchange="updateVisualization()">
                <span id="minSharedPatientsValue">1</span>
            </div>
            
            <div class="control-group">
                <label>Min Shared Revenue:</label>
                <input type="range" id="minSharedRevenue" min="0" max="50000" value="0" step="1000" onchange="updateVisualization()">
                <span id="minSharedRevenueValue">$0</span>
            </div>
            
            <div class="control-group">
                <label>Provider Specialty:</label>
                <select id="specialtyFilter" onchange="updateVisualization()">
                    <option value="all">All Specialties</option>
                </select>
            </div>
            
            <div class="stats" id="networkStats">
                <strong>Network Statistics:</strong><br>
                Providers: {len(nodes_data)}<br>
                Connections: {len(edges_data)}<br>
                Total Shared Revenue: ${{total_shared_revenue:,.2f}}
            </div>
            
            <div id="connectionTable">
                <h4>Provider Connections</h4>
                <p>Click a provider node to see their connections</p>
            </div>
        </div>
    </div>

<script>
// Data
const nodesData = {nodes_data};
const edgesData = {edges_data};
let currentNodes = [...nodesData];
let currentEdges = [...edgesData];

// Initialize specialty filter
const specialties = [...new Set(nodesData.map(n => n.specialty))].sort();
const specialtySelect = document.getElementById('specialtyFilter');
specialties.forEach(spec => {{
    const option = document.createElement('option');
    option.value = spec;
    option.textContent = spec;
    specialtySelect.appendChild(option);
}});

function updateVisualization() {{
    const viewMode = document.getElementById('viewMode').value;
    const minSharedPatients = parseInt(document.getElementById('minSharedPatients').value);
    const minSharedRevenue = parseInt(document.getElementById('minSharedRevenue').value);
    const specialtyFilter = document.getElementById('specialtyFilter').value;
    
    // Update display values
    document.getElementById('minSharedPatientsValue').textContent = minSharedPatients;
    document.getElementById('minSharedRevenueValue').textContent = `${{minSharedRevenue.toLocaleString()}}`;
    
    // Filter data
    currentEdges = edgesData.filter(edge => 
        edge.shared_patients >= minSharedPatients && 
        edge.shared_revenue >= minSharedRevenue &&
        (specialtyFilter === 'all' || 
         edge.provider1_specialty === specialtyFilter || 
         edge.provider2_specialty === specialtyFilter)
    );
    
    // Filter nodes to only include those with connections
    const connectedNodes = new Set();
    currentEdges.forEach(edge => {{
        connectedNodes.add(edge.node1);
        connectedNodes.add(edge.node2);
    }});
    
    currentNodes = nodesData.filter(node => 
        connectedNodes.has(node.id) &&
        (specialtyFilter === 'all' || node.specialty === specialtyFilter)
    );
    
    createPlot();
    updateStats();
}}

function createPlot() {{
    const viewMode = document.getElementById('viewMode').value;
    
    // Create edges trace
    const edgeTrace = {{
        x: [],
        y: [],
        mode: 'lines',
        line: {{ color: [], width: [] }},
        hoverinfo: 'text',
        hovertext: [],
        showlegend: false
    }};
    
    currentEdges.forEach(edge => {{
        edgeTrace.x.push(edge.x0, edge.x1, null);
        edgeTrace.y.push(edge.y0, edge.y1, null);
        
        // Color by shared revenue
        const revenue = edge.shared_revenue;
        let color, width;
        if (revenue > 20000) {{
            color = '#d32f2f'; width = 3;
        }} else if (revenue > 10000) {{
            color = '#f57c00'; width = 2;
        }} else {{
            color = '#fbc02d'; width = 1;
        }}
        
        edgeTrace.line.color.push(color, color, color);
        edgeTrace.line.width.push(width, width, width);
        edgeTrace.hovertext.push('', '', '');
    }});
    
    // Create nodes trace
    const nodeTrace = {{
        x: currentNodes.map(n => n.x),
        y: currentNodes.map(n => n.y),
        mode: 'markers+text',
        marker: {{
            size: currentNodes.map(n => viewMode === 'shared' ? 
                Math.max(8, Math.min(30, n.shared_patients * 2)) : 
                Math.max(8, Math.min(30, n.total_patients / 2))
            ),
            color: currentNodes.map(n => viewMode === 'shared' ? n.shared_patients : n.total_patients),
            colorscale: viewMode === 'shared' ? 'Reds' : 'Blues',
            showscale: true,
            colorbar: {{
                title: viewMode === 'shared' ? 'Shared Patients' : 'Total Patients',
                x: 1.02
            }},
            line: {{ width: 1, color: 'darkblue' }}
        }},
        text: currentNodes.map(n => n.id.length > 20 ? n.id.substring(0, 17) + '...' : n.id),
        textposition: 'middle center',
        textfont: {{ size: 10 }},
        hoverinfo: 'text',
        hovertext: currentNodes.map(n => `
            ${{n.id}}<br>
            Specialty: ${{n.specialty}}<br>
            ${{viewMode === 'shared' ? 
                `Shared Patients: ${{n.shared_patients}}<br>Shared Revenue: $${{n.shared_revenue.toLocaleString()}}<br>Shared Revenue %: ${{n.shared_revenue_pct.toFixed(1)}}%` :
                `Total Patients: ${{n.total_patients}}<br>Total Revenue: $${{n.total_revenue.toLocaleString()}}`
            }}
        `),
        showlegend: false
    }};
    
    const layout = {{
        title: `Healthcare Provider Network - ${{viewMode === 'shared' ? 'Shared' : 'Total'}} Revenue Analysis`,
        showlegend: false,
        hovermode: 'closest',
        margin: {{ t: 50, b: 50, l: 50, r: 50 }},
        xaxis: {{ showgrid: false, zeroline: false, showticklabels: false }},
        yaxis: {{ showgrid: false, zeroline: false, showticklabels: false }},
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)'
    }};
    
    Plotly.newPlot('networkPlot', [edgeTrace, nodeTrace], layout);
    
    // Add click handler
    document.getElementById('networkPlot').on('plotly_click', function(data) {{
        if (data.points.length > 0) {{
            const pointIndex = data.points[0].pointIndex;
            const clickedNode = currentNodes[pointIndex];
            showConnections(clickedNode);
        }}
    }});
}}

function showConnections(node) {{
    const connections = node.connections.filter(conn => 
        currentNodes.some(n => n.id === conn.neighbor)
    );
    
    let tableHTML = `
        <h4>${{node.id}}</h4>
        <p><strong>Specialty:</strong> ${{node.specialty}}</p>
        <p><strong>Shared Patients:</strong> ${{node.shared_patients}} | <strong>Shared Revenue:</strong> $${{node.shared_revenue.toLocaleString()}}</p>
        <table>
            <thead>
                <tr>
                    <th>Connected Provider</th>
                    <th>Patients</th>
                    <th>Revenue</th>
                    <th>Avg/Patient</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    connections.sort((a, b) => b.shared_patients - a.shared_patients).forEach(conn => {{
        const revenueClass = conn.shared_revenue > 15000 ? 'high-revenue' : 
                           conn.shared_revenue > 7500 ? 'medium-revenue' : 'low-revenue';
        
        tableHTML += `
            <tr class="${{revenueClass}}">
                <td title="${{conn.neighbor}}">${{conn.neighbor.length > 25 ? conn.neighbor.substring(0, 22) + '...' : conn.neighbor}}</td>
                <td>${{conn.shared_patients}}</td>
                <td>$${{conn.shared_revenue.toLocaleString()}}</td>
                <td>$${{conn.avg_revenue.toLocaleString()}}</td>
            </tr>
        `;
    }});
    
    tableHTML += '</tbody></table>';
    document.getElementById('connectionTable').innerHTML = tableHTML;
}}

function updateStats() {{
    const totalRevenue = currentEdges.reduce((sum, edge) => sum + edge.shared_revenue, 0);
    const avgSharedPatients = currentEdges.length > 0 ? 
        currentEdges.reduce((sum, edge) => sum + edge.shared_patients, 0) / currentEdges.length : 0;
    
    document.getElementById('networkStats').innerHTML = `
        <strong>Network Statistics:</strong><br>
        Providers: ${{currentNodes.length}}<br>
        Connections: ${{currentEdges.length}}<br>
        Total Shared Revenue: $${{totalRevenue.toLocaleString()}}<br>
        Avg Shared Patients: ${{avgSharedPatients.toFixed(1)}}
    `;
}}

// Initialize
updateVisualization();
</script>
</body>
</html>
"""
        
        # Calculate total shared revenue for stats
        total_shared_revenue = sum(edge['shared_revenue'] for edge in edges_data)
        
        # Replace placeholders with proper JSON
        html_content = html_content.replace('{nodes_data}', json.dumps(nodes_data))
        html_content = html_content.replace('{edges_data}', json.dumps(edges_data))
        html_content = html_content.replace('{total_shared_revenue}', str(total_shared_revenue))
        
        # Write file
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print("✅ Shared revenue HTML written successfully")
        return output_file

def main():
    """Main function to create shared revenue network visualization"""
    print("💰 SHARED PATIENT REVENUE NETWORK ANALYZER")
    print("=" * 60)
    print("🛡️  Using Fully Anonymous Data - No Real Identifiers")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = SharedRevenueNetworkAnalyzer()
    
    # Load data
    if not analyzer.load_claims_data():
        return
    
    # Create shared revenue network
    G = analyzer.calculate_shared_revenue_network(min_shared_patients=1)
    
    if G.number_of_nodes() == 0:
        print("❌ No network created - check your data")
        return
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Create visualization
    output_file = "output/shared_revenue_network_anonymous.html"
    analyzer.create_enhanced_shared_revenue_html(G, output_file)
    
    print(f"💰 Shared revenue network saved: {output_file}")
    
    print(f"\n✅ SHARED REVENUE VISUALIZER COMPLETE!")
    print(f"🌐 File: {output_file}")
    print(f"\n💰 SHARED REVENUE FEATURES:")
    print(f"   • ✅ Revenue calculated ONLY from shared patients")
    print(f"   • ✅ Toggle between Total vs Shared revenue views")
    print(f"   • ✅ Connection table shows revenue breakdown per relationship")
    print(f"   • ✅ Edge colors based on total shared revenue")
    print(f"   • ✅ Detailed per-patient revenue averages")
    print(f"   • ✅ Percentage of revenue from shared patients")
    print(f"\n🛡️  PRIVACY FEATURES:")
    print(f"   • ✅ Fully anonymous data - no real identifiers")
    print(f"   • ✅ Synthetic NPIs (starting with 9)")
    print(f"   • ✅ Synthetic provider names")
    print(f"   • ✅ No real addresses or contact information")
    print(f"   • ✅ Safe for public sharing")
    print(f"\n💡 FINANCIAL INSIGHTS:")
    print(f"   1. See which provider relationships generate most revenue")
    print(f"   2. Identify providers heavily dependent on shared patients")  
    print(f"   3. Find high-value connections vs high-volume connections")
    print(f"   4. Analyze revenue per shared patient for efficiency")

if __name__ == "__main__":
    main()