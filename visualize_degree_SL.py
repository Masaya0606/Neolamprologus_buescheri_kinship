import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# **Load files**
degree1 = pd.read_csv("Updated_king.kin_degree1_refMap.csv", sep=",", engine="python")
degree2 = pd.read_csv("Updated_king.kin_degree2_refMap.csv", sep=",", engine="python")
degree3 = pd.read_csv("Updated_king.kin_degree3_refMap.csv", sep=",", engine="python")
all_kinship = pd.read_csv("Updated_king.kin0_refMap.csv", sep=",", engine="python")
location_info = pd.read_csv("updated_individual_info_sex_SL_social_rank_HaremID_2", sep="\t", engine="python")
additional_location_info = pd.read_csv("Updated_Nest_Social_status_param_2.txt", sep="\t", engine="python")

# **Set criteria**
criteria = {
    "Degree1": {"HetHet": 0.07, "IBS0": 0.002, "Kinship": 0.1768},
    "Degree2": {"HetHet": 0.05, "IBS0": 0.0027, "Kinship": 0.0884},
    "Degree3": {"HetHet": 0.03, "IBS0": 0.02, "Kinship": 0.0442},
}

# **Function to classify relationships**
def classify_relationship(row, criteria):
    for relation, threshold in criteria.items():
        if (
            row["HetHet"] >= threshold["HetHet"]
            and row["IBS0"] <= threshold["IBS0"]
            and row["Kinship"] >= threshold["Kinship"]
        ):
            return relation
    return None

# **Merge datasets**
dataframes = []
for degree, df in [("degree1", degree1), ("degree2", degree2), ("degree3", degree3)]:
    df["Relationship"] = df.apply(lambda row: classify_relationship(row, criteria), axis=1)
    dataframes.append(df)

# **Combine data with relationships within Degree3**
all_relationships = pd.concat(dataframes)
all_relationships = all_relationships[all_relationships["Relationship"].notnull()]

# **Color mapping**
color_map = {"Degree1": "blue", "Degree2": "green", "Degree3": "orange"}
sex_color_map = {"M": "lightblue", "F": "pink", "NA": "gray"}
edge_color_map = {"BF": "black", "BM": "purple", "H": "cyan", "J": "yellow", "SM": "red"}

# **Create network graph**
G = nx.Graph()

# **Add edges for individuals with relationships within Degree3**
for _, row in all_relationships.iterrows():
    G.add_edge(row["ID1"], row["ID2"], relationship=row["Relationship"], color=color_map[row["Relationship"]])

# **Integrate all individual location information**
combined_location_info = pd.concat([location_info, additional_location_info]).drop_duplicates(subset="ID").set_index("ID")

# **Add all individuals to G**
all_individuals = set(all_kinship["ID1"]).union(set(all_kinship["ID2"]), set(location_info["ID"]), set(additional_location_info["ID"]))
G.add_nodes_from(all_individuals)

# **Retrieve position information**
positions = {
    node: (combined_location_info.loc[node, "Longitude"], combined_location_info.loc[node, "Latitude"])
    if node in combined_location_info.index else (0, 0)
    for node in all_individuals
}

# **Set node colors based on sex**
node_colors = []
for node in G.nodes:
    if node in combined_location_info.index:
        node_colors.append(sex_color_map.get(combined_location_info.loc[node, "sex"], "gray"))
    else:
        node_colors.append("gray")

# **Adjust node sizes**
node_sizes = []
for node in G.nodes:
    if node in combined_location_info.index and pd.notna(combined_location_info.loc[node, "SL"]):
        node_sizes.append((combined_location_info.loc[node, "SL"] / combined_location_info["SL"].max()) * 2000)
    else:
        node_sizes.append(100)

# **Connect individuals with the same Harem_ID_Nest_ID using black dashed lines**
harem_edges = []
grouped_harem = additional_location_info.groupby("Harem_ID_Nest_ID")["ID"].apply(list)

for group in grouped_harem:
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            if group[i] in G.nodes and group[j] in G.nodes:
                harem_edges.append((group[i], group[j]))

# **Connect individuals with the same Harem_ID using red dotted lines**
harem_id_edges = []
grouped_harem_id = additional_location_info.groupby("Harem_ID")["ID"].apply(list)

for group in grouped_harem_id:
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            if group[i] in G.nodes and group[j] in G.nodes:
                harem_id_edges.append((group[i], group[j]))

# **Set node border colors based on `social_rank`**
node_border_colors = []
for node in G.nodes:
    if node in combined_location_info.index and pd.notna(combined_location_info.loc[node, "social_rank"]):
        node_border_colors.append(edge_color_map.get(combined_location_info.loc[node, "social_rank"], "gray"))
    else:
        node_border_colors.append("gray")

# **Set edge colors**
edge_colors = [G[u][v]["color"] if "color" in G[u][v] else "black" for u, v in G.edges]

# **Plotting**
plt.figure(figsize=(16, 12))
ax = plt.gca()

# **Draw black dashed edges for Harem_ID_Nest_ID**
nx.draw_networkx_edges(G, pos=positions, edgelist=harem_edges, edge_color="black", style="dashed", width=1.5, alpha=0.6)

# **Draw red dotted edges for Harem_ID**
nx.draw_networkx_edges(G, pos=positions, edgelist=harem_id_edges, edge_color="red", style="dotted", width=1.5, alpha=0.6)

# **Draw nodes (with borders)**
for node, (x, y) in positions.items():
    idx = list(G.nodes).index(node)  # Get node index
    ax.scatter(
        x, y, 
        s=node_sizes[idx], 
        facecolors=node_colors[idx],  # **Fill color of nodes**
        edgecolors=node_border_colors[idx],  # **Border color**
        linewidths=2,
        zorder=3
    )

# **Draw normal edges**
nx.draw_networkx_edges(G, pos=positions, edge_color=edge_colors, width=2, alpha=0.6)

# **Draw Harem_ID_Nest_ID dashed edges**
nx.draw_networkx_edges(G, pos=positions, edgelist=harem_edges, edge_color="black", style="dashed", width=1.5, alpha=0.6)

# **Add labels**
nx.draw_networkx_labels(G, pos=positions, font_size=10)

# **Create legend**
degree_legend = [Line2D([0], [0], color=color, lw=4, label=degree) for degree, color in color_map.items()]
sex_legend = [Line2D([0], [0], marker='o', color='w', markersize=10, markerfacecolor=color, label=sex) for sex, color in sex_color_map.items()]
rank_legend = [Line2D([0], [0], marker='o', color='w', markersize=10, markeredgewidth=2, markeredgecolor=color, label=rank) for rank, color in edge_color_map.items()]
legend_elements = degree_legend + sex_legend + rank_legend

harem_legend = [
    Line2D([0], [0], color="black", linestyle="dashed", lw=2, label="Harem_ID_Nest_ID Connection"),
    Line2D([0], [0], color="red", linestyle="dotted", lw=2, label="Harem_ID Connection")
]

# Add `harem_legend` to existing legend elements
legend_elements += harem_legend

# **Place legend in the upper right**
plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=12)

plt.title("Geographic Network with Clone, Degree Relationships, SL-based Node Size, Social Rank Borders, and Harem Connections")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.show()
