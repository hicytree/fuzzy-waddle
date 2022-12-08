import csv
import json
import matplotlib.pyplot as plt
import numpy as np
import spotipy
import pandas as pd
from pandas import DataFrame as df
from scipy.spatial.distance import cdist, euclidean
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import statistics
import warnings
import random
from matplotlib.animation import FuncAnimation
import weakref

# accesses the Spotify web api
_CLIENT_ID = "cada1a6f03b84727b0e5c59c973bd5a1"
_CLIENT_SECRET = "25d8778fe7ea435fb964260e80bf6214"
 
warnings.filterwarnings("ignore", category=DeprecationWarning)
 
token = spotipy.oauth2.SpotifyClientCredentials(client_id=_CLIENT_ID, client_secret=_CLIENT_SECRET)
cache_token = token.get_access_token()
sp = spotipy.Spotify(cache_token)
 
genre_songs = []
genre_names = []

f = open('songsbygenre.json')
genres = json.load(f)
for genre in genres.keys():
    genre_songs.append(genres[genre])
    genre_names.append(genre)
f.close()

year_songs = []
year_names = []

f2 = open('testhits.json')
yearhits = json.load(f2)
for year in yearhits.keys():
    year_songs.append(yearhits[year])
    year_names.append(year)
f2.close()

#creates clusters with all the data and algorithms that come with it
class Spotify_Clustering:
 
    # sets up global variables with class is instantiated
    def __init__(self):
        self.center_points = []
        self.km = []
        self.cluster_name = {}
 
    # calculates the pca values of each song in the playlist and returns the list of pca values
    def pca_calculation(self, songs):
        cur_num = 1
        song_features = []

        for song in songs:
            audio_features = song[list(song.keys())[0]][0]
            if audio_features == None:
                continue
            print(cur_num, list(song.keys())[0].split('::')[0])
            cur_num += 1

            song_features.append(audio_features)
        print()

        df = pd.DataFrame.from_dict(song_features)

        scaler = StandardScaler()
        scaler.fit(df)
        scaled_data = scaler.transform(df)
 
        pca = PCA(n_components=3)
        pca.fit(scaled_data)
 
        return pca.transform(scaled_data)
 
    # using the 3 dimensional points in the list of pca values, find the geometric median of the set of points and return it
    def find_geo_med(self, pca):
        x_vals = []
        y_vals = []
        z_vals = []
 
        for i in range(len(pca)):
            x_vals.append(pca[i][0])
            y_vals.append(pca[i][1])
            z_vals.append(pca[i][2])
 
        list_points = []
        for i in range(len(x_vals)):
            coor = []
            coor.append(x_vals[i])
            coor.append(y_vals[i])
            coor.append(z_vals[i])
            list_points.append(coor)
 
        list_points = np.array(list_points)
        return self.geometric_median(list_points)
 
    # helper method to find_geo_med() that takes in a list of 3-D points and returns the geometric median of the set of points
    def geometric_median(self, X, eps=1e-5):
        y = np.mean(X, 0)
 
        while True:
            D = cdist(X, [y])
            nonzeros = (D != 0)[:, 0]
 
            Dinv = 1 / D[nonzeros]
            Dinvs = np.sum(Dinv)
            W = Dinv / Dinvs
            T = np.sum(W * X[nonzeros], 0)
 
            num_zeros = len(X) - np.sum(nonzeros)
            if num_zeros == 0:
                y1 = T
            elif num_zeros == len(X):
                return y
            else:
                R = (T - y) * Dinvs
                r = np.linalg.norm(R)
                rinv = 0 if r == 0 else num_zeros / r
                y1 = max(0, 1 - rinv) * T + min(1, rinv) * y
 
            if euclidean(y, y1) < eps:
                return y1
 
            y = y1
 
    # takes in the number of clusters and graphs the geometrical medians on the 3-D figure, coloring them based on the cluster they belong to
    def graph_clusters(self, num_cluster):
        fig = plt.figure("Genre Trends", figsize=(15, 15))
 
        ax = fig.add_subplot(111, projection='3d')
        #ax.set_xlabel('Principle Component 1')
        #ax.set_ylabel('Principle Component 2')
        #ax.set_zlabel('Principle Component 3')
 
        x_geomeds = []
        y_geomeds = []
        z_geomeds = []
 
        i = 0
        font = {'family': 'serif',
                'color': 'darkred',
                'weight': 'normal',
                'size': 10,
                }
        
        for coor in self.center_points[:len(genres)]:
            x_geomeds.append(coor[0])
            y_geomeds.append(coor[1])
            z_geomeds.append(coor[2])
            ax.text(coor[0], coor[1], coor[2], list(genres.keys())[i], fontdict=font, size=10, zorder=1, color='gray')
            i += 1
 
        y_predicted = self.km[num_cluster - 1].fit_predict(self.df_geomeds)
        self.df_geomeds['cluster'] = y_predicted
        
        for i in range(len(genres)):
            if i < len(genres):
                self.cluster_name.update({list(genres.keys())[i]: y_predicted[i]})
        
        for i in range(num_cluster):
            rand_color = '#%02x%02x%02x' % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            cluster = self.df_geomeds[self.df_geomeds.cluster == i]
 
            ax.scatter3D(cluster['x_coor'], cluster['y_coor'], cluster['z_coor'], color=rand_color, alpha=1.0)
        
        x_line = []
        y_line = []
        z_line = []
        self.firsttime = True

        def animate(i):
            x_line.append(self.center_points[len(genres) + i][0])
            y_line.append(self.center_points[len(genres) + i][1])
            z_line.append(self.center_points[len(genres) + i][2])  
            
            if(len(x_line) == 8):
                ax.lines.clear()
                ax.texts.pop(len(genres))
                x_line.pop(0)
                y_line.pop(0)
                z_line.pop(0)
                if self.firsttime:
                    self.firsttime = False
                    x_line.pop(0)
                    y_line.pop(0)
                    z_line.pop(0)
                     
            ax.plot(x_line, y_line, z_line,color="gray")
            
            if len(x_line) > 1:
                ax.text(x_line[-1], y_line[-1], z_line[-1], list(yearhits.keys())[i], fontdict=font, size=10, zorder=1, color='black')

        animation = FuncAnimation(fig, func=animate, frames=np.arange(0, len(yearhits), 1), interval=1000)
        animation.save('./animation.gif', writer='imagemagick', fps=60)
        plt.show()

    # finds the optimal number of clusters for the data by calculating the elbow of the graph of clusters-variance
    def find_num_clusters(self):
        # sse = []
        # k_rng = range(1, len(genres) + len(yearhits))
 
        # for i in range(len(k_rng)):
        #     self.km.append(KMeans(n_clusters=k_rng[i]))
        #     self.km[i].fit(self.df_geomeds[['x_coor', 'y_coor', 'z_coor']])
        #     sse.append(self.km[i].inertia_)
 
        # areas = []
        # for j in range(len(k_rng)):
        #     T = (1 / 2) * abs(
        #         (k_rng[0] - k_rng[j]) * (sse[len(sse) - 1] - sse[0]) - (k_rng[0] - k_rng[len(k_rng) - 1]) * (
        #                     sse[j] - sse[0]))
        #     areas.append(T)
 
        # return areas.index(max(areas)) + 1
        self.km.append(KMeans(n_clusters=8))
        return 8
 
# this class sets up to find the best set of clusters by creating a variable number of clusters and graphing the cluster
class Spotify_Runner:
 
    # sets up the global variables that will hold the sets of cluster arrangements and their inertias
    def __init__(self, num_runs):
        self.spot_list = []
        self.inertias = []
 
        self.min_inertia_spot = -1
        self.best_num_cluster = -1
 
        self.num_runs = num_runs
        self.center_points = []
        self.first_pca = []
 
    # creates a num_runs number of cluster arrangements and sorts them to find the most efficient arrangement and graphing that arrangement
    def spot_creation(self):
        for i in range(self.num_runs):
            self.spot_list.append(Spotify_Clustering())
 
            if i == 0:
                for genre in genres:
                    pca = self.spot_list[i].pca_calculation(genres[genre])
                    if len(self.first_pca) == 0:
                        self.first_pca = pca
                    x, y, z = self.spot_list[i].find_geo_med(pca)
                    self.center_points.append([x, y, z])
                for year in yearhits:
                    pca = self.spot_list[i].pca_calculation(yearhits[year])
                    x, y, z = self.spot_list[i].find_geo_med(pca)
                    self.center_points.append([x, y, z])
            
            self.spot_list[i].center_points = self.center_points
            self.spot_list[i].df_geomeds = df(self.center_points[:len(genres)], columns=['x_coor', 'y_coor', 'z_coor'])

            if i == 0:
                list_num_cluster = []
                for j in range(25):
                    list_num_cluster.append(self.spot_list[0].find_num_clusters())

                self.best_num_cluster = statistics.mode(list_num_cluster)

            self.spot_list[i].find_num_clusters()
 
            # self.inertias.append(self.spot_list[i].km[self.best_num_cluster - 1].inertia_)
            # if min(self.inertias) == self.spot_list[i].km[self.best_num_cluster - 1].inertia_:
            #     self.min_inertia_spot = i

           # print("iteration %s" % i)
        
        #genre_graphing = Spotify_Clustering()
        #self.first_pca = genre_graphing.pca_calculation(genres[genre])
        #genre_graphing.graph_pca(self.first_pca)
        # self.spot_list[self.min_inertia_spot].graph_geo_med()
        # self.spot_list[self.min_inertia_spot].graph_roles()
        # self.spot_list[self.min_inertia_spot].graph_clusters(self.best_num_cluster)
        self.spot_list[0].graph_clusters(self.best_num_cluster)
        
        print("\n\n\n")
        for i in range(self.best_num_cluster):
            list_names = [key for key, value in self.spot_list[self.min_inertia_spot].cluster_name.items() if
                          value == i]
            print("Cluster " + str(i + 1) + ": ", end='')
            for j in range(len(list_names) - 1):
                print(str(list_names[j]), end=', ')
            print(list_names[len(list_names) - 1])
        
runner = Spotify_Runner(1)
runner.spot_creation()
print("\n\n\n")
