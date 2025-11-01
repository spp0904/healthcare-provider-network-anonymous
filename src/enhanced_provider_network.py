#!/usr/bin/env python3
"""
Enhanced Provider Network with Fully Anonymous Data
==================================================

Privacy-safe network analysis using fully anonymous provider data
with NO identifiable information.
"""

import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from collections import defaultdict

class EnhancedProviderNetwork:
    def __init__(self, claims_file, npi_data_file=None):
        """Initialize with claims data and optional NPI lookup file"""
        self.claims_file = claims_file
        self.npi_data_file = npi_data_file or "data/michigan_providers_fully_anonymous.csv"
        self.df = None
        self.provider_names = {}
        
    def load_provider_names(self):
        """Load synthetic provider names from fully anonymous dataset"""
        print("🔍 Loading synthetic provider names from anonymous dataset...")
        
        try:
            npi_df = pd.read_csv(self.npi_data_file)
            print(f"   Loaded {len(npi_df)} NPI records")
            
            # Find name columns
            name_columns = []
            for col in npi_df.columns:
                if any(name_part in col.lower() for name_part in ['last name', 'first name', 'organization name']):
                    name_columns.append(col)
            
            print(f"   Found name columns: {name_columns}")
            
            # Create provider name mapping
            for _, row in npi_df.iterrows():
                npi = row['NPI']
                if pd.notna(npi):
                    # Try organization name first
                    if 'Provider Organization Name (Legal Business Name)' in npi_df.columns:
                        org_name = row['Provider Organization Name (Legal Business Name)']
                        if pd.notna(org_name) and org_name != 'MASKED':
                            self.provider_names[npi] = org_name
                            continue
                    
                    # Build individual name
                    name_parts = []
                    if 'Provider Name Prefix Text' in npi_df.columns and pd.notna(row['Provider Name Prefix Text']):
                        name_parts.append(str(row['Provider Name Prefix Text']))
                    if 'Provider First Name' in npi_df.columns and pd.notna(row['Provider First Name']):
                        name_parts.append(str(row['Provider First Name']))
                    if 'Provider Middle Name' in npi_df.columns and pd.notna(row['Provider Middle Name']):
                        name_parts.append(str(row['Provider Middle Name']))
                    if 'Provider Last Name (Legal Name)' in npi_df.columns and pd.notna(row['Provider Last Name (Legal Name)']):
                        name_parts.append(str(row['Provider Last Name (Legal Name)']))
                    if 'Provider Name Suffix Text' in npi_df.columns and pd.notna(row['Provider Name Suffix Text']):
                        name_parts.append(str(row['Provider Name Suffix Text']))
                    if 'Provider Credential Text' in npi_df.columns and pd.notna(row['Provider Credential Text']):
                        name_parts.append(str(row['Provider Credential Text']))
                    
                    if name_parts:
                        full_name = ' '.join(name_parts)
                        self.provider_names[npi] = full_name
                    else:
                        self.provider_names[npi] = f"Provider {npi}"
            
            print(f"✅ Loaded names for {len(self.provider_names)} providers")
            return True
            
        except Exception as e:
            print(f"❌ Error loading provider names: {e}")
            return False
    
    def load_claims_data(self):
        """Load the claims data"""
        print("📊 Loading claims data...")
        try:
            self.df = pd.read_csv(self.claims_file)
            print(f"   Loaded {len(self.df)} claims")
            
            # Load provider names
            self.load_provider_names()
            
            return True
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            return False
    
    def create_shared_patient_network(self, min_shared_patients=2):
        """Create network based on shared patients between providers"""
        print(f"🔗 Creating shared patient network (min {min_shared_patients} shared patients)...")
        
        # Group by patient and find providers per patient
        patient_providers = self.df.groupby('person_alias')['servicing_provider_npi_number'].apply(list).reset_index()
        
        # Find patients with multiple providers
        multi_provider_patients = patient_providers[patient_providers['servicing_provider_npi_number'].apply(len) > 1]
        print(f"   Found {len(multi_provider_patients)} patients with multiple providers")
        
        # Count shared patients between provider pairs
        shared_counts = defaultdict(int)
        shared_revenue = defaultdict(float)
        
        for _, row in multi_provider_patients.iterrows():
            providers = row['servicing_provider_npi_number']
            patient_id = row['person_alias']
            
            # Get total revenue for this patient
            patient_revenue = self.df[self.df['person_alias'] == patient_id]['allowed_amount'].sum()
            
            # Create pairs and count
            for i in range(len(providers)):
                for j in range(i+1, len(providers)):
                    p1, p2 = sorted([providers[i], providers[j]])
                    shared_counts[(p1, p2)] += 1
                    shared_revenue[(p1, p2)] += patient_revenue
        
        # Create network
        G = nx.Graph()
        
        # Add edges for provider pairs with sufficient shared patients
        for (p1, p2), count in shared_counts.items():
            if count >= min_shared_patients:
                # Get provider names
                name1 = self.provider_names.get(p1, f"Provider {p1}")
                name2 = self.provider_names.get(p2, f"Provider {p2}")
                
                # Add edge with shared patient count and revenue
                G.add_edge(name1, name2, 
                          shared_patients=count,
                          shared_revenue=shared_revenue[(p1, p2)],
                          provider1_npi=p1,
                          provider2_npi=p2)
        
        print(f"   Network: {G.number_of_nodes()} providers, {G.number_of_edges()} connections")
        return G
    
    def get_provider_info(self, provider_name):
        """Get detailed information about a provider"""
        # Find the NPI for this provider name
        provider_npi = None
        for npi, name in self.provider_names.items():
            if name == provider_name:
                provider_npi = npi
                break
        
        if not provider_npi:
            return {}
        
        # Get claims for this provider
        provider_claims = self.df[self.df['servicing_provider_npi_number'] == provider_npi]
        
        if len(provider_claims) == 0:
            return {}
        
        # Calculate metrics
        total_claims = len(provider_claims)
        total_revenue = provider_claims['allowed_amount'].sum()
        unique_patients = provider_claims['person_alias'].nunique()
        avg_claim_amount = provider_claims['allowed_amount'].mean()
        
        # Get specialty info
        specialty = "Unknown"
        if 'taxonomy_classification' in provider_claims.columns:
            specialty_counts = provider_claims['taxonomy_classification'].value_counts()
            if len(specialty_counts) > 0:
                specialty = specialty_counts.index[0]
        
        return {
            'npi': provider_npi,
            'name': provider_name,
            'specialty': specialty,
            'total_claims': total_claims,
            'total_revenue': total_revenue,
            'unique_patients': unique_patients,
            'avg_claim_amount': avg_claim_amount
        }
    
    def create_network_visualization(self, G, output_file, title="Provider Network"):
        """Create an interactive network visualization"""
        
        # Calculate layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Prepare node traces
        node_x = []
        node_y = []
        node_text = []
        node_info = []
        node_sizes = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Get provider info
            info = self.get_provider_info(node)
            
            node_text.append(node)
            node_info.append(f"{node}<br>"
                           f"Specialty: {info.get('specialty', 'Unknown')}<br>"
                           f"Patients: {info.get('unique_patients', 0)}<br>"
                           f"Revenue: ${info.get('total_revenue', 0):,.2f}")
            
            # Size based on degree
            degree = G.degree(node)
            node_sizes.append(max(10, degree * 2))
        
        # Create node trace
        node_trace = go.Scatter(x=node_x, y=node_y,
                               mode='markers+text',
                               hoverinfo='text',
                               hovertext=node_info,
                               text=node_text,
                               textposition="middle center",
                               marker=dict(size=node_sizes,
                                         color='lightblue',
                                         line=dict(width=1, color='darkblue')))
        
        # Prepare edge traces
        edge_x = []
        edge_y = []
        edge_info = []
        
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            shared_patients = edge[2].get('shared_patients', 0)
            shared_revenue = edge[2].get('shared_revenue', 0)
            edge_info.append(f"Shared Patients: {shared_patients}<br>"
                           f"Shared Revenue: ${shared_revenue:,.2f}")
        
        # Create edge trace
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                               line=dict(width=1, color='gray'),
                               hoverinfo='none',
                               mode='lines')
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=title,
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Fully Anonymous Healthcare Provider Network<br>No Real Identifiers",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color="red", size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        
        # Save
        fig.write_html(output_file)
        return output_file