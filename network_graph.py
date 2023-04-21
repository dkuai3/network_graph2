
from pyvis.network import Network
import difflib
import networkx as nx
import streamlit as st
import streamlit.components.v1 as components
import csv
import pandas as pd

st.title('Network Graph Visualization of Adverse Drug Event (ADE) Data')

#Extract list of unique drug names 
file1 = open('faers_nodes_all_drugnames_04-10-2023.csv')
csvreader1 = csv.reader(file1)

header1 = []
header1 = next(csvreader1)

drugs = []

for row in csvreader1: 
        drugs.append(row[2])
    
file1.close()

#Get unique drug names
drugs = list(set(drugs))

#Get user input of drug name
drug_name = st.text_input("Enter drug name: ")

#Find close matches to inputted drug name
close_matches = difflib.get_close_matches(drug_name, drugs, n = 5)
st.write('Here are some close matches: ', close_matches)

# Have user input final choice for drug name
drug_name = st.text_input("Enter a drug name from the provided list of similar matches (case sensitive!): ")
if '"' or "'" in drug_name: 
    drug_name = drug_name[1:-1]
else: 
    drug_name = drug_name

st.write("Below is the network graph for your chosen drug.")
st.write("You can hover over each node to see more information about the patient.")

#Extract nodes data and append to dict 
file2 = open('faers_nodes_all_drugnames_04-10-2023.csv')
csvreader2 = csv.reader(file2)

header2 = []
header2 = next(csvreader2)
caseids = []

ind = 0
data_dict = {'nodes': [], 'links': []}
for row in csvreader2: 
    if row[2] == drug_name:
        caseids.append(row[1])
        data_dict['nodes'].append({'caseid': row[1], 'drugname': row[2], 'total_entries': row[3], 'died': row[8]})
        if row[8] == '0': 
            data_dict['nodes'][ind]['died'] = 0 #Add binary variable to show if death was an outcome or not (0 = no, 1 = yes death)
        else: 
            data_dict['nodes'][ind]['died'] = 1
        ind += 1

file2.close()

#Remove duplicate caseid (if any)
caseids = list(set(caseids))

#Extract edges data and append to dict 
file3 = open('faers_edges_final_03-31-2023.csv')
csvreader3 = csv.reader(file3)

header = []
header = next(csvreader3)

for row in csvreader3: 
    if (row[1] in caseids) or (row[2] in caseids):
        data_dict['links'].append({'source': row[1], 'target': row[2]})

file3.close()

#Load ADE data - will be used in tooltip
ADE_data_full = pd.read_csv('ADE-V2.csv', sep = ';')

ADE_data_unique = ADE_data_full.drop_duplicates(subset = 'caseid', keep = 'first')
ADE_data_unique = ADE_data_unique.reset_index()

#Add Nodes 
net = Network(height = '1500px', width = '100%')

nodes = data_dict['nodes']
node_inds = {}

for i in range(len(nodes)):
    if nodes[i]['died'] == 0:
        color = "green"
    else: 
        color = "red"
    if int(nodes[i]['total_entries']) <= 5:
        size = 5
    elif int(nodes[i]['total_entries']) > 5 and int(nodes[i]['total_entries']) <= 10:
        size = 20
    elif int(nodes[i]['total_entries']) > 10 and int(nodes[i]['total_entries']) <= 20:
        size = 40
    else:
        size = 60
    ind = ADE_data_unique[ADE_data_unique['caseid'] == int(nodes[i]['caseid'])].index[0]
    age = ADE_data_unique._get_value(ind, 'age')
    sex = ADE_data_unique._get_value(ind, 'sex')
    wt = ADE_data_unique._get_value(ind, 'wt')
    rc = ADE_data_unique._get_value(ind, 'reporter_country')
    title = 'Age: ' + str(age) + '\n' + 'Sex: ' + sex + '\n' + 'Weight (lbs): ' + str(wt) + '\n' + 'Reporter Country: ' + rc
    net.add_node(i, label = nodes[i]['caseid'], color = color, size = size, title = title)
    node_inds[nodes[i]['caseid']] = i

#Add Edges
edges = data_dict['links']

for i in range(len(edges)):
    try:
        source = edges[i]['source']
        target = edges[i]['target']
        source_ind = node_inds[source]
        target_ind = node_inds[target]
        net.add_edge(source_ind, target_ind)
    except:
        continue

#Visualize the graph with edges
net.barnes_hut()

path = '/tmp'
net.save_graph(f'{path}/pyvis_graph.html')
HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding = 'utf-8')

components.html(HtmlFile.read(), height = 435)