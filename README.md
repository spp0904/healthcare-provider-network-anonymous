# Healthcare Provider Network Analysis

🏥 **Interactive network visualization of healthcare provider relationships based on shared patient revenue.**

![Privacy Protected](https://img.shields.io/badge/Privacy-Protected-green)
![Synthetic Data](https://img.shields.io/badge/Data-Synthetic-blue)
![Python](https://img.shields.io/badge/Python-3.8+-blue)

## 🎯 Features

- **Privacy-Protected**: Uses completely anonymized synthetic data
- **Interactive Visualization**: Network graph with revenue-based connections  
- **Financial Insights**: Analyze shared patient revenue patterns
- **Provider Analysis**: Specialty-based filtering and statistics
- **GitHub Pages Ready**: Self-contained HTML visualization

## 🛡️ Privacy & Compliance

- ✅ **Fully Anonymous Data**: No real provider identifiers
- ✅ **Synthetic NPIs**: All identifiers start with '9' (non-real)
- ✅ **Safe for Public Sharing**: Complete anonymization
- ✅ **HIPAA Compliant**: No PHI or real healthcare data

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/spp0904/Provider-Network-Visualization-.git
cd Provider-Network-Visualization-
```

### 2. Set up Python environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Generate visualization
```bash
python src/shared_revenue_analyzer.py
```

### 4. View results
Open `output/shared_revenue_network_anonymous.html` in your browser

## 📊 What You'll See

- **Network Graph**: Providers as nodes, shared revenue as connections
- **Edge Colors**: Darker lines = higher shared revenue
- **Interactive Controls**: Filter by specialty, patient count, revenue
- **Statistics Table**: Detailed connection analysis
- **Revenue Insights**: Total vs shared revenue comparisons

## 🔧 Technical Details

### Data Pipeline
1. **Synthetic Claims Generation**: Creates realistic but fake healthcare claims
2. **Provider Network Construction**: Identifies shared patient relationships
3. **Revenue Calculation**: Computes shared revenue from common patients
4. **Network Analysis**: Applies graph theory for layout and insights
5. **Visualization Generation**: Creates interactive HTML output

### Technologies Used
- **Python**: Data processing and analysis
- **NetworkX**: Graph theory and network analysis
- **Plotly**: Interactive web visualizations
- **Pandas**: Data manipulation
- **NumPy**: Numerical computations

## 📁 Project Structure

```
healthcare_network_github/
├── src/                          # Source code
│   ├── shared_revenue_analyzer.py    # Main analyzer
│   └── enhanced_provider_network.py  # Network utilities
├── data/                         # Synthetic datasets
│   ├── synthetic_healthcare_claims_fully_anonymous.csv
│   └── michigan_providers_fully_anonymous.csv
├── output/                       # Generated visualizations
│   └── shared_revenue_network_anonymous.html
└── requirements.txt              # Python dependencies
```

## 💡 Use Cases

1. **Healthcare Analytics**: Understanding provider collaboration patterns
2. **Network Analysis**: Identifying key provider relationships
3. **Revenue Analysis**: Shared patient economics
4. **Data Science Portfolio**: Demonstrating graph analysis skills
5. **Privacy-Safe Research**: Methodology for sensitive data visualization

## 🎨 Visualization Features

- **Interactive Network Graph**: Zoom, pan, hover for details
- **Revenue-Based Edge Thickness**: Visual representation of financial relationships
- **Specialty Filtering**: Focus on specific provider types
- **Connection Statistics**: Detailed analysis tables
- **Privacy Banner**: Clear indication of synthetic data use

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test with synthetic data only
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

**Samuel Peters**
- GitHub: [@spp0904](https://github.com/spp0904)
- Repository: [Provider-Network-Visualization-](https://github.com/spp0904/Provider-Network-Visualization-)

---

⚡ **Built with privacy-first principles for healthcare data analysis**