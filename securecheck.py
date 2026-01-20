# SecureCheck: Police Post Log Ledger 


# Imports

import mysql.connector
import pandas as pd
import streamlit as st
import plotly.express as px


# Database Connection

def new_connection():
    """Create a new connection to the MySQL database."""
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",   # 🔐 Replace with your DB password if set
            database="secure"
        )
        return mydb
    except mysql.connector.Error as e:
        st.error(f"Connection Error: {e}")
        return None


# Fetch Data from Database

def fetch_data(query):
    """Fetch data from MySQL and return as DataFrame."""
    conn = new_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            return df
        finally:
            conn.close()
    else:
        return pd.DataFrame()


# Streamlit Page Config

st.set_page_config(page_title="Secure - Police Post Logs", layout="wide")
st.title("🚔 SecureCheck: Police Post Log Ledger")
st.balloons()


# Sidebar Navigation

menu = st.sidebar.selectbox(
    "Navigate", 
    ["Home", "Data Analytics & Visuals", "View Logs", "Add Logs"]
)


# Fetch Full Table

query = "SELECT * FROM secure.check"
data = fetch_data(query)

st.header("📋 Police Logs Overview")
st.dataframe(data, use_container_width=True)


# Quick Metrics

st.header("📊 Key Metrics")
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Police Stops", len(data))

c2.metric(
    "Total Arrests",
    int(data["is_arrested"].sum()) if "is_arrested" in data.columns else 0
)

c3.metric(
    "Search Conducted",
    int(data["search_conducted"].sum()) if "search_conducted" in data.columns else 0
)

c4.metric(
    "Warnings",
    len(
        data[
            data["stop_outcome"]
            .str.contains("warning", case=False, na=False)
        ]
    ) if "stop_outcome" in data.columns else 0
)


# Visual Insights (Error-Free)

st.header("📈 Visual Insights")
tab1, tab2 = st.tabs(["Stops by Violation", "Driver Gender Distribution"])

# ----- Stops by Violation -----
with tab1:
    if not data.empty and 'violation' in data.columns:
        violation_data = data['violation'].value_counts().reset_index()
        violation_data.columns = ['Violation', 'Count']

        if not violation_data.empty:
            fig1 = px.bar(
                violation_data,
                x='Violation',
                y='Count',
                title="Stops by Violation Type",
                color='Violation'
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("No violation data to display.")
    else:
        st.warning("Violation column not found in database.")

# ----- Driver Gender Distribution -----
with tab2:
    if not data.empty and 'driver_gender' in data.columns:
        gender_data = data['driver_gender'].value_counts().reset_index()
        gender_data.columns = ['Gender', 'Count']

        if not gender_data.empty:
            fig2 = px.pie(
                gender_data,
                names='Gender',
                values='Count',
                title="Driver Gender Distribution"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No gender data to display.")
    else:
        st.warning("Driver gender column not found in database.")


# Advanced Queries 

st.header("🔍 Advanced Insights")
selected_query = st.selectbox("Select a Query to Run", [
    "Total Number of Police Stops",
    "Count of Stops by Violation Type",
    "Number of Arrests vs. Warnings",
    "Average Age of Drivers Stopped",
    "Top 5 Most Frequent Search Types",
    "Count of Stops by Gender",
    "Most Common Violation for Arrests",
    "Top 10 Vehicles in Drug-Related Stops",
    "Most Frequently Searched Vehicles",
    "Driver Age Group with Highest Arrest Rate",
    "Gender Distribution of Drivers by Country",
    "Race & Gender Combination with Highest Search Rate",
    "Time of Day with Most Traffic Stops",
    "Average Stop Duration by Violation",
    "Arrest Rate by Country and Violation"
])

query_map = {
    "Total Number of Police Stops": 
        "SELECT COUNT(*) AS total_stops FROM secure.check",

    "Count of Stops by Violation Type": 
        "SELECT violation, COUNT(*) AS count FROM secure.check GROUP BY violation ORDER BY count DESC",

    "Number of Arrests vs. Warnings": 
        "SELECT stop_outcome, COUNT(*) AS count FROM secure.check GROUP BY stop_outcome",

    "Average Age of Drivers Stopped": 
        "SELECT AVG(driver_age) AS average_age FROM secure.check",

    "Top 5 Most Frequent Search Types": 
        "SELECT search_type, COUNT(*) AS count FROM secure.check WHERE search_type != '' GROUP BY search_type ORDER BY count DESC LIMIT 5",

    "Count of Stops by Gender": 
        "SELECT driver_gender, COUNT(*) AS count FROM secure.check GROUP BY driver_gender",

    "Most Common Violation for Arrests": 
        "SELECT violation, COUNT(*) AS count FROM secure.check WHERE stop_outcome LIKE '%Arrest%' GROUP BY violation ORDER BY count DESC",

    "Top 10 Vehicles in Drug-Related Stops":
        "SELECT vehicle_number, COUNT(*) AS count FROM secure.check WHERE drugs_related_stop=1 GROUP BY vehicle_number ORDER BY count DESC LIMIT 10",

    "Most Frequently Searched Vehicles":
        "SELECT vehicle_number, COUNT(*) AS count FROM secure.check WHERE search_conducted=1 GROUP BY vehicle_number ORDER BY count DESC LIMIT 10",

    "Driver Age Group with Highest Arrest Rate":
        "SELECT driver_age, COUNT(*) AS arrests FROM secure.check WHERE is_arrested=1 GROUP BY driver_age ORDER BY arrests DESC LIMIT 1",

    "Gender Distribution of Drivers by Country":
        "SELECT country_name, driver_gender, COUNT(*) AS count FROM secure.check GROUP BY country_name, driver_gender",

    "Race & Gender Combination with Highest Search Rate":
        "SELECT driver_race, driver_gender, COUNT(*) AS count FROM secure.check WHERE search_conducted=1 GROUP BY driver_race, driver_gender ORDER BY count DESC LIMIT 1",

    "Time of Day with Most Traffic Stops":
        "SELECT stop_time, COUNT(*) AS count FROM secure.check GROUP BY stop_time ORDER BY count DESC LIMIT 1",

    "Average Stop Duration by Violation":
        "SELECT violation, AVG(TIME_TO_SEC(stop_duration))/60 AS avg_duration_minutes FROM secure.check GROUP BY violation",

    "Arrest Rate by Country and Violation":
        "SELECT country_name, violation, SUM(is_arrested)/COUNT(*) AS arrest_rate FROM secure.check GROUP BY country_name, violation"
}

if st.button("Run Query"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.write(result)
    else:
        st.warning("No results found for the selected query.")


# Add New Police Log & Predict Outcome

st.markdown("---")
st.header("📝 Add New Police Log & Predict Outcome")

stop_duration_options = (
    data["stop_duration"].dropna().unique() 
    if not data.empty and 'stop_duration' in data.columns
    else ["0-15 min", "16-30 min", "30+ min"]
)

with st.form("new_log_form"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    county_name = st.text_input("County Name")  # optional
    driver_gender = st.selectbox("Driver Gender", ["male", "female"])
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27)
    driver_race = st.text_input("Driver Race")
    search_conducted = st.selectbox("Was a Search Conducted?", ["0", "1"])
    search_type = st.text_input("Search Type")
    stop_duration = st.selectbox("Stop Duration", stop_duration_options)
    vehicle_number = st.text_input("Vehicle Number")
    timestamp = pd.Timestamp.now()

    submitted = st.form_submit_button("Predict & Save")

    if submitted:
        # Safe Filtering
        filtered_data = data.copy()
        if 'driver_gender' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['driver_gender'] == driver_gender]
        if 'driver_age' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['driver_age'] == driver_age]
        if 'search_conducted' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['search_conducted'] == int(search_conducted)]
        if 'stop_duration' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['stop_duration'] == stop_duration]

        # Predictions
        predicted_outcome = filtered_data['stop_outcome'].mode()[0] if 'stop_outcome' in filtered_data.columns and not filtered_data.empty else "warning"
        predicted_violation = filtered_data['violation'].mode()[0] if 'violation' in filtered_data.columns and not filtered_data.empty else "speeding"

        # Summary
        search_text = "A search was conducted" if int(search_conducted) else "No search was conducted"
        st.markdown(f"""
        🧠 **Prediction Summary**  
        **Predicted Violation:** `{predicted_violation}`  
        **Predicted Stop Outcome:** `{predicted_outcome}`  

        ---
        🚓 A {driver_age}-year-old {driver_gender} driver in **{county_name}**  
        was stopped at **{stop_time.strftime('%I:%M %p')}** on **{stop_date}**.  

        {search_text}  

        **Stop duration:** `{stop_duration}`  
        **Vehicle number:** `{vehicle_number}`
        """)

        # Insert into Database
        conn = new_connection()
        if conn:
            cursor = conn.cursor()
            db_columns_df = fetch_data("SHOW COLUMNS FROM secure.check")
            db_columns = db_columns_df['Field'].tolist() if not db_columns_df.empty else []

            columns_to_insert = []
            values = []

            if 'stop_date' in db_columns: columns_to_insert.append('stop_date'); values.append(stop_date)
            if 'stop_time' in db_columns: columns_to_insert.append('stop_time'); values.append(stop_time)
            if 'county_name' in db_columns: columns_to_insert.append('county_name'); values.append(county_name)
            if 'driver_gender' in db_columns: columns_to_insert.append('driver_gender'); values.append(driver_gender)
            if 'driver_age' in db_columns: columns_to_insert.append('driver_age'); values.append(driver_age)
            if 'driver_race' in db_columns: columns_to_insert.append('driver_race'); values.append(driver_race)
            if 'search_conducted' in db_columns: columns_to_insert.append('search_conducted'); values.append(int(search_conducted))
            if 'search_type' in db_columns: columns_to_insert.append('search_type'); values.append(search_type)
            if 'stop_duration' in db_columns: columns_to_insert.append('stop_duration'); values.append(stop_duration)
            if 'vehicle_number' in db_columns: columns_to_insert.append('vehicle_number'); values.append(vehicle_number)
            if 'stop_outcome' in db_columns: columns_to_insert.append('stop_outcome'); values.append(predicted_outcome)
            if 'violation' in db_columns: columns_to_insert.append('violation'); values.append(predicted_violation)
            if 'timestamp' in db_columns: columns_to_insert.append('timestamp'); values.append(timestamp)

            if columns_to_insert:
                insert_query = f"""
                    INSERT INTO secure.check ({', '.join(columns_to_insert)})
                    VALUES ({', '.join(['%s'] * len(values))})
                """
                cursor.execute(insert_query, values)
                conn.commit()
                st.success("✅ New log added successfully!")
            else:
                st.warning("No valid columns to insert into database.")
            conn.close()


# Footer

st.markdown("---")
st.markdown("Built with ❤️ for Law Enforcement by SecureCheck")
