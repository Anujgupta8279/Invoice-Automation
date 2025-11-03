import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
import os
from datetime import datetime

# ---------- Load or Create Data ----------
if os.path.exists("customers.csv"):
    customers = pd.read_csv("customers.csv")
else:
    customers = pd.DataFrame(columns=["customer_id", "customer_name", "address", "mobile", "email"])

if os.path.exists("products.csv"):
    products = pd.read_csv("products.csv")
else:
    products = pd.DataFrame(columns=["product_id", "product_name", "description", "price"])

# Ensure price column is numeric
if "price" in products.columns:
    products["price"] = pd.to_numeric(products["price"], errors="coerce").fillna(0.0)

if os.path.exists("invoice_history.csv"):
    invoice_history = pd.read_csv("invoice_history.csv")
else:
    invoice_history = pd.DataFrame(columns=["invoice_no", "customer_name", "products", "total", "date"])


# ---------- Helper Function ----------
def generate_invoice(customer, selected_products_df, quantities):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=30)
    pdf.cell(200, 10, txt="INVOICE", ln=True, align='C')

    try:
        if os.path.exists("company_logo.png"):
            pdf.image("company_logo.png", x=160, y=25, w=30)
    except Exception:
        pass

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="SD Pvt Ltd.", ln=True)
    pdf.cell(200, 10, txt="Delhi, India", ln=True)
    pdf.cell(200, 10, txt="Pincode: 110080", ln=True)
    pdf.cell(200, 10, txt="Email: mail.anujgupta@gmail.com", ln=True)
    pdf.cell(200, 10, txt="", ln=True)

    pdf.set_font("Arial", 'B', size=20)
    pdf.cell(200, 10, txt="Customer Details", ln=True)
    pdf.cell(200, 10, txt="", ln=True)

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Customer: {customer['customer_name']}", ln=True)
    pdf.cell(200, 10, txt=f"Address: {customer['address']}", ln=True)
    pdf.cell(200, 10, txt=f"Mobile: {customer['mobile']}", ln=True)
    pdf.cell(200, 10, txt=f"Email: {customer['email']}", ln=True)
    pdf.cell(200, 10, txt="", ln=True)

    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(60, 10, txt="Product", border=1)
    pdf.cell(60, 10, txt="Description", border=1)
    pdf.cell(20, 10, txt="Qty", border=1)
    pdf.cell(30, 10, txt="Unit Price", border=1)
    pdf.cell(30, 10, txt="Total", border=1)
    pdf.ln()

    total = 0
    pdf.set_font("Arial", size=12)

    for i, (_, product) in enumerate(selected_products_df.reset_index(drop=True).iterrows()):
        quantity = int(quantities[i]) if i < len(quantities) else 1
        price = float(product.get('price', 0.0))
        line_total = price * quantity
        total += line_total

        pdf.cell(60, 10, txt=str(product.get('product_name', '')), border=1)
        pdf.cell(60, 10, txt=str(product.get('description', '')), border=1)
        pdf.cell(20, 10, txt=str(quantity), border=1)
        pdf.cell(30, 10, txt=f"${price:.2f}", border=1)
        pdf.cell(30, 10, txt=f"${line_total:.2f}", border=1)
        pdf.ln()

    pdf.cell(200, 10, txt=" ", ln=True)
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(170, 10, txt="Total", border=1)
    pdf.cell(30, 10, txt=f"${total:.2f}", border=1)

    invoice_no = len(invoice_history) + 1
    filename = f"invoice_{invoice_no}.pdf"
    pdf.output(filename)
    return filename, round(total, 2), invoice_no


# ---------- Streamlit UI ----------
st.title(" Invoice Automation System")
st.sidebar.header("Select or Add Customer")

# Initialize session state toggles
for key in ["add_customer", "delete_customer", "add_product", "delete_product"]:
    if key not in st.session_state:
        st.session_state[key] = False


# ---- Add Customer ----
st.session_state.add_customer = st.sidebar.checkbox("Add New Customer", value=st.session_state.add_customer)
if st.session_state.add_customer:
    new_name = st.sidebar.text_input("Customer Name")
    new_address = st.sidebar.text_input("Address")
    new_mobile = st.sidebar.text_input("Mobile")
    new_email = st.sidebar.text_input("Email")
    if st.sidebar.button("Save Customer"):
        new_id = len(customers) + 1
        customers.loc[len(customers)] = [new_id, new_name, new_address, new_mobile, new_email]
        customers.to_csv("customers.csv", index=False)
        st.sidebar.success("Customer added successfully!")

# ---- Delete Customer ----
if not customers.empty:
    st.session_state.delete_customer = st.sidebar.checkbox("🗑 Delete Customer", value=st.session_state.delete_customer)
    if st.session_state.delete_customer:
        delete_customer = st.sidebar.selectbox("Select Customer to Delete", customers["customer_name"].tolist())
        if st.sidebar.button("Confirm Delete Customer"):
            customers = customers[customers["customer_name"] != delete_customer]
            customers.to_csv("customers.csv", index=False)
            st.sidebar.success(f"🗑 Customer '{delete_customer}' deleted successfully!")


# ---- Customer Selection ----
customer_names = customers["customer_name"].tolist()
if not customer_names:
    st.warning("Please add a customer first!")
else:
    selected_customer = st.sidebar.selectbox("Customer", customer_names)
    customer = customers[customers['customer_name'] == selected_customer].iloc[0]

    st.sidebar.header("Select Products")

    # ---- Add Product ----
    st.session_state.add_product = st.sidebar.checkbox(" Add New Product", value=st.session_state.add_product)
    if st.session_state.add_product:
        new_pname = st.sidebar.text_input("Product Name")
        new_desc = st.sidebar.text_input("Description")
        new_price = st.sidebar.number_input("Price", min_value=0.0, value=0.0)
        if st.sidebar.button("Save Product"):
            new_pid = len(products) + 1
            products.loc[len(products)] = [new_pid, new_pname, new_desc, new_price]
            products.to_csv("products.csv", index=False)
            st.sidebar.success(" Product added successfully!")

    # ---- Delete Product ----
    if not products.empty:
        st.session_state.delete_product = st.sidebar.checkbox("🗑 Delete Product", value=st.session_state.delete_product)
        if st.session_state.delete_product:
            delete_product = st.sidebar.selectbox("Select Product to Delete", products["product_name"].tolist())
            if st.sidebar.button("Confirm Delete Product"):
                products = products[products["product_name"] != delete_product]
                products.to_csv("products.csv", index=False)
                st.sidebar.success(f"🗑 Product '{delete_product}' deleted successfully!")

    # ---- Product Selection ----
    product_names = products['product_name'].tolist()
    selected_products = st.sidebar.multiselect("Products", product_names)

    if selected_products:
        try:
            product_rows = products.set_index('product_name').loc[selected_products].reset_index()
        except KeyError:
            product_rows = products[products['product_name'].isin(selected_products)].reset_index(drop=True)
    else:
        product_rows = pd.DataFrame(columns=products.columns)

    quantities = []
    for product in selected_products:
        q = st.sidebar.number_input(f"Quantity of {product}", min_value=1, max_value=100, value=1, key=f"qty_{product}")
        quantities.append(q)

    if st.sidebar.button("Generate Invoice"):
        if not selected_products:
            st.error("Please select at least one product.")
        else:
            filename, total, invoice_no = generate_invoice(customer, product_rows, quantities)
            date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
            invoice_history.loc[len(invoice_history)] = [invoice_no, selected_customer, ", ".join(selected_products), total, date_now]
            invoice_history.to_csv("invoice_history.csv", index=False)

            with open(filename, 'rb') as f:
                st.download_button(" Download Invoice", f, file_name=filename, mime="application/pdf")

            with open(filename, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"></iframe>', unsafe_allow_html=True)


# ---------- Invoice History Section ----------
st.subheader("📜 Invoice History")
if not invoice_history.empty:
    st.dataframe(invoice_history)
else:
    st.info("No invoices generated yet.")