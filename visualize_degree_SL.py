import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D  # Import Line2D for legend

# Load files
degree1 = pd.read_csv("king.kin_degree1_refMap.csv", sep=",", engine="python")
degree2 = pd.read_csv("king.kin_degree2_refMap.csv", sep=",", engine="python")
degree3 = pd.read_csv("king.kin_degree3_refMap.csv", sep=",", engine="python")
location_info = pd.read_csv("individual_info_sex_SL", sep="\t", engine="python")
additional_location_info = pd.read_csv("Nest_Social_status_param.txt", sep="\t", engine="python")

# Set criteria
criteria = {
    "Clone": {"HetHet": 0.1, "IBS0": 0.001, "Kinship": 0.45},
    "Degree1": {"HetHet": 0.07, "IBS0": 0.002, "Kinship": 0.35},
    "Degree2": {"HetHet": 0.05, "IBS0": 0.01, "Kinship": 0.15},
    "Degree3": {"HetHet": 0.03, "IBS0": 0.02, "Kinship": 0.05},
}

# Function to classify relationships
def classify_relationship(row, criteria):
    for relation, threshold in criteria.items():
        if (
            row["HetHet"] >= threshold["HetHet"]
            and row["IBS0"] <= threshold["IBS0"]
            and row["Kinship"] >= threshold["Kinship"]
        ):
            return relation
    return None

# Merge datasets
dataframes = []
for degree, df in [("degree1", degree1), ("degree2", degree2), ("degree3", degree3)]:
    df["Relationship"] = df.apply(lambda row: classify_relationship(row, criteria), axis=1)
    dataframes.append(df)

# Concatenate data
all_relationships = pd.concat(dataframes)
all_relationships = all_relationships[all_relationships["Relationship"].notnull()]

# Color mapping
color_map = {"Clone": "red", "Degree1": "blue", "Degree2": "green", "Degree3": "orange"}
sex_color_map = {"M": "lightblue", "F": "pink"}

# Create network graph
G = nx.Graph()
for _, row in all_relationships.iterrows():
    G.add_edge(row["ID1"], row["ID2"], relationship=row["Relationship"], color=color_map[row["Relationship"]])

# Merge location info
combined_location_info = pd.concat([location_info, additional_location_info]).drop_duplicates(subset="ID").set_index("ID")

# Remove nodes without location info
G.remove_nodes_from([node for node in G.nodes if node not in combined_location_info.index])

# Set node colors based on sex
node_colors = [sex_color_map.get(combined_location_info.loc[node, "sex"], "gray") for node in G.nodes]

# Retrieve SL values and fill missing values with the median
valid_nodes = list(G.nodes)  # Explicitly list G.nodes
SL_values = combined_location_info.loc[valid_nodes, "SL"].fillna(combined_location_info["SL"].median())

# Scale node sizes
node_sizes = (SL_values / SL_values.max()) * 2000  # Adjust max size to 2000

# Set edge colors
edge_colors = [G[u][v]["color"] for u, v in G.edges]

# Retrieve positions
positions = {node: (combined_location_info.loc[node, "Longitude"], combined_location_info.loc[node, "Latitude"]) for node in G.nodes}

# Validate data
print("Number of nodes:", len(G.nodes))
print("Number of SL values:", len(SL_values))
print("Positions:", list(positions.items())[:5])  # Check first 5 positions

# Plot
plt.figure(figsize=(16, 12))
nx.draw_networkx_nodes(G, pos=positions, node_color=node_colors, node_size=node_sizes)
nx.draw_networkx_edges(G, pos=positions, edge_color=edge_colors, width=2, alpha=0.6)
nx.draw_networkx_labels(G, pos=positions, font_size=10)

# Create legend
degree_legend = [Line2D([0], [0], color=color, lw=4, label=degree) for degree, color in color_map.items()]
sex_legend = [Line2D([0], [0], marker='o', color='w', markersize=10, markerfacecolor=color, label=sex) for sex, color in sex_color_map.items()]
legend_elements = degree_legend + sex_legend

# Place legend outside the plot (right side)
plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=12)

plt.title("Geographic Network with Clone, Degree Relationships, and SL-based Node Size")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Adjust layout to avoid overlapping with legend
plt.tight_layout()
plt.show()
