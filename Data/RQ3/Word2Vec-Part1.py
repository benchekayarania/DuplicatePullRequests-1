# -*- coding: utf-8 -*-
"""Rania_Word2Vec_Part1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zsJoHExc91-OHKF9SKyPqQ2AC_V462XR

# ***Part1***
"""

# installing extra packages
!pip install distance
!pip install fuzzywuzzy

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
from nltk.corpus import stopwords
import distance
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup

from nltk.corpus import stopwords
import os
from nltk.corpus import stopwords
from fuzzywuzzy import fuzz
from sklearn.manifold import TSNE
from wordcloud import WordCloud, STOPWORDS
from os import path
from PIL import Image

from google.colab import drive
drive.mount("/content/gdrive", force_remount=True)

try:
  from google.colab import drive
  IN_COLAB=True
except:
  IN_COLAB=False

if IN_COLAB:
  print("We're running Colab")

# Commented out IPython magic to ensure Python compatibility.
if IN_COLAB:
  # Mount the Google Drive at mount
  mount='/content/gdrive'
  print("Colab: mounting Google drive on ", mount)

  drive.mount(mount)

# Switch to the directory on the Google Drive that you want to use
  import os
  drive_root = mount + "/MyDrive/W2VEC_PullRequest_VF"
  
  # Create drive_root if it doesn't exist
  create_drive_root = True
  if create_drive_root:
    print("\nColab: making sure ", drive_root, " exists.")
    os.makedirs(drive_root, exist_ok=True)
  
  # Change to the directory
  print("\nColab: Changing directory to ", drive_root)
#   %cd $drive_root

os.chdir(mount +'/MyDrive/W2VEC_PullRequest_2')

"""# ***Exploratory Data Analysis***"""

data = pd.read_csv(mount +'/MyDrive/W2VEC_PullRequest_1/W2V_3329.csv', delimiter=';', encoding='cp437')
print(f'The number of datapoints is {data.shape}')
data.head(5)

"""We have the following columns

**id:** A unique id for the Pull Request pair

**PRid1:** id of the first Pull Request.

**PRid2:** id of the second Pull Request

**Pull Request1:** the first Pull Request

**Pull Request2:** second Pull Request

**is_duplicate:** Whether both are duplicate or not.
"""

data.info()

"""# ***Checking for null values***"""

data[data.isnull().any(axis=1)]

data = data.dropna()
data.shape

"""# ***Check for duplicate entries***"""

data[data.drop(columns=['id']).duplicated()]

"""We don't have any duplicate rows present

# ***Analyzing distribution of target variable***
"""

plt.figure(figsize=(8,6))
ct = data['is_duplicate'].value_counts()
sns.barplot(x=ct.index,y=ct.values)
plt.title('Total number of values')
plt.xlabel('duplicate')
plt.ylabel('count')
plt.show()

print('Total number of Pull Request pairs is {}'.format(len(data.id.values)))
print('Pull Request pairs that are similar is {} which is {} % of total'.format(ct[1],round((ct[1]/(ct[1]+ct[0])*100)),2))
print('Pull Request pairs that are not similar is {} which is {} % of total'.format(ct[0],round((ct[0]/(ct[1]+ct[0])*100)),2))

"""# ***Number of uniques Pull Requests and repeated Pull Requests***"""

PRids = pd.Series(data.PRid2.tolist() + data.PRid1.tolist())
uniq = len(np.unique(PRids))
print('Total number of unique Pull Requests is {}'.format(uniq))
#Number of Pull Requests that repeated than 1 time
cnt = PRids.value_counts()
more1 = len(cnt[cnt.values > 1])
print('Number of Pull Requests that repeated more than 1 time is {} which is {}%'.format(more1,(more1/(len(cnt))*100)))
print('The maximum number of times a Pull Request occured is {}'.format(max(cnt)))

plt.figure(figsize=(8,6))
x = ['unique Pull Requests','repeated Pull Requests']
y = [uniq,more1]
sns.barplot(x,y)
plt.title('No of unique and repeated Pull Requests')
plt.show()

plt.figure(figsize=(20, 8))
plt.hist(PRids.value_counts(), bins=160)
plt.yscale('log')
plt.title('Log-Histogram of Pull Request appearance counts')
plt.xlabel('Number of occurences of Pull Request')
plt.ylabel('Number of Pull Requests')
plt.show()

"""# ***Basic Feature Engineering(Before cleaning the data)***

Let us now construct a few features like:

**freq_PRid1 =** Frequency of PRid1's #ie, number of times Pull Request1 occur

**freq_PRid2 =** Frequency of PRid2's

**q1len =** Length of q1

**q2len =** Length of q2

**q1_n_words =** Number of words in Pull Request 1

**q2_n_words =** Number of words in Pull Request 2

**word_Common =** (Number of common unique words in Pull Request 1 and Pull Request 2)

**word_Total =**(Total num of words in Pull Request 1 + Total num of words in Pull Request 2)

**word_share =** (word_common)/(word_Total)

**freq_q1+freq_q2 =** sum total of frequency of PRid1 and PRid2

**freq_q1-freq_q2 =** absolute difference of frequency of PRid1 and PRid2
"""

if os.path.isfile('data_with_out_preprocess.csv'):
    data = pd.read_csv("data_with_out_preprocess.csv",encoding='latin-1')
else:
    def common_wrd(row):
        x = set(row['Pull Request1'].lower().strip().split(" ")) 
        y = set(row['Pull Request2'].lower().strip().split(" "))
        return 1.0 * len(x & y)


    def total(row):
        set1 = set(row['Pull Request1'].lower().strip().split(" "))
        set2 = set(row['Pull Request2'].lower().strip().split(" "))
        return 1.0 * (len(set1) + len(set2))

    def word_share(row):
        x = row['word_common']/row['word_total']
        return  x

############################################
    
    data['freq_PRid1'] = data['PRid1'].apply(lambda x: cnt[x])
    data['freq_PRid2'] = data['PRid2'].apply(lambda x: cnt[x])
    data['q1len'] = data['Pull Request1'].apply(lambda x: len(x))
    data['q2len'] = data['Pull Request2'].apply(lambda x: len(x))
    data['q1_n_words'] = data['Pull Request1'].apply(lambda x: len(x.split(" ")))
    data['q2_n_words'] = data['Pull Request2'].apply(lambda x: len(x.split(" ")))
    data['word_common'] = data.apply(common_wrd,axis=1)
    data['word_total'] = data.apply(total,axis=1)
    data['word_share'] = data.apply(word_share,axis=1)
    data['freq_q1+q2'] = data['freq_PRid1']+data['freq_PRid2']
    data['freq_q1-q2'] = abs(data['freq_PRid1']-data['freq_PRid2'])
    data.to_csv("data_with_out_preprocess.csv", index=False)

data = pd.read_csv(mount +'/MyDrive/W2VEC_PullRequest_1/data_with_out_preprocess.csv')
data.head(3)

"""# ***Analysis on extracted features***"""

print ("Minimum length of the Pull Requests in Pull Request1 : " , min(data['q1_n_words']))

print ("Minimum length of the Pull Requests in Pull Request2 : " , min(data['q2_n_words']))

print ("Number of Pull Requests with minimum length [Pull Request1] :", data[data['q1_n_words']== 1].shape[0])
print ("Number of Pull Requests with minimum length [Pull Request2] :", data[data['q2_n_words']== 1].shape[0])

data[data['q1_n_words']== 1].head(3)

"""We can see certain Pull Requests with single word.Anyway we will keep it and proceed

# ***Analysing word share***
"""

plt.figure(figsize=(12,6))
plt.subplot(1,2,1)
sns.violinplot(x='is_duplicate',y='word_share',data=data)
plt.subplot(1,2,2)
sns.distplot(data[data['is_duplicate'] == 1]['word_share'],color='red',label='similar')
sns.distplot(data[data['is_duplicate'] == 0]['word_share'],color='blue',label='disimilar')
plt.legend()
plt.show()

"""We can see that as the word share increases there is a higher chance the Pull Requests are similar. From the histogram we can see that word share has some information differentiating similar and dissimilar classes.

# ***Analyzing word_common***
"""

plt.figure(figsize=(12,6))
plt.subplot(1,2,1)
sns.violinplot(x='is_duplicate',y='word_common',data=data)
plt.subplot(1,2,2)
sns.distplot(data[data['is_duplicate'] == 1]['word_common'],color='red',label='similar')
sns.distplot(data[data['is_duplicate'] == 0]['word_common'],color='blue',label='disimilar')
plt.legend()
plt.show()

"""We can see that common_words doesnot have enough information seperating classes.The hist plots of word_common of duplicate and non-duplicate Pull Requests are overlapping. Not much information can be retrived as most of pdf's is overlapping.

# ***Analysis on frequency of Pull Requests***
"""

# Frequency of Pull Request 1
plt.figure(figsize=(15,6))
my_count = data['freq_PRid1'].value_counts()
sns.barplot(my_count.index, my_count.values, alpha=0.8)
plt.ylabel('Number of times Pull Request 1 Occurrenced', fontsize=10)
plt.xlabel('Frequency of Pull Request', fontsize=10)
plt.show()

# Frequency of Pull Request 2
plt.figure(figsize=(15,6))
my_count = data['freq_PRid2'].value_counts()
sns.barplot(my_count.index, my_count.values, alpha=0.8)
plt.ylabel('Number of times Pull Request 2 Occurrenced', fontsize=10)
plt.xlabel('Frequency of Pull Request', fontsize=10)
plt.show()

"""# ***Adavanced Feature Engineering***

# Text Preprocessing(Cleaning)

**As a part of text preprocessing, I have done**

Removing html tags

Removing Punctuations

Performing stemming

Removing Stopwords

Expanding contractions etc.
"""

import nltk
nltk.download('stopwords')

STOP_WORDS = stopwords.words("english")


def preprocess(x):
    x = str(x).lower()
    x = x.replace(",000,000", "m").replace(",000", "k").replace("′", "'").replace("’", "'")\
                           .replace("won't", "will not").replace("cannot", "can not").replace("can't", "can not")\
                           .replace("n't", " not").replace("what's", "what is").replace("it's", "it is")\
                           .replace("'ve", " have").replace("i'm", "i am").replace("'re", " are")\
                           .replace("he's", "he is").replace("she's", "she is").replace("'s", " own")\
                           .replace("%", " percent ").replace("₹", " rupee ").replace("$", " dollar ")\
                           .replace("€", " euro ").replace("'ll", " will")
    #replacing multiple digits representation to  miilion,thoudsands etc.. eg:1000 -> 1k
    x = re.sub(r"([0-9]+)000", r"\1k", x)
    x = re.sub(r"([0-9]+)000000", r"\1m", x)  
    
    
    porter = PorterStemmer()    #apply stemming  eg: growing,growth --> grow
    pattern = re.compile('\W')  #matching word charecter
    
    if type(x) == type(''):
        x = re.sub(pattern, ' ', x)
    
    
    if type(x) == type(''):
        x = porter.stem(x)
        example1 = BeautifulSoup(x)
        x = example1.get_text()
               
    
    return x

"""More feature engineering:

cwc_min : Ratio of common_word_count to min length of word count of Q1 and Q2
  
cwc_min = common_word_count / (min(len(q1_words), len(q2_words))

cwc_max : Ratio of common_word_count to max length of word count of Q1 and Q2  

cwc_max = common_word_count / (max(len(q1_words), len(q2_words))

csc_min : Ratio of common_stop_count to min length of stop count of Q1 and Q2   

csc_min = common_stop_count / (min(len(q1_stops), len(q2_stops))

csc_max : Ratio of common_stop_count to max length of stop count of Q1 and Q2 

csc_max = common_stop_count / (max(len(q1_stops), len(q2_stops))

ctc_min : Ratio of common_token_count to min lenghth of token count of Q1 and 

Q2 ctc_min = common_token_count / (min(len(q1_tokens), len(q2_tokens))

ctc_max : Ratio of common_token_count to max lenghth of token count of Q1 and 

Q2 ctc_max = common_token_count / (max(len(q1_tokens), len(q2_tokens))

last_word_eq : Check if last word of both Pull Requests is equal or not 

last_word_eq = int(q1_tokens[-1] == q2_tokens[-1])

first_word_eq : Check if First word of both Pull Requests is equal or not 

first_word_eq = int(q1_tokens[0] == q2_tokens[0])
abs_len_diff : Abs. length difference abs_len_diff = abs(len(q1_tokens) - len(q2_tokens))

mean_len : Average Token Length of both Pull Requests mean_len = (len(q1_tokens) + len(q2_tokens))/2

fuzz_ratio : Here comes the interesting part. Fuzz ratio depends upon the Levenshtein distance. Intutively saying if the corresponding edits required from one sentance to become other is large, fuzz ratio will be small. ie, fuzz ratio will be similar for most similar words.

eg: s1 = "mumbai is a great place" s2 = "mumbai is a nice place". fuzz ratio = 91

fuzz_partial_ratio : In certain cases fuzz ratio cannot solve the issue.
fuzz.ratio("YANKEES", "NEW YORK YANKEES") ⇒ 60
fuzz.ratio("NEW YORK METS", "NEW YORK YANKEES") ⇒ 75
Both s1 and s2 mean the same. But their fuzz ratio can be smaller. So we will find the ratio for partial sentences and it will be high. In such case, it is known as a fuzz partial ratio.
fuzz.partial_ratio("YANKEES", "NEW YORK YANKEES") ⇒ 60

token_sort_ratio: In some other cases even fuzz partial ratio will fail.

For example:

fuzz.partial_ratio("MI vs RCB","RCB vs MI") ⇒ 72 Actually both the sentence have the same meaning. But the fuzz ratio gives a low result. So a better approach is to sort the tokens and then apply fuzz ratio. fuzz.token_sort_ratio("MI vs RCB","RCB vs MI") ⇒ 100

token_set_ratio: There is another type of fuzz ratio which helps even I cases where all above fails. It is the token set ratio. For that we have to first 

find the following:

t0 -> find the intersection words of sentance1 and sentance2 and sort them.

t1-> t0 + rest of tokens in sentance1.

t2-> t0 + rest of tokens in sentance2.
tocken_set_ratio = max(fuzz_ratio(to,t1),fuzz_ratio(t1,t2),fuzz_ratio(t0,t2))

longest_substr_ratio : Ratio of length longest common substring to min lenghth of token count of Q1 and Q2. 

s1-> hai, today is a good day

s2-> No, today is a bad day

Here longest common substring is "today is a". So we have longest_substring_ratio = 3 / min(6,6) = 0.5 longest_substr_ratio = len(longest common substring) / (min(len(q1_tokens), len(q2_tokens))
"""

def get_token_features(q1, q2):
    token_features = [0.0]*10
    
    # Converting the Sentence into Tokens: 
    q1_tokens = q1.split()
    q2_tokens = q2.split()

    if len(q1_tokens) == 0 or len(q2_tokens) == 0:
        return token_features
    # Get the non-stopwords in Pull Requests
    q1_words = set([word for word in q1_tokens if word not in STOP_WORDS])
    q2_words = set([word for word in q2_tokens if word not in STOP_WORDS])
    
    #Get the stopwords in Pull Requests
    q1_stops = set([word for word in q1_tokens if word in STOP_WORDS])
    q2_stops = set([word for word in q2_tokens if word in STOP_WORDS])
    
    # Get the common non-stopwords from Pull Request pair
    common_word_count = len(q1_words.intersection(q2_words))
    
    # Get the common stopwords from Pull Request pair
    common_stop_count = len(q1_stops.intersection(q2_stops))
    
    # Get the common Tokens from Pull Request pair
    common_token_count = len(set(q1_tokens).intersection(set(q2_tokens)))
    
    SAFE_DIV = 0.0001 
    token_features[0] = common_word_count / (min(len(q1_words), len(q2_words)) + SAFE_DIV)
    token_features[1] = common_word_count / (max(len(q1_words), len(q2_words)) + SAFE_DIV)
    token_features[2] = common_stop_count / (min(len(q1_stops), len(q2_stops)) + SAFE_DIV)
    token_features[3] = common_stop_count / (max(len(q1_stops), len(q2_stops)) + SAFE_DIV)
    token_features[4] = common_token_count / (min(len(q1_tokens), len(q2_tokens)) + SAFE_DIV)
    token_features[5] = common_token_count / (max(len(q1_tokens), len(q2_tokens)) + SAFE_DIV)
    
    # Last word of both Pull Request is same or not
    token_features[6] = int(q1_tokens[-1] == q2_tokens[-1])
    
    # First word of both Pull Request is same or not
    token_features[7] = int(q1_tokens[0] == q2_tokens[0])
    
    token_features[8] = abs(len(q1_tokens) - len(q2_tokens))
    
    #Average Token Length of both Pull Requests
    token_features[9] = (len(q1_tokens) + len(q2_tokens))/2
    return token_features

# get the Longest Common sub string

def get_longest_substr_ratio(a, b):
    strs = list(distance.lcsubstrings(a, b))      # will return longest common substring 
    if len(strs) == 0:
        return 0
    else:
        return len(strs[0]) / (min(len(a), len(b)) + 1)

def extract_features(df):
    # To get the results in 4 decemal points
    
    # preprocessing each Pull Request
    df["Pull Request1"] = df["Pull Request1"].fillna("").apply(preprocess)
    df["Pull Request2"] = df["Pull Request2"].fillna("").apply(preprocess)

    print("token features...")
    
    # Merging Features with dataset
    
    token_features = df.apply(lambda x: get_token_features(x["Pull Request1"], x["Pull Request2"]), axis=1)
    
    df["cwc_min"]       = list(map(lambda x: x[0], token_features))
    df["cwc_max"]       = list(map(lambda x: x[1], token_features))
    df["csc_min"]       = list(map(lambda x: x[2], token_features))
    df["csc_max"]       = list(map(lambda x: x[3], token_features))
    df["ctc_min"]       = list(map(lambda x: x[4], token_features))
    df["ctc_max"]       = list(map(lambda x: x[5], token_features))
    df["last_word_eq"]  = list(map(lambda x: x[6], token_features))
    df["first_word_eq"] = list(map(lambda x: x[7], token_features))
    df["abs_len_diff"]  = list(map(lambda x: x[8], token_features))
    df["mean_len"]      = list(map(lambda x: x[9], token_features))
   
    #Computing Fuzzy Features and Merging with Dataset
    
    # do read this blog: http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/
    # https://stackoverflow.com/Pull Requests/31806695/when-to-use-which-fuzz-function-to-compare-2-strings
    # https://github.com/seatgeek/fuzzywuzzy
    print("fuzzy features..")

    df["token_set_ratio"]       = df.apply(lambda x: fuzz.token_set_ratio(x["Pull Request1"], x["Pull Request2"]), axis=1)
    # The token sort approach involves tokenizing the string in Pull Request, sorting the tokens alphabetically, and 
    # then joining them back into a string We then compare the transformed strings with a simple ratio().
    df["token_sort_ratio"]      = df.apply(lambda x: fuzz.token_sort_ratio(x["Pull Request1"], x["Pull Request2"]), axis=1)
    df["fuzz_ratio"]            = df.apply(lambda x: fuzz.QRatio(x["Pull Request1"], x["Pull Request2"]), axis=1)
    df["fuzz_partial_ratio"]    = df.apply(lambda x: fuzz.partial_ratio(x["Pull Request1"], x["Pull Request2"]), axis=1)
    df["longest_substr_ratio"]  = df.apply(lambda x: get_longest_substr_ratio(x["Pull Request1"], x["Pull Request2"]), axis=1)
    return df

df = extract_features(data)
df.to_csv(mount +"/MyDrive/W2VEC_PullRequest_1/data_with_preprocess_2.csv", index=False)

df = pd.read_csv(mount +"/MyDrive/W2VEC_PullRequest_1/data_with_preprocess_2.csv")
print(df.shape)
df.head(2)

"""# ***Plotting Word Clouds***

Plotting Word Clouds help us to undertand important words/features.
"""

df_duplicate = df[df['is_duplicate'] == 1]
df_nonduplicate = df[df['is_duplicate'] == 0]

sent_dup =np.dstack([df_duplicate['Pull Request1'].values,df_duplicate['Pull Request2'].values])
#words_dup = [word for sublist in sent_dup for word in sublist]
words_dup = sent_dup.flatten()
######
sent_ndup =np.dstack((df_nonduplicate['Pull Request1'].values,df_nonduplicate['Pull Request2'].values))
#words_ndup = [word for sublist in sent_ndup for word in sublist]
words_ndup = sent_ndup.flatten()

textp_w = words_dup
#open(path.join(d, 'train_p.txt')).read()
textn_w = words_ndup
#open(path.join(d, 'train_n.txt')).read()
stopwords = set(STOPWORDS)
print ("Total number of words in duplicate pair Pull Requests :",len(textp_w))
print ("Total number of words in non duplicate pair Pull Requests :",len(textn_w))


textn_w = [str(i) for i in textn_w]
textp_w = [str(i) for i in textp_w]
textp_w = ''.join(textp_w)
textn_w = ''.join(textn_w)

"""# ***Word cloud for duplicate pair of Pull Requests***"""

wc = WordCloud(background_color="white", max_words=len(textp_w), stopwords=stopwords)
wc.generate(textp_w)
print ("Word Cloud for Duplicate Pull Request pairs")
plt.figure(figsize=(16,8))
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
plt.show()

"""# ***Word cloud for non duplicate pair of Pull Requests***"""

wc = WordCloud(background_color="white", max_words=len(textn_w), stopwords=stopwords)
wc.generate(textn_w)
print ("Word Cloud for Non Duplicate Pull Request pairs")
plt.figure(figsize=(16,8))
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
plt.show()

"""# ***Pair plot of features ['ctc_min', 'cwc_min', 'csc_min' 'token_sort_ratio']***"""

sns.pairplot(df, hue='is_duplicate', vars=['ctc_min', 'cwc_min', 'csc_min', 'token_sort_ratio'])
plt.figure(figsize=(16,8))
plt.show()

"""# ***Analysis on absolute difference in length of Pull Requests***"""

plt.figure(figsize=(20, 10))
dist = df['abs_len_diff'][0:10000].values
dist.min()
plt.xlabel('Absolute difference in number of words')
sns.countplot(dist)
plt.show()

"""# ***TSNE Visualization***"""

from sklearn.preprocessing import MinMaxScaler

dfp_subsampled = df[0:5000]
X = MinMaxScaler().fit_transform(dfp_subsampled[['cwc_min', 'cwc_max', 'csc_min', 'csc_max' , 'ctc_min' , 'ctc_max' , 'last_word_eq', 'first_word_eq' , 'abs_len_diff' , 'mean_len' , 'token_set_ratio' , 'token_sort_ratio' ,  'fuzz_ratio' , 'fuzz_partial_ratio' , 'longest_substr_ratio']])
y = dfp_subsampled['is_duplicate'].values

tsne2d = TSNE(
    n_components=2,
    init='random', # pca
    random_state=101,
    method='barnes_hut',
    n_iter=1000,
    verbose=2,
    angle=0.5
).fit_transform(X)
#tsne result will appear as 2 columns.We have to plot it
# creating a new data frame which help us in ploting the tsne_result
tsne_new = np.vstack((tsne2d.T,dfp_subsampled['is_duplicate'])).T
df = pd.DataFrame(data=tsne_new, columns=("dimension1", "dimension2",
"is_duplicated"))
# Ploting the result
sns.FacetGrid(df, hue="is_duplicated", size=6).map(plt.scatter, 'dimension1',
'dimension2').add_legend()
plt.title("TSNE plot with perplexity 30 and max iter 1000")
plt.show()