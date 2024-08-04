
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


# example/st_app.py

conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet="Products")
orders_existing_data = conn.read(worksheet="Orders")


#st.dataframe(orders_existing_data)
#st.dataframe(data)



#Creating a form
st.subheader("User information")

name = st.text_input("Name", max_chars=50)
surname = st.text_input("Surname", max_chars=50)
email = st.text_input("Email", max_chars=50)
emp_number = st.text_input("Employee Number", max_chars=10)

st.subheader("Select Product")

selected_product = st.selectbox(
    "Available Products",
    (data["Description"]),
)


qty = f"""SELECT "Qty" FROM Products WHERE Description = '{selected_product}'"""
price = f"""SELECT "Price" FROM Products WHERE Description = '{selected_product}'"""


qty_df = conn.query(sql=qty, ttl=3600)
price = conn.query(sql=price, ttl=3600)


selected_qty = st.number_input("Select Quantity", min_value=1, max_value=int(qty_df["Qty"]))

total_price = float(price["Price"]) * selected_qty


st.write(selected_product)
st.text("Total Qty Available: " + int(qty_df["Qty"]).__str__())
st.text("Total Price: R " + str(total_price))


submit = st.button("Place Order")


if submit:

    if not name:
        st.warning("Please input your name!!! :pleading_face:")
        st.stop()
    if not surname:
        st.warning("Please input your surname!!! :pleading_face:")
        st.stop()
    if not email:
        st.warning("Please input your email!!! :pleading_face:")
        st.stop()
    if not emp_number:
        st.warning("Please input your employee number!!! :pleading_face:")
        st.stop()

    st.cache_data.clear()

    orders_data = pd.DataFrame(
        [
            {
                "EmpNumber": emp_number,
                "Name": name,
                "Surname": surname,
                "Email": email,
                "Product": selected_product,
                "OrderQty": str(selected_qty),
                "TotalPrice": str(total_price)
            }
        ]
    )

    updated_orders_data = pd.concat([orders_existing_data, orders_data], ignore_index=True)

    #Updating Google Sheet with new data
    conn.update(worksheet="Orders", data=updated_orders_data)

    st.success("Order placed successful :clap:")