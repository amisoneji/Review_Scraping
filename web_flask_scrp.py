from flask import Flask, render_template, request,jsonify
# from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo

app = Flask(__name__)  # initialising the flask app with the name 'app'




@app.route('/',methods=['POST','GET']) # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':  #request hit API
        serchstring = request.form['content'].replace(" ", "")  #it returns the content enter  in html page (string)
        try:
            dbconn = pymongo.MongoClient("mongodb://localhost:27017/") #opening mongodb connection
            db = dbconn["reviews_db"] #creating &connecting DB reviews_db
            reviews = db[serchstring].find({}) #if sewrch string reviews table alrady exist with reviews return that & show it to user
            if reviews.count() > 0:
                return render_template("results.html", reviews=reviews)
            else:

                flipkart_url = "https://www.flipkart.com/search?q=" + serchstring #url for serching product
                uClient = uReq(flipkart_url)   # requesting the webpage from the internet
                flipkart_page = uClient.read() # reading the webpage
                uClient.close() # closing the connection to the web serve

                flipkart_html = bs(flipkart_page, "html.parser") #the web page is in bytes(binary) so parsing it to html page
                all_product = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"}) # seacrhing for appropriate tag to redirect to the product link
                # we have a list of all product for same serch string assuming third product user want reviews
                del all_product[0:3] #droping first three products
                product = all_product[0] #product for review
                product_link = "https://www.flipkart.com" + product.div.div.div.a['href'] # extracting the actual product link

                product_result = requests.get(product_link) # getting the product page from server
                product_html = bs(product_result.text, "html.parser") # parsing the product page as HTML
                CommentBoxes = product_html.find_all("div", {"class": "_16PBlm"}) # finding the HTML section containing the customer comments

                table = db[serchstring] #creating table wuth same name user entered as a serch string

                reviews = [] #creating empty list for appending all reviews

                #  iterating over the comment section to get the details of customer and their comments
                for commentbox in CommentBoxes:
                    try:
                        name = commentbox.div.div.find_all("p", {"_2sc7ZR _2V5EHH"})[0].text #fetching commenter  name
                    except:
                        name = "No Name"

                    try:
                        rating = commentbox.div.div.div.div.text #fetching commenter  rating
                    except:
                        rating = "No Rating"

                    try:
                        comment_header = commentbox.div.div.div.p.text #fetching comment header
                    except:
                        comment_header = "No comment Headeing available"

                    try:
                        comment_tag = commentbox.div.div.find_all('div', {'class': ''}) #fetching review
                        cust_comment = comment_tag[0].div.text
                    except:
                        cust_comment = "No comments from customer"

                    my_dict = {"Product": serchstring, "Name": name, "Rating": rating, "CommentHead": comment_header,
                           "Comment": cust_comment} #converig all data with dictionary
                    X= table.insert_one(my_dict)#adding that oner person whole comment data to database
                    reviews.append(my_dict) #  appending the comments to the review list
                return render_template('results.html', reviews=reviews) # showing the review to the user

        except:
            return "Something Wrong"

    else:
        return render_template("index.html")

if __name__ == '__main__':

    app.run(port=5000,debug=True) # running the app on the local machine on port 5000


