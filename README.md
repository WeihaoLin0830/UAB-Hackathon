# LatamBodyguard

## Safe Route Navigator for Latin America

LatamBodyguard is a web application developed during UAB The Hack that helps users find the safest and fastest routes between two locations in Mexico City using crime data analysis and weighted graph algorithms.

![Web Application Preview](/img/photo2.jpg)

## Project Overview

This solution was created for PayRetailers' challenge focused on solving real-world problems in South America. LatamBodyguard combines geospatial analysis with AI to provide route recommendations that prioritize both safety and efficiency.

## Key Features

- **Safety-Optimized Routes**: Generates paths that avoid high-crime areas while maintaining efficiency
- **AI-Powered Chatbot**: Uses Large Language Models to explain routing decisions with transparency
- **Crime Data Integration**: Analyzes Mexico City crime statistics to inform route calculations
- **Cluster Analysis**: Employs buffer-based clustering to distinguish between types of urban areas

![Safe Route with Buffer Zones](/img/photo1.jpg)

## How It Works

### Data Processing & Analysis
1. **Crime Data Collection**: We aggregated and processed crime incident data from Mexico City, categorizing by type, severity, and location.
2. **Geospatial Mapping**: The application creates a heat map of criminal activity across the city, identifying high-risk zones.
3. **Buffer Zones**: We implemented a buffer system around high-crime areas, with varying levels of "danger radius" based on crime type and frequency.

### Routing Algorithm
1. **Graph Construction**: The city map is converted into a weighted graph where:
   - Nodes represent intersections and key points
   - Edges represent streets and paths
   - Edge weights incorporate both distance and a calculated safety score
2. **Safety Weighting**: Each path segment is assigned a safety score derived from:
   - Proximity to high-crime areas
   - Time of day (adjusts risk factors based on historical crime patterns)
   - Crime type prevalence in the area
3. **Path Calculation**: We use a modified A* algorithm that optimizes for both shortest distance and maximum safety, allowing the system to find routes that may be slightly longer but significantly safer.

### User Experience
1. **Query Input**: Users enter starting and destination points
2. **Route Generation**: The system calculates and displays the optimal safe route
3. **AI Explanation**: The integrated LLM chatbot provides natural language explanations of:
   - Why certain areas were avoided
   - Trade-offs made between speed and safety
   - Specific safety concerns along the route

## Technical Implementation

- **Backend**: Python-based geospatial processing using GeoPandas and NetworkX for graph operations
- **AI Component**: Integration of LLM APIs for natural language processing and response generation
- **Frontend**: Interactive map visualization using Leaflet.js with custom safety overlay layers
- **Data Pipeline**: Automated processing of crime statistics with regular update capability

## Team Members

- Sergi Flores Marín
- Jiahui Chen
- Weihao Lin
- Clàudia Gallego

## Technology Stack

- Geospatial Analysis
- Weighted Graph Algorithms
- Large Language Models
- Web Development

## Challenges Overcome

- **Data Integration**: Harmonizing different crime data sources and formats
- **Algorithm Optimization**: Balancing computational efficiency with route quality
- **UX Design**: Creating an intuitive interface that clearly communicates safety information without causing alarm

## Project Impact

LatamBodyguard demonstrates the practical application of AI and data science to address real safety concerns in urban environments, offering a solution that could potentially improve daily life for people in high-crime areas of Latin America.
