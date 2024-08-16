
from datetime import datetime
import time
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import re

#Checking If Email is Valid using RegEx
def check(email_str):
    pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if re.match(pat,email_str):
        return True
    else:
        return False


#setting up the page
st.set_page_config(page_title="Warehouse Stock Sale")
st.title("Warehouse Stock Sale")

conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet="Products")
orders_existing_data = conn.read(worksheet="Orders")

dt = data["Description"] + data["Price"].astype(str)

#st.dataframe(orders_existing_data)
#st.dataframe(data)

#Creating a form
st.subheader("User information")

name = st.text_input("Name & Surname", max_chars=80)
email = st.text_input("Email", max_chars=50, placeholder="someone@gmail.com")

emp_number = st.text_input("Employee Number", max_chars=10)

st.subheader("Select Product")

selected_product = st.selectbox(
    "Available Products",
    (
        data["Description"] + " - R " + round((data["Price"] * 1.15), 2).astype(str)
    ),
)

selected_prod_str = str(selected_product).split(" - R ")

#st.write(selected_prod_str)

qty = f"""SELECT "AvailableQty" FROM Products WHERE Description = '{selected_prod_str[0]}'"""
price = f"""SELECT "Price" FROM Products WHERE Description = '{selected_prod_str[0]}'"""


qty_df = conn.query(sql=qty, ttl=3600)
price = conn.query(sql=price, ttl=3600)


selected_qty = st.number_input("Select Quantity", min_value=0, max_value=int(qty_df["AvailableQty"]))

total_price = round((float(price["Price"]) * selected_qty) * 1.15, 2)

if (int(qty_df["AvailableQty"] > 0)):
    st.write(selected_product)
    st.text("Total Qty Available: " + int(qty_df["AvailableQty"]).__str__())
    st.text("Total Price: R " + str(total_price) + " (Incl VAT)")
else:
    st.write(selected_product)
    st.markdown("**Product not available**")

#new_qty = (int(qty_df["Qty"])-selected_qty)
#st.write(new_qty)
#st.write()

submit = st.button("Place Order")

if submit:

    if not name:
        st.warning("Please input your name!!! :pleading_face:")
        st.stop()
    if not email:
        st.warning("Please input your email!!! :pleading_face:")
        st.stop()
    if not emp_number:
        st.warning("Please input your employee number!!! :pleading_face:")
        st.stop()
    if (int(qty_df["AvailableQty"] <= 0)):
        st.warning("Product not available:disappointed:")
        st.stop()
    if(not check(email)):
       st.warning("Please enter correct email address")
       st.stop()

    st.cache_data.clear()

    orders_data = pd.DataFrame(
        [
            {
                "EmpNumber": emp_number,
                "Name": name,
                "Email": email,
                "OrderDate": datetime.today().strftime('%Y-%m-%d'),
                "OrderTime": time.strftime("%H:%M:%S", time.localtime()),
                "Product": selected_prod_str[0],
                "OrderQty": str(selected_qty),
                "TotalPrice": str(total_price)
            }
        ]
    )

    updated_orders_data = pd.concat([orders_existing_data, orders_data], ignore_index=True)

    #Updating Google Sheet with new data
    conn.update(worksheet="Orders", data=updated_orders_data)

    st.success("Order placed successful :clap:")