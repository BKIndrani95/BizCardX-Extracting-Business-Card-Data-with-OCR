#---------*****---------------BIZCARDX: EXTRACTING BUSINESS CARD DATA WITH OCR--------------*****-----------------#

#-----IMPORT PACKAGES-------#
import pandas as pd
import numpy as np
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re
import mysql.connector
import pymysql
import base64

st.set_page_config(page_title="BIZCARDX: EXTRACTING DATA FROM BUSINESS CARD USING OCR",
                   layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("<h1 style='text-align: center; color: black;'>BIZCARDX: EXTRACTING BUSINESS CARD DATA WITH OCR</h1>",
            unsafe_allow_html=True)

selected = option_menu(None, ["ABSTRACT", "Upload & Extract", "Modify"],
                       icons=["house", "cloud-upload", "pencil-square"],
                       default_index=0,
                       orientation="vertical",
                       styles={"nav-link": {"font-size": "22px", "text-align": "centre", "margin": "-2px",
                                            "--hover-color": "#6495ED"},
                               "icon": {"font-size": "22px"},
                               "container": {"max-width": "2000px"},
                               "nav-link-selected": {"background-color": "#6495ED"}})
reader = easyocr.Reader(['en'])

#------------CONNECTING WITH MYSQL DATABASE
mydb = mysql.connector.connect( host="localhost",
                                user="root",
                                password="Indranibk95@",
                                database="bizcardx",
                                charset='utf8mb4')
cursor = mydb.cursor()
mydb.commit()

#----------TABLE CREATION
cursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                   (company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image LONGBLOB)''')
mydb.commit()

#-----------------Project
if selected == "ABSTRACT":
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Technologies Used :** Python, MYSQL, easy OCR, Streamlit, Pandas")
    with col2:
        st.write("**About :** This Project aims to extract information from business cards.")
        st.write(
            ' The main purpose of this project is to automate the process of extracting details from business card(Visiting Card) images using Optical Character Recognition (OCR). This project can able to extract text from the images.')

#----------------UPLOAD AND EXTRACT MENU
if selected == "Upload & Extract":
    st.subheader(":Orange[Upload a Business Card Image]")
    uploaded_card = st.file_uploader("upload here", label_visibility="collapsed", type=["png", "jpeg", "jpg"])
    if uploaded_card is not None:
        uploaded_image_data = uploaded_card.getvalue()
        binary_image_data = np.asarray(bytearray(uploaded_image_data), dtype=np.uint8)
        encoded_image_data = base64.b64encode(binary_image_data)

#------------EXTRACTING CARD DETAILS
        def save_card(uploaded_card):
            uploaded_cards_dir = os.path.join(os.getcwd(), "uploaded_cards")
            # Create the directory if it doesn't exist
            os.makedirs(uploaded_cards_dir, exist_ok=True)
            with open(os.path.join(uploaded_cards_dir, uploaded_card.name), "wb") as f:
                f.write(uploaded_card.getbuffer())
        save_card(uploaded_card)

        def image_preview(image, res):
            for (bbox, text, prob) in res:
                # unpack the bounding box
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15, 15)
            plt.axis('off')
            plt.imshow(image)

        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown("You have uploaded the card")
            st.image(uploaded_card)
        with col2:
            with st.spinner("BIZCARD <---> OCR"):
                st.set_option('deprecation.showPyplotGlobalUse', False)
                saved_img = os.getcwd() + "\\" + "uploaded_cards" + "\\" + uploaded_card.name
                image = cv2.imread(saved_img)
                res = reader.readtext(saved_img)
                st.markdown("Image Processed and Data Extracted")
                st.pyplot(image_preview(image, res))

        saved_img = os.path.join(os.getcwd(),"uploaded_cards",uploaded_card.name)
        result = reader.readtext(saved_img, detail=0, paragraph=False)

        def img_to_binary(saved_img):
            with open(saved_img, 'rb') as file:
                binary_data = file.read()
            return binary_data

        binary_image_data = img_to_binary(saved_img)

        data = {"company_name": [],
                "card_holder": [],
                "designation": [],
                "mobile_number": [],
                "email": [],
                "website": [],
                "area": [],
                "city": [],
                "state": [],
                "pin_code": [],
                "image": encoded_image_data
                }
#--------------Fetching Data from Image
        def get_data(res):
            for ind, i in enumerate(res):
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)

                elif "WWW" in i:
                    data["website"] = res[4] + "." + res[5]

                elif "@" in i:
                    data["email"].append(i)

                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) == 2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])

                elif ind == len(res) - 1:
                    data["company_name"].append(i)

                elif ind == 0:
                    data["card_holder"].append(i)

                elif ind == 1:
                    data["designation"].append(i)

                if re.findall('^[0-9].+, [a-zA-Z]+', i):
                    data["area"].append(i.split(',')[0])

                elif re.findall('[0-9] [a-zA-Z]+', i):
                    data["area"].append(i)

                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*', i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
                if state_match:
                    data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
                    data["state"].append(i.split()[-1])
                if len(data["state"]) == 2:
                    data["state"].pop(0)

                if len(i) >= 6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]', i):
                    data["pin_code"].append(i[10:])
        get_data(result)
        company_name = data["company_name"]

        def create_df(data):
            df = pd.DataFrame(data)
            return df

        df = create_df(data)
        st.success("Data Extraction Done :)")
        st.write(df)
        if st.button("Upload to Database"):
            for i, row in df.iterrows():
               card_holder = row['card_holder']
               cursor.execute("SELECT * FROM card_data WHERE card_holder = %s",(card_holder,))
               existing_data = cursor.fetchone()
               if existing_data:
                   st.error("Data Already Exist in Database!")
               else:
                   sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                   cursor.execute(sql, (row["company_name"],card_holder, row["designation"], row["mobile_number"], row["email"], row["website"], row["area"], row["city"], row["state"], row["pin_code"], encoded_image_data))
                   mydb.commit()
                   st.success("Uploaded to database successfully :)")
#-----------View Updated Database
        if st.button(":yellow[View updated data]"):
            cursor.execute(
                "SELECT company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code FROM card_data")
            updated_df = pd.DataFrame(cursor.fetchall(),
                                      columns=["company_name", "card_holder", "designation", "mobile_number",
                                               "email",
                                               "website", "area", "city", "state", "pin_code"])
            st.write(updated_df)

#-----------------Modify Existing Data
if selected == "Modify":
    select = option_menu(None,
                         options=["ALTER", "DELETE"],
                         default_index=0,
                         orientation="vertical",
                         styles={"container": {"width": "100%"},
                                 "nav-link": {"font-size": "18px", "text-align": "center", "margin": "-2px"},
                                 "nav-link-selected": {"background-color": "#6495ED"}})

#-----------------Alter Existing data in Database
    if select == "ALTER":
        st.markdown(":violet[Alter Data]")
        try:
            cursor.execute("SELECT card_holder FROM card_data")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            options = ["None"] + list(business_cards.keys())
            selected_card = st.selectbox("**Select a card**", options)
            if selected_card == "None":
                st.write("No card selected.")
            else:
                st.markdown("Update or modify any data below")
                cursor.execute(
                    "SELECT company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder = %s",
                    (selected_card,))
                result = cursor.fetchone()
                if result:
                    company_name = st.text_input("company_name", result[0])
                    card_holder = st.text_input("card_holder", result[1])
                    designation = st.text_input("designation", result[2])
                    mobile_number = st.text_input("mobile_number", result[3])
                    email = st.text_input("Email", result[4])
                    website = st.text_input("Website", result[5])
                    area = st.text_input("Area", result[6])
                    city = st.text_input("City", result[7])
                    state = st.text_input("State", result[8])
                    pin_code = st.text_input("pin_code", result[9])
                    cursor.fetchall()

                    if st.button(":violet[Commit changes to DB]"):
                        cursor.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                        WHERE card_holder=%s""", (company_name,card_holder, designation, mobile_number, email, website, area, city, state, pin_code, selected_card))
                        mydb.commit()
                        st.success("Information updated in database successfully.")
                else:
                    st.warning("No data found for the selected card")

            if st.button(":blue[View updated data]"):
                cursor.execute(
                    "SELECT company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code FROM card_data")
                updated_df = pd.DataFrame(cursor.fetchall(),
                                          columns=["Company_Name", "Card_Holder", "Designation", "mobile_number",
                                                   "Email", "Website", "Area", "City", "State", "Pin_Code"])
                st.write(updated_df)
        except Exception as e:
            st.error(f"Error: {e}")

#--------------Delete Data from Database
    if select == "DELETE":
        st.subheader(":red[Delete the data]")
        try:
            cursor.execute("SELECT card_holder FROM card_data")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            options = ["None"] + list(business_cards.keys())
            selected_card = st.selectbox("**Select a card**", options)
            if selected_card == "None":
                st.write("No card selected.")
            else:
                st.write(f" You have selected :red[**{selected_card}'s**] card to delete")
                st.write("Proceed to delete this card?")
                if st.button("Yes Delete Business Card"):
                    cursor.execute(f"DELETE FROM card_data WHERE card_holder ='{selected_card}'")
                    mydb.commit()
                    st.success("Business card information deleted from database.")

            if st.button(":green[View updated data]"):
                cursor.execute(
                    "SELECT company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code FROM card_data")
                updated_df = pd.DataFrame(cursor.fetchall(),
                                          columns=["Company_Name", "Card_Holder", "Designation", "mobile_number",
                                                   "Email",
                                                   "Website", "Area", "City", "State", "Pin_Code"])
                st.write(updated_df)

        except Exception as e:
            st.error(f"Error: {e}")

#************************************************************************************************************************************************************************************************-:)
