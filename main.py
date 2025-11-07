import streamlit as st
import pandas as pd
import hashlib
import smtplib
import random
import os
from datetime import datetime
from fpdf import FPDF
import base64

# ---------------- EMAIL CONFIG ----------------
SENDER_EMAIL = "anujgupta9755@gmail.com"         # 👈 your Gmail
EMAIL_PASSWORD = "ufbvhqsvakeieomv"     # 👈 app password (not Gmail password)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ---------------- USER DATA ----------------
if os.path.exists("users.csv"):
    users = pd.read_csv("users.csv")
else:
    users = pd.DataFrame(columns=["email", "password_hash"])
    users.to_csv("users.csv", index=False)

# ---------------- UTILITIES ----------------
def make_hash(password):
    return hashlib.sha256(str(password).encode()).hexdigest()

def send_email(to_email, subject, body):
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            msg = f"Subject: {subject}\n\n{body}"
            server.sendmail(SENDER_EMAIL, to_email, msg)
        return True
    except Exception as e:
        st.error(f"❌ Email sending failed: {e}")
        return False

# ---------------- SESSION VARS ----------------
for key in [
    "user", "otp_code", "otp_stage", "temp_email", "temp_pass",
    "reset_stage", "reset_email"
]:
    if key not in st.session_state:
        st.session_state[key] = None if key not in ["otp_stage", "reset_stage"] else False

# ---------------- LOGIN / SIGNUP FIRST ----------------
if not st.session_state.user:
    st.title("🔐 Login / Sign Up")

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    # LOGIN TAB
    with tab_login:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login"):
                if email in users["email"].values:
                    stored_hash = users.loc[users["email"] == email, "password_hash"].values[0]
                    if make_hash(password) == stored_hash:
                        st.session_state.user = email
                        st.success(f"✅ Logged in as {email}")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password.")
                else:
                    st.warning("⚠ No account found. Please sign up.")

        with col2:
            if st.button("Forgot Password?"):
                if not email:
                    st.warning("Enter your email first above.")
                elif email not in users["email"].values:
                    st.error("Email not registered.")
                else:
                    otp = random.randint(100000, 999999)
                    sent = send_email(email, "Password Reset OTP", f"Your OTP is: {otp}")
                    if sent:
                        st.session_state.otp_code = otp
                        st.session_state.reset_stage = True
                        st.session_state.reset_email = email
                        st.info(f"📩 OTP sent to {email}. Enter it below to reset your password.")

    # RESET PASSWORD
    if st.session_state.reset_stage:
        st.subheader("🔁 Reset Password")
        entered_otp = st.text_input("Enter OTP sent to your email", key="reset_otp")
        new_pass = st.text_input("New Password", type="password", key="reset_new_pass")
        confirm_pass = st.text_input("Confirm Password", type="password", key="reset_confirm_pass")
        if st.button("Reset Password"):
            if entered_otp == str(st.session_state.otp_code):
                if new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                elif not new_pass:
                    st.error("Password cannot be empty.")
                else:
                    users.loc[users["email"] == st.session_state.reset_email, "password_hash"] = make_hash(new_pass)
                    users.to_csv("users.csv", index=False)
                    st.success("✅ Password reset successful. Please log in again.")
                    st.session_state.reset_stage = False
                    st.session_state.reset_email = None
                    st.session_state.otp_code = None
                    st.success("✅ Password reset successful! Please log in again.")
                    st.rerun()

            else:
                st.error("❌ Invalid OTP.")

        if st.button("Cancel Reset"):
            st.session_state.reset_stage = False
            st.experimental_rerun()

    # SIGNUP TAB
    with tab_signup:
        if not st.session_state.otp_stage:
            new_email = st.text_input("New Email")
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")

            if st.button("Send OTP"):
                if new_email in users["email"].values:
                    st.warning("⚠ Email already registered.")
                elif new_pass != confirm_pass:
                    st.error("❌ Passwords do not match.")
                elif not new_email or not new_pass:
                    st.error("Please fill all fields.")
                else:
                    otp = random.randint(100000, 999999)
                    sent = send_email(new_email, "Signup Verification OTP", f"Your OTP is: {otp}")
                    if sent:
                        st.session_state.otp_code = otp
                        st.session_state.temp_email = new_email
                        st.session_state.temp_pass = new_pass
                        st.session_state.otp_stage = True
                        st.info(f"📩 OTP sent to {new_email}. Enter it below to verify.")
                        st.rerun()
        else:
            entered_otp = st.text_input("Enter OTP sent to your email")
            if st.button("Verify OTP"):
                if entered_otp == str(st.session_state.otp_code):
                    email = st.session_state.temp_email
                    password = st.session_state.temp_pass
                    users.loc[len(users)] = [email, make_hash(password)]
                    users.to_csv("users.csv", index=False)
                    st.success("🎉 Account created successfully! Please log in.")
                    st.session_state.otp_stage = False
                    st.session_state.otp_code = None
                    st.session_state.temp_email = None
                    st.session_state.temp_pass = None
                else:
                    st.error("❌ Incorrect OTP.")
            if st.button("Resend OTP"):
                otp = random.randint(100000, 999999)
                st.session_state.otp_code = otp
                send_email(st.session_state.temp_email, "Resent OTP", f"Your OTP is: {otp}")
                st.info("🔁 OTP resent successfully.")

    st.stop()  # Stop app here if not logged in

# ---------------- AFTER LOGIN: INVOICE APP ----------------
st.sidebar.success(f"✅ Logged in as {st.session_state.user}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.user = None
    st.rerun()
    # ---- Delete Account ----
with st.sidebar.expander("⚠ Delete Account"):
    st.warning("Deleting your account will permanently remove your data.")
    confirm_delete = st.checkbox("I understand and want to delete my account")
    if st.button("🗑 Confirm Delete Account"):
        if confirm_delete:
            users = users[users["email"] != st.session_state.user]
            users.to_csv("users.csv", index=False)
            st.success("🗑 Account deleted successfully.")
            st.session_state.user = None
            st.rerun()
        else:
            st.info("Please confirm before deleting.")
    
    
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
   
# ---------- Invoice History Delete Section ----------
st.subheader("Remove Invoice")

if not invoice_history.empty:
    st.dataframe(invoice_history)

    st.markdown("### 🗑 Manage Invoice History")
    delete_mode = st.radio(
        "Choose delete option:",
        ["None", "Delete Selected Invoice", "Clear All History"],
        horizontal=True
    )

    if delete_mode == "Delete Selected Invoice":
        selected_invoice = st.selectbox("Select Invoice No to Delete", invoice_history["invoice_no"].tolist())
        if st.button("Confirm Delete Invoice"):
            invoice_history = invoice_history[invoice_history["invoice_no"] != selected_invoice]
            invoice_history.to_csv("invoice_history.csv", index=False)
            st.success(f" Invoice {selected_invoice} deleted successfully.")
            st.rerun()

    elif delete_mode == "Clear All History":
        if st.button(" Confirm Delete All Invoices"):
            invoice_history = pd.DataFrame(columns=["invoice_no", "customer_name", "products", "total", "date"])
            invoice_history.to_csv("invoice_history.csv", index=False)
            st.success("🧹 All invoice history cleared successfully.")
            st.rerun()

else:
    st.info("No invoices delete yet.")

