from flask import Response
from flask import Flask, jsonify, request,redirect
from flask_restful import Resource, Api
from flask_cors import CORS
#Imports
import string
import requests
import json
import random
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import PunktSentenceTokenizer
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import smtplib
import nltk.classify
from sklearn.svm import LinearSVC
import requests
import random
import string
from functools import wraps
import time
from Database import Database
import boto3
import os
now = datetime.now().date()
app=Flask(__name__)
CORS(app)
api=Api(app)
from decouple import config
#NLTK Downloads (Need to do only once)
nltk.download('punkt') 
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet') 
nltk.download('nps_chat')

#Global Constants
GREETING_INPUTS    = ("hello", "hi")
GREETING_RESPONSES = ["hi", "hey", "*nods*", "hi there", "Talkin' to me?"]
FILENAME           = "datasets.txt"
#Global Variables
lem = nltk.stem.WordNetLemmatizer()
remove_punctuation = dict((ord(punct), None) for punct in string.punctuation)

#Functions
'''
fetch_features transforms a chat into a classifier friendly format
'''
def fetch_features(chat):
    features = {}
    for word in nltk.word_tokenize(chat):
        features['contains({})'.format(word.lower())] = True
    return features
'''
lemmatise performs lemmatization on words
'''
def lemmatise(tokens):
    return [lem.lemmatize(token) for token in tokens]
  
'''
tokenise tokenizes the words
'''
def tokenise(text):
    return lemmatise(nltk.word_tokenize(text.lower().translate(remove_punctuation)))

'''
Standard greeting responses that the bot can recognize and respond with
'''
def greet(sentence):
    for word in sentence.split():
        if word.lower() in GREETING_INPUTS:
            return random.choice(GREETING_RESPONSES)
'''
match matches a user input to the existing set of questions
'''


def match(user_response):
    resp      =''
    q_list.append(user_response)
    TfidfVec  = TfidfVectorizer(tokenizer=tokenise, stop_words='english')
    tfidf     = TfidfVec.fit_transform(q_list)
    print(user_response)
    vals      = cosine_similarity(tfidf[-1], tfidf)
    print(vals)
    idx       = vals.argsort()[0][-2]
    flat      = vals.flatten()
    flat.sort()
    req_tfidf = flat[-2]
    
    if(req_tfidf==0):
        resp = resp+"not recognize"
        return resp
    else:
        resp_ids = qa_dict[idx]
        resp_str = ''
        s_id = resp_ids[0]
        end = resp_ids[1]
        while s_id<end :
            resp_str = resp_str + " " + sent_tokens[s_id]
            s_id+=1
        resp = resp+resp_str
        return resp


#Training the classifier
chats = nltk.corpus.nps_chat.xml_posts()[:10000]
featuresets = [(fetch_features(chat.text), chat.get('class')) for chat in chats]
size = int(len(featuresets) * 0.1)
train_set, test_set = featuresets[size:], featuresets[:size]
classifier = nltk.classify.SklearnClassifier(LinearSVC())
classifier.train(train_set)
# classifier = nltk.NaiveBayesClassifier.train(train_set) #If you need to test Naive Bayes as well
# print(nltk.classify.accuracy(classifier, test_set))

# #Question Bank Creation
ques_bank   = open(FILENAME,'r',errors = 'ignore')
qb_text     = ques_bank.read()
qb_text     = qb_text.lower()
sent_tokens = nltk.sent_tokenize(qb_text)# converts to list of sentences 
word_tokens = nltk.word_tokenize(qb_text)# converts to list of words
print(sent_tokens)
qa_dict     = {} #The Dictionary to store questions and corresponding answers
q_list      = [] #List of all questions
s_count     = 0  #Sentence counter

#Extract questions and answers
#Answer is all the content between 2 questions [assumption]
while s_count < len(sent_tokens):
    result = classifier.classify(fetch_features(sent_tokens[s_count]))
    # print(fetch_features(sent_tokens[s_count]))
    if("question" in result.lower()):
        next_question_id = s_count+1
        next_question = classifier.classify(fetch_features(sent_tokens[next_question_id]))
        while(not("question" in next_question.lower()) and next_question_id < len(sent_tokens)-1):
            next_question_id+=1
            next_question = classifier.classify(fetch_features(sent_tokens[next_question_id]))
        q_list.append(sent_tokens[s_count])
        
        end = next_question_id
        if(next_question_id-s_count > 5):
            end = s_count+5
        qa_dict.update({len(q_list)-1:[s_count+1,end]})
        s_count = next_question_id
    else:
        s_count+=1
        
#Response Fetching
class Classifier(Resource):
    def post(self): #method.
        res = request.get_json()
        value = res.get('value')
        value = value.split("\n")
        print(value)
        for x in value:
            print(x)
            u_input = x
            u_input = u_input.lower()
            if(u_input!='ciao'):
                predict = match(u_input).strip().capitalize()
                q_list.remove(u_input)
                if(predict.replace('.','')=='Medication'):
                    return {"data":predict.replace('.','')}
                if(predict.replace('.','')=='Education'):
                    return {"data":predict.replace('.','')}
                if(predict.replace('.','')=='Food'):
                    print("food")
                    return {"data":predict.replace('.','')}
                if(predict.replace('.','')=='Utilities'):
                    return {"data":predict.replace('.','')}
                if(predict.replace('.','')=='Transportation'):
                    return {"data":predict.replace('.','')}
                if(predict.replace('.','')=='Groceries'):
                    return {"data":predict.replace('.','')}

        return {"data":"Others"}

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class Usermanagement(Resource):
    def __init__(self):
        self.db=Database()

    def post(self,pk=None):
        data = request.get_json()
        try:
            self.db.insert(f"INSERT INTO users(email,password) values('{data.get('email')}','{data.get('password')}')")
            return {"status":"success"}
        except Exception as e:
            print(e)
            return {"status":"Failed Input"}

    def get(self,pk=None):
        if pk==None:
            res = self.db.query('SELECT * FROM users')
        else:
            res = self.db.query(f'SELECT * FROM users where id={pk}')
        return {"data":res}

    def delete(self,pk):
        try:
            self.db.insert(f'DELETE FROM users where id={pk}')
            return {"data":"success"}
        except:
            return {"status":"Failed"}
    
    def put(self,pk=None):
        data = request.get_json()
        print(data)
        try:
            isValid = self.db.query(f"select * from users where email='{data.get('email')}' and id={data.get('id')}")
            if(len(isValid)==0):
                data_fetch = self.db.query(f"select * from users where email='{data.get('email')}'")
                if(len(data_fetch)>0):
                    return {"status":"Failed Input"}
            if(data.get('password')=='' or data.get('password')==None):
                self.db.insert(f"UPDATE users set email='{data.get('email')}' where id={pk}")
            else:
                self.db.insert(f"UPDATE users set email='{data.get('email')}',password='{data.get('password')}' where id={pk}")
            print("saved")
            return {"status":"Success"}
        except Exception as e:
            print(e)
            return {"status":"Failed"}

class Categories(Resource):
    def __init__(self):
        self.db=Database()
        self.listitem=[]
    def get(self,category=None,pk=None):
        print(category)
        print(pk)
        try:
            res = self.db.query(f"select * from receipt where categories='{category}' and user_id='{pk}' ORDER BY -id ")
            if(res==[]):
                print("okay")
                return None
            else:
                print(res)
                listitem=[{"id":i[0],"vendor_name":i[2],"created_date":i[3],"category":i[4],
                "image":f"https://cashtosspublic.s3.us-east-2.amazonaws.com/{i[5]}","total":i[6]} for i in res]
                print(listitem)
                return listitem
        except Exception as e:
            print(e)
            return {"status":f"{e}"}


class ResetPassword(Resource):
    def __init__(self):
        self.db=Database()
        
    def post(self):
        res = request.get_json()
        pw = id_generator()
        print(res)
        isValid = self.db.query(f"select * from users where email='{res.get('email')}' ")
        if(len(isValid) > 0):
            self.db.insert(f"UPDATE users set password='{pw}' where email='{res.get('email')}' ")
            msg = MIMEMultipart()
            msg.add_header('Content-Type', 'text/html')
            msg['To'] = str(res.get('email'))
            msg['Subject'] = "Reset password from Cashtoss App"
            part1=MIMEText("""\
                <html>
                    <body>
                        Here's your new password : """+pw+"""
                    </body>
                </html>
                
                """,'html')

            msg.attach(part1)
            server = smtplib.SMTP('smtp.gmail.com: 587')
            server.starttls()
            server.login('Cashtoss8@gmail.com', "Cashtoss2021!")
            # send the message via the server.
            server.sendmail('Cashtoss8@gmail.com', msg['To'], msg.as_string())
            server.quit()
            print("successfully sent email to %s:" % (msg['To']))
            return {"status":"success"}
        else:
            print("invalid")
            return {"status":"invalid"}



class EmailVerification(Resource):
    def __init__(self):
        self.db=Database()
        
    def post(self):
        res = request.get_json()
        msg = MIMEMultipart()
        msg.add_header('Content-Type', 'text/html')
        msg['To'] = str(res.get('email'))
        msg['Subject'] = "Verification for Cashtoss App"
        part1=MIMEText("""\
            <html><body>Please verify your email <a href='http://3.144.76.35:5000/api/v1/verified'>Verify</a></body></html>
            
            """,'html')
        msg.attach(part1)
        server = smtplib.SMTP('smtp.gmail.com: 587')
        server.starttls()
        server.login('Cashtoss8@gmail.com', "Cashtoss2021!")
        # send the message via the server.
        server.sendmail('Cashtoss8@gmail.com', msg['To'], msg.as_string())
        server.quit()   
        print("successfully sent email to %s:" % (msg['To']))
        return {"status":"success"}



class Receipt(Resource):
    def __init__(self):
        self.db=Database()
    def delete(self,pk):
        self.db.insert(f"delete from receipt where user_id={pk} ")
        print(pk)
        self.db.insert(f"update users set totalamount=0 where id={pk}")
        return {}
    def put(self,pk):
        self.db.insert(f"delete from receipt where id={pk} ")
        return {}

    def get(self,pk=None):
        item={"total":0.0,"Medication":0.0,"Groceries":0.0,"Others":0.0,"Food":0.0,"Transportation":0.0,"Education":0.0,"Utilities":0.0}
        query = self.db.query(f"SELECT categories,sum(total) FROM receipt where user_id = '{pk}' group by categories ")
        total = self.db.query(f"SELECT SUM(total) FROM receipt where user_id='{pk}'")
        # item =  [{f"{x[0]}":float(x[1]) for x in query}]
        for x in query:
            if(x[0]=='Medication'):
                item['Medication']=float(x[1])
            elif(x[0]=='Others'):
                item['Others']=float(x[1])
            elif(x[0]=='Food'):
                item['Food']=float(x[1])
            elif(x[0]=='Education'):
                item['Education']=float(x[1])
            elif(x[0]=='Utilities'):
                item['Utilities']=float(x[1])
            elif(x[0]=='Groceries'):
                item['Groceries']=float(x[1])
            elif(x[0]=='Transportation'):
                item['Transportation']=float(x[1])
        item['total']=total[0][0]
        return item
        
    def post(self,pk=None):
        data = request.get_json()
        id = self.db.query("select max(id)+1 from receipt")
        if(id[0][0]==None):
            id=0
        else:
            id=id[0][0]
        try:
            res = self.db.insert(f"INSERT INTO receipt values({id},'{data.get('id')}','{data.get('vendor_name')}','{data.get('date')}','{data.get('category_name')}','{data.get('image')}',{float(data.get('total'))})")
            if(res==[]):
                print(res)
                return Response({"status":"Wrong Credentials"},status=404)
            else:
                result_data = self.db.query(f"SELECT SUM(total) FROM receipt where user_id = '{data.get('id')}'")
                result_settings = self.db.query(f"SELECT totalAmount from users where id = {data.get('id')}")
                id = self.db.query(f"select max(id) from receipt")
                print(result_settings[0][0])
                if(int(result_data[0][0])>=(result_settings[0][0])):     
                    print(result_settings[0][0])    
                    return {"status":"exceed","id":id[0][0]}
                else:
                    return {"status":"less","id":id[0][0]}
                
        except Exception as e:
            print(e)
            return {"status":f"{e}"}



class Login(Resource):
    def __init__(self):
        self.db=Database()

    def post(self,pk=None):
        data = request.get_json()
        print(data)
        try:
            res = self.db.query(f"SELECT * FROM users where email='{data.get('email')}' and password='{data.get('password')}'")
            if(res==[]):
                print(res)
                return {"status":400}
            else:
                print(res[0][0])
                return {"id":res[0][0],"email":res[0][1],"password":res[0][2],"status":201}
            
        except Exception as e:
            print(e)
            return {"status":"Failed Input"}


class Threshold(Resource):
    def __init__(self):
        self.db=Database()

    def get(self,pk=None):
        print("okay")
        try:
            result_settings = self.db.query(f"SELECT totalAmount from users where id={pk} ")
            total = self.db.query(f"SELECT SUM(total) FROM receipt where user_id='{pk}'")
            if result_settings[0][0]==0:
                return {'status':False}
            elif((total[0][0]/result_settings[0][0]*100)>float(80)):
                return {'status':True}
            else:
                return {'status':False}
            # if(res==[]):
            #     print(res)
            #     return {"status":True}
            # else:
            #     print(res[0][0])
            #     return {"id":res[0][0],"email":res[0][1],"password":res[0][2],"status":201}
            
        except Exception as e:
            print(e)
            return {"status":False}

class Register(Resource):
    def __init__(self):
        self.db=Database()

    def post(self,pk=None):
        data = request.get_json()
        print(data)
        data_fetch = self.db.query(f"select * from users where email='{data.get('email')}'")
        
        if(len(data_fetch)>0):
            print(data_fetch)
            return {"status":"Failed Input"}
        try:
            id = self.db.query("select max(id)+1 from users")
            res = self.db.insert(f"INSERT INTO users values({id[0][0]},'{data.get('email')}','{data.get('password')}')")
            msg = MIMEMultipart()
            msg.add_header('Content-Type', 'text/html')
            msg['To'] = str(data.get('email'))
            msg['Subject'] = "Cashtoss Registration Successful"
            part1=MIMEText("""\
                <html>
                    <body>
                        <div>
                        Welcome to Cashtoss!</div>
                        <div>
                        Hope this expense tracker application address your budget monitoring needs.
                        </div>
                        <div>
                        Sincerly,
                        </div>
                        <div>
                        Cashtoss
                        </div>
                    </body>
                </html>
                
                """,'html')

            msg.attach(part1)
            server = smtplib.SMTP('smtp.gmail.com: 587')
            server.starttls()
            server.login('Cashtoss8@gmail.com', "Cashtoss2021!")
            # send the message via the server.
            server.sendmail('Cashtoss8@gmail.com', msg['To'], msg.as_string())
            server.quit()
            return Response({"status":"Success"},status=201)
            
        except Exception as e:
            print(e)
            return {"status":"Failed Input"}


class Verified(Resource):
    def get(self,pk=None):
        return {"status":"verified"}


class Receipts(Resource):
    def __init__(self):
        self.db=Database()

    def get(self,pk=None):
        result_settings = self.db.query(f"SELECT * from receipt where user_id={pk} ")
        print(result_settings)
        return result_settings


class Settings(Resource):
    def __init__(self):
        self.db=Database()

    def get(self,pk=None):
        result_settings = self.db.query(f"SELECT totalAmount from users where id={pk} ")
        return result_settings[0][0]

    def post(self,pk):
        res = request.get_json()
        print(res)
        try:
            self.db.query(f"UPDATE users set totalAmount={res.get('totalAmount')} where id={pk}")
            return {}
        except Exception as e:
            print(e)
            return {}


class Payment(Resource):
    def __init__(self):
        self.db=Database()

    def get(self,pk=None):
        url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"

        payload='grant_type=client_credentials'
        headers = {'Authorization': 'Basic QWZoa1BDVUZubXlvZnV3TjNPU2ljTzdaODNnS29YbERVbWJhN21laDNHZXd2QjZlQzFuUTc0SnJNQ1NBTnBZeVV1ZHlqRXZaQm9kYS01cS06RUZtREUweVdxcW95VE42THVMZ0Y3V24wajJpWkdxOGdTa1NPR3phTmxmSEtaeTJ1cGwyRmticmlGbGdrNTVfU0dtRlN2SVZnbVZmOWNYZGs=','Content-Type':'application/x-www-form-urlencoded','Cookie':'cookie_prefs=P%3D1%2CF%3D1%2Ctype%3Dimplicit; enforce_policy=ccpa; ts=vreXpYrS%3D1734306076%26vteXpYrS%3D1639637099%26vt%3Dc1e12b5717dac1200018c0cefffffb00%26vr%3Dc1e12b5717dac1200018c0cefffffaff; ts_c=vr%3Dc1e12b5717dac1200018c0cefffffaff%26vt%3Dc1e12b5717dac1200018c0cefffffb00'}
        response = requests.request("POST", url, headers=headers, data=payload)
        x = json.loads(response.text)
        paymentId=request.args.get('paymentId')
        PayerID=request.args.get('PayerID')
        url = f"https://api.sandbox.paypal.com/v1/payments/payment/{paymentId}/execute"
        payload = json.dumps({
        "payer_id": PayerID
        })
        headers = {"Authorization": f"Bearer {x['access_token']}","Content-Type": "application/json","Cookie": "cookie_prefs=P%3D1%2CF%3D1%2Ctype%3Dimplicit; enforce_policy=ccpa; ts=vreXpYrS%3D1734306076%26vteXpYrS%3D1639637099%26vt%3Dc1e12b5717dac1200018c0cefffffb00%26vr%3Dc1e12b5717dac1200018c0cefffffaff; ts_c=vr%3Dc1e12b5717dac1200018c0cefffffaff%26vt%3Dc1e12b5717dac1200018c0cefffffb00; tsrce=devdiscoverynodeweb"}
        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text)
        return {"status":response.text}

def toDict(res):
    s = string.replace("{" ,"")
    finalstring = s.replace("}" , "")

    #Splitting the string based on , we get key value pairs
    list = finalstring.split(",")

    dictionary ={}
    for i in list:
        #Get Key Value pairs separately to store in dictionary
        keyvalue = i.split(":")

        #Replacing the single quotes in the leading.
        m= keyvalue[0].strip('\'')
        m = m.replace("\"", "")
        dictionary[m] = keyvalue[1].strip('"\'')
    return dictionary

class Upload(Resource):
    def __init__(self):
        self.db=Database()

    def post(self,pk=None):
        imageFile=request.files['image']
        file_path=os.path.join('', imageFile.filename) # path where file can be saved
        imageFile.save(file_path)
        client = boto3.client('s3',aws_access_key_id=config("AWS_ACCESS_ID"),aws_secret_access_key=config("AWS_SECRET_ID"))
        client.upload_file(f'{imageFile.filename}','cashtosspublic',f'{imageFile.filename}')
        self.db.insert(f"UPDATE receipt set image='{imageFile.filename}' where id={pk} ")
        return {"status":"Successful"}

api.add_resource(Usermanagement,'/api/v1/users/<int:pk>')
api.add_resource(Login,'/api/v1/login')
api.add_resource(Register,'/api/v1/register')
api.add_resource(Classifier,'/api/v1/chat')
api.add_resource(ResetPassword,'/api/v1/reset_password')
api.add_resource(EmailVerification,'/api/v1/verification')
api.add_resource(Receipt,'/api/v1/receipt/<int:pk>')
api.add_resource(Receipts,'/api/v1/receipts/<int:pk>')
api.add_resource(Settings,'/api/v1/settings/<int:pk>')
api.add_resource(Threshold,'/api/v1/threshold/<int:pk>')
api.add_resource(Upload,'/api/v1/upload/<int:pk>')
api.add_resource(Payment,'/api/v1/payment')
api.add_resource(Verified,'/api/v1/verified')
# api.add_resource(UploadTest,'/api/v1/uploadtest')
api.add_resource(Categories,'/api/v1/categories/<string:category>/<int:pk>')
if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=config("PORT"))