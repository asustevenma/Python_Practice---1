
import networkx
from operator import itemgetter
import matplotlib.pyplot
import numpy as np

# Read the data from the amazon-books.txt;
# populate amazonProducts nested dicitonary;
# key = ASIN; value = MetaData associated with ASIN
# The text data is already read into fhr
amazonBooks = {}
fhr.readline()
for line in fhr:
    cell = line.split('\t')
    MetaData = {}
    MetaData['Id'] = cell[0].strip() 
    ASIN = cell[1].strip()
    MetaData['Title'] = cell[2].strip()
    MetaData['Categories'] = cell[3].strip()
    MetaData['Group'] = cell[4].strip()
    MetaData['SalesRank'] = int(cell[5].strip())
    MetaData['TotalReviews'] = int(cell[6].strip())
    MetaData['AvgRating'] = float(cell[7].strip())
    MetaData['DegreeCentrality'] = int(cell[8].strip())
    MetaData['ClusteringCoeff'] = float(cell[9].strip())
    amazonBooks[ASIN] = MetaData
fhr.close()

# Read the data from amazon-books-copurchase.adjlist;
# assign it to copurchaseGraph weighted Graph;
# node = ASIN, edge= copurchase, edge weight = category similarity
fhr=open("amazon-books-copurchase.edgelist", 'rb')
copurchaseGraph=networkx.read_weighted_edgelist(fhr)
fhr.close()

print ("Looking for Recommendations for Customer Purchasing this Book:")
print ("--------------------------------------------------------------")
purchasedAsin = '0805047905'

# Let's first get some metadata associated with this book
print ("ASIN = ", purchasedAsin) 
print ("Title = ", amazonBooks[purchasedAsin]['Title'])
print ("SalesRank = ", amazonBooks[purchasedAsin]['SalesRank'])
print ("TotalReviews = ", amazonBooks[purchasedAsin]['TotalReviews'])
print ("AvgRating = ", amazonBooks[purchasedAsin]['AvgRating'])
print ("DegreeCentrality = ", amazonBooks[purchasedAsin]['DegreeCentrality'])
print ("ClusteringCoeff = ", amazonBooks[purchasedAsin]['ClusteringCoeff'])
    
###############################################################################

#     Get the depth-1 ego network of purchasedAsin from copurchaseGraph,
#     and assign the resulting graph to purchasedAsinEgoGraph.
purchasedAsinEgoGraph = networkx.ego_graph(copurchaseGraph, purchasedAsin, radius=1)

# plot the graph and the ego network

pos = networkx.spring_layout(copurchaseGraph)  
matplotlib.pyplot.figure(figsize=(10,10))
networkx.draw_networkx_labels(copurchaseGraph,pos,font_size=20)
networkx.draw(copurchaseGraph, pos=pos, node_size=1500, node_color='r', edge_color='r', style='dashed')
networkx.draw(purchasedAsinEgoGraph, pos=pos, node_size=1000, node_color='b', edge_color='b', style='solid')
matplotlib.pyplot.show()

###############################################################################

#     Use the island method on purchasedAsinEgoGraph to only retain edges with 
#     threshold >= 0.5, and assign resulting graph to purchasedAsinEgoTrimGraph
threshold = 0.5
purchasedAsinEgoTrimGraph = networkx.Graph()
for f, t, e in purchasedAsinEgoGraph.edges(data=True):
    if e['weight'] >= threshold:
        purchasedAsinEgoTrimGraph.add_edge(f,t,e)

###############################################################################

#     Find the list of neighbors of the purchasedAsin in the 
#     purchasedAsinEgoTrimGraph, and assign it to purchasedAsinNeighbors
purchasedAsinNeighbors = purchasedAsinEgoTrimGraph.neighbors(purchasedAsin)

###############################################################################

# We make recommendations on the basis of SalesRank, AvgRating and TotalReviews.
# But first, we filter out those which have clustering coefficient >= 0.5.
# After that, we sort these ASINs based on SalseRank, AvgRating and TotalReviews separately, and we assign the ASINs with different weights.
# For SalesRank, we assign the ASIN the highest weight to the rank (the highest weight the number of all ASINs in purchasedAsinNeighbors).
# For AvgRating, we use the original rating as the weight.
# For TotalReviews, we standardize the number of reviews as the weight and add 1 to each of them, in order to avoid extreme values and negative values
# Finally, we sum up all the weights for each ASIN, and select the top 5 as our recommendation

# Filter out those who have clustering coefficient >= 0.5 to narrow down candicate nodes
Filtered_neighbors = []
for filtered_user in purchasedAsinNeighbors:
    if amazonBooks[filtered_user]['ClusteringCoeff'] >= 0.5:
        Filtered_neighbors.append(filtered_user)

# Creat dictionaries for each measuring criteria
Rank = {}
Rating = {}
Review = {}
for user in Filtered_neighbors:
    Rank[user] = amazonBooks[user]['SalesRank']
    Rating[user] = amazonBooks[user]['AvgRating']
    Review[user] = amazonBooks[user]['TotalReviews']
    
Sorted_Rank = sorted(Rank.items(), key=itemgetter(1))
Sorted_Rating = sorted(Rating.items(), key=itemgetter(1), reverse=True)
Sorted_Review = sorted(Review.items(), key=itemgetter(1), reverse=True)

# Creat list for ASINs under Rank criteria(already sorted)
Sorted_Rank_list = []
for user1 in Sorted_Rank:
    Sorted_Rank_list.append(user1[0])
    
# Standarization on TotalReviews
Sum_Review = 0
Std_list = []
for user3 in Sorted_Review:
    Sum_Review += user3[1]
    Std_list.append(user3[1])
Avg_Review = Sum_Review/len(Sorted_Review)
Std_Review = np.std(Std_list)

# Assign weight points for each ASIN under each criteria
Weighted_Rank = {}
for weight_point1 in Sorted_Rank_list:
    Weighted_Rank[weight_point1] = int(len(Sorted_Rank_list)) - int(Sorted_Rank_list.index(weight_point1))

Weighted_Rating = {}
for weight_point2 in Sorted_Rating:
    Weighted_Rating[weight_point2[0]] = weight_point2[1]

Weighted_Review = {}
for weight_point3 in Sorted_Review:
    Weighted_Review[weight_point3[0]] = ((weight_point3[1] - Avg_Review)/Std_Review) + 1

Total_pts = {}
for i in Weighted_Rank.keys():
    for j in Weighted_Rating.keys():
        for k in Weighted_Review.keys():
            if i == j and j == k:
                Total_pts[i] = Weighted_Rank[i] + Weighted_Rating[j] + Weighted_Review[k]

###############################################################################

# Print Top 5 recommendations (ASIN, and associated Title, Sales Rank, 
# TotalReviews, AvgRating, DegreeCentrality, ClusteringCoeff)

Recommend_list = sorted(Total_pts.items(), key=itemgetter(1), reverse=True)[:5]
print()
print("==============================================================")
print()
print("Top 5 Recommendations for Customer Purchasing this Book:")
print("--------------------------------------------------------------")
for recommend in Recommend_list:
    print ("ASIN = ", recommend[0]) 
    print ("Title = ", amazonBooks[recommend[0]]['Title'])
    print ("SalesRank = ", amazonBooks[recommend[0]]['SalesRank'])
    print ("TotalReviews = ", amazonBooks[recommend[0]]['TotalReviews'])
    print ("AvgRating = ", amazonBooks[recommend[0]]['AvgRating'])
    print ("DegreeCentrality = ", amazonBooks[recommend[0]]['DegreeCentrality'])
    print ("ClusteringCoeff = ", amazonBooks[recommend[0]]['ClusteringCoeff'])
    print ("--------------------------------------------------------------")
