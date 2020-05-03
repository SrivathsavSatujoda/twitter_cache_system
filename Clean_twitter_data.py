#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import re


# In[6]:


# set input/output file paths for twitter data
input_path = "C:/Users/Sam/Documents/Data_Bases/music_tweets.csv"
output_path = "C:/Users/Sam/Documents/Data_Bases/music_tweets_cleaned.csv"


# In[4]:


tweets = pd.read_csv(input_path)


# In[5]:


tweets.head()


# In[7]:


tweets.tail()


# In[8]:


tweets.shape


# In[10]:


# remove first two characters ['b]
tweets["text"] = tweets["text"].str[2:]
# remove last character [']
tweets["text"] = tweets["text"].str[:-1]


# In[11]:


tweets["text"][5852]


# In[12]:


# remove links
tweets["text"] = tweets["text"].replace(r"http\S+", "", regex=True)


# In[13]:


tweets["text"][5852]


# In[14]:


# remove unicode
tweets["text"] = tweets["text"].replace(r"\\x[a-z0-9]{2}", "", regex=True)


# In[15]:


tweets["text"][5852]


# In[16]:


# remove newlines
tweets["text"] = tweets["text"].replace(r"\\n", " ", regex=True)


# In[17]:


tweets["text"][5852]


# In[18]:


# replace user name with generic @user
tweets["text"] = tweets["text"].replace(r"@\S+", "@user", regex=True)


# In[19]:


tweets["text"][5852]


# In[20]:


# remove hastag terms
tweets["text"] = tweets["text"].replace(r"#\S+", "", regex=True)


# In[21]:


tweets["text"][5852]


# In[22]:


# to lowercase
tweets["text"] = tweets["text"].str.lower()


# In[23]:


tweets["text"][5852]


# In[24]:


# remove anything not a letter, space, or @
tweets["text"] = tweets["text"].replace(r"[^a-zA-Z\s@]", "", regex=True)


# In[25]:


tweets["text"][5852]


# In[26]:


# replace multiple whitespaces with one
tweets["text"] = tweets["text"].replace(r"\s+", " ", regex=True)


# In[24]:


tweets["tweet"][5852]


# In[25]:


# remove leading and trailing whitespace
tweets["tweet"] = tweets["tweet"].str.strip()


# In[26]:


tweets["tweet"][5852]


# In[27]:


# remove empty entries in dataframe
tweets = tweets[tweets["tweet"] != ""]


# In[ ]:


from nltk.tokenize import WordPunctTokenizer
tok = WordPunctTokenizer()
#@ mentions
pat1 = r'@[A-Za-z0-9]+' 
#Url links
pat2 = r'https?://[A-Za-z0-9./]+'
combined_pat = r'|'.join((pat1, pat2))
def tweet_cleaner(text):
    #html decoding using beautiful soup
    soup = BeautifulSoup(text, 'lxml') 
    souped = soup.get_text()
    stripped = re.sub(combined_pat, '', souped)
    try:
        clean = stripped.decode("utf-8-sig").replace(u"\ufffd", "?")
    except:
        clean = stripped
    letters_only = re.sub("[^a-zA-Z]", " ", clean)
    lower_case = letters_only.lower()
    # During the letters_only process two lines above, it has created unnecessay white spaces,
    # I will tokenize and join together to remove unneccessary white spaces
    words = tok.tokenize(lower_case)
    return (" ".join(words)).strip()


# In[ ]:


cleaned_tweets = []
for t in tweets.text:
    cleaned_tweets.append(tweet_cleaner(t))


# In[ ]:


tweets.drop(columns='text', inplace =True)
tweets['text'] = cleaned_tweets


# In[28]:


# remove duplicates within each class


# In[29]:


# remove tweets that do not meet minimum length (10 chars?)


# In[30]:


tweets.shape


# In[31]:


# output cleaned data
tweets.to_csv(output_path)


# In[ ]:




