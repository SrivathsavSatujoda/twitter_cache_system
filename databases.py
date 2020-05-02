from flask import Flask, request, render_template, jsonify
import pandas as pd
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import WhiteListRoundRobinPolicy, DowngradingConsistencyRetryPolicy
from cassandra.query import dict_factory
from collections import OrderedDict
import time
import psycopg2

app = Flask(__name__)


class Tweets_client:

    def __init__(self):
        self.cache = OrderedDict()
        self.max_cache = 2500
    
    def user_input(self):
        print('''Welcome to the twitter search application. Choose your search by option:
                              1 to Search by Genre
                              2 to Search by User name
                              3 to Search by TweetID
                              4 to Search by Date
                              5 to exit \n''')
                              
        i = int(input())
        query = self.choice(i)
        return query


    def choice(self,i):
        if (i==1):
            query = self.search_by_genre()
        elif(i==2):
            query = self.search_by_username()
        elif(i==3):
            query = self.search_by_tweetid()
        elif(i==4):
            query = self.search_by_date()
        elif(i==5):
            query = self.search_by_word()
        elif(i==6):
            exit_func()
        else:
            print("***Invalid Choice***")
            exit()
        return query

    def exit_func(self):
        print ('*****Thank you and have a great day*****')
        pass

    def search_by_genre(self):
        print('''Enter your genre of choice
                 1 for Rock
                 2 for Rap
                 3 for Pop
                 4 for Instrumental \n''')
        genre_choice = int(input())
        print(genre_choice)
        if (genre_choice == 1):
            query = 'select tweet_id from "Information" where category=\'rock\''
        elif (genre_choice == 2):
            query = 'select tweet_id from "Information" where category=\'rap\''
        elif (genre_choice == 3):
            query = 'select tweet_id from "Information" where category=\'pop\''
        elif (genre_choice == 4):
            query = 'select tweet_id from "Information" where category=\'instrumental\''
        else:
            print("Invalid choice\n")
            exit()

        return query


    def search_by_tweetid(self):
        print('''Please select if you want to search for a particular tweetID or range of ids:
                 1 for single tweetID
                 2 for range of IDs \n''')
        range_or_single = int(input())
        if (range_or_single == 1):
            print ("Enter the tweetID (valid range 1-10000):\n")
            tweet_id = int(input())
            query = 'select tweet_id from "Information" where tweet_id={}' .format(tweet_id)
        elif(range_or_single == 2):
            print("Enter lower tweet range:\n")
            lower = int(input())
            print("Enter upper tweet range:\n")
            upper = int(input())
            if (lower>upper):
                print("Invalid range. Lower range cant be greater than or equal to upper range. \n")
                exit()
            query = 'select tweet_id from "Information" where tweet_id between {} and {}'.format(lower,upper)

        return query

    def search_by_username(self):
        global username
        print("Please enter the username: \n")
        username = input()
        query = 'select tweet_id from "Information" where user_name = \'{}\''.format(username)
        return query

    def search_by_date(self):
        print("Please enter the date range (date format YYYY-MM-DD): \n")
        print("Enter start-date:\n")
        lower_range = input()
        print("Enter end-date:\n")
        upper_range = input()
        query = "select tweet_id from \"Information\" where time>='{}' and time < '{}'".format(lower_range,upper_range)
        return query

    def init_cassandra(self):
        # returns connection object
        profile = ExecutionProfile(
            load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1']),
            retry_policy=DowngradingConsistencyRetryPolicy(),
            row_factory=dict_factory
        )
        cluster = Cluster(execution_profiles={EXEC_PROFILE_DEFAULT: profile})
        session = cluster.connect()
        print('******Connection to Cassnadra establised******')
        return session

    def init_postgre(self):
        # returns connection object
        conn = psycopg2.connect(host="localhost", port=5432, database="TweetInfo", user="postgres", password="1234")
        cur = conn.cursor()
        print('******Connection to Postgre established******')
        return cur


    def fetch_tweetIDS(self,query,postgre_conn):
        #given a query fetches tweet ids that match the query
        tweet_ids = []
        postgre_conn.execute(query)
        query_result = postgre_conn.fetchall()
        #we have to convert the tuples to list
        for x in query_result:
            tweet_ids.append(x[0])
        return tweet_ids



    def fetch_tweet(self,tweetid,cass_conn):
        #returns the final result
        session = cass_conn
        session.set_keyspace('music_tweets')
        rows = session.execute('SELECT * FROM tweets where tweet_id = {}'.format(tweetid))
        for x in rows:
            dict_data = x
        return dict_data

    def fetch_tweet_from_cache(self,tweet_id):
        if (tweet_id in self.cache):
            return self.cache[tweet_id]
        return None
        #returns the final result from cache


    def write_to_csv(self, df):
        df.to_csv("query_result.csv")
        return None


    def run(self, query, cache_status):

        cass_conn = self.init_cassandra()
        postgre_conn = self.init_postgre()
        start_time = time.time()
        tweet_ids = self.fetch_tweetIDS(query, postgre_conn)
        dict_list = []
        hit_count = 0
        for id in tweet_ids:
            if (cache_status):

                temp_dict = self.fetch_tweet_from_cache(id)
                if (temp_dict):
                    del self.cache[id]
                    self.cache[id] = temp_dict
                    hit_count+=1
                else:
                    temp_dict = self.fetch_tweet(id, cass_conn)
                    # updating cache
                    if (len(self.cache) >= self.max_cache):
                        self.cache.popitem(False)
                    self.cache[id] = temp_dict
            else:
                temp_dict = self.fetch_tweet(id, cass_conn)
            dict_list.append(temp_dict)

        if (cache_status):
            print("Hit rate to cache: ", 0 if len(tweet_ids) == 0 else float(hit_count / len(tweet_ids)))



        df_cass = pd.DataFrame(dict_list)
        print("Execution time:"+ str(time.time()-start_time) + "\n")
        execution_time = time.time()-start_time
        #print(df_cass)

        cass_conn.shutdown()
        postgre_conn.close()
        return execution_time , df_cass, 0 if len(tweet_ids) == 0 else float(hit_count / len(tweet_ids) * 100)

@app.route('/')
def resolve_query():
    global tweets_client
    global username
    cache_status = request.args.get('cache_is_enabled') == 'True'
    #tweets_client =  Tweets_client(enable_caching=cache_status)
    print(request.args)
    #print(type(request.args))
    #print(request.args.get('cache_is_enabled'))
    if request.args.get("query_type") is not None:
        if request.args.get("query_type")=="genre":
            if request.args.get("genre_radio_button")=="Rock":
                query = 'select tweet_id from "Information" where category=\'rock\''
            elif request.args.get("genre_radio_button")=="Rap":
                query = 'select tweet_id from "Information" where category=\'rap\''
            elif request.args.get("genre_radio_button")=="Pop":
                query = 'select tweet_id from "Information" where category=\'pop\''
            elif request.args.get("genre_radio_button")=="Instrumental":
                query = 'select tweet_id from "Information" where category=\'instrumental\''
        elif request.args.get("query_type") == "username":
            username = request.args.get("username")
            query = 'select tweet_id from "Information" where user_name = \'{}\''.format(username)
        elif request.args.get("query_type") == "tweetid_single":
            tweet_id = request.args.get("tweet_id")
            query = 'select tweet_id from "Information" where tweet_id={}'.format(tweet_id)
        elif request.args.get("query_type") == "select_range":
            lower = request.args.get("lower_range")
            upper = request.args.get("upper_range")
            query = 'select tweet_id from "Information" where tweet_id between {} and {}'.format(lower,upper)
        elif request.args.get("query_type")=="date":
            lower_range = request.args.get("start_date")
            upper_range = request.args.get("end_date")
            query = "select tweet_id from \"Information\" where time>='{}' and time < '{}'".format(lower_range,upper_range)
        
        print(query,cache_status)
        res = tweets_client.run(query, cache_status)
     #print(tweets_client.run(query))
        print(request)
        cols = res[1].columns.tolist()
        exec_time = res[0]
        hit_rate = res[2]
        return (render_template("index.html", columns = cols, data = res[1] , exec_time=exec_time , hit_rate = hit_rate))
    else:
        return (render_template("index.html"))
    

if __name__ == "__main__":
    tweets_client = Tweets_client()
    
    app.run(port = 5001)


    # tweets_client = Tweets_client(enable_caching=True)
    # query1 = 'select tweet_id from "Information" where tweet_id between 1 and 1000'
    # query2 = 'select tweet_id from "Information" where tweet_id between 500 and 1000'
    # query3 = 'select tweet_id from "Information" where tweet_id between 750 and 1250'
    # # cache disabled time = 16.268s
    # # cache enabled_time = 10.343s
    # exec_time1 = tweets_client.run(query1)
    # # query = tweets_client.user_input()
    # exec_time2 = tweets_client.run(query2)
    # # query = tweets_client.user_input()
    # exec_time3 = tweets_client.run(query3)
    # print("Total execution time: ", exec_time1 + exec_time2 + exec_time3)
    # '''





# '''
# #query = tweets_client.user_input()
#
#
# '''
#
# '''
#     tweets_client = Tweets_client(enable_caching=True)
#     query = tweets_client.user_input()
#     exec_time = tweets_client.run(query)
#     print('The execution time: ', exec_time)
#     print("Do you want to write the results to a file? Press 1 for yes\n")
#     yes = int(input())
#     if(yes==1):
#         tweets_client.write_to_csv(df)
#     else:
#         pass
# '''




