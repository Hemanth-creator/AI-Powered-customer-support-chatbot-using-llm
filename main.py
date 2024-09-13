from langchain_google_genai import GoogleGenerativeAI
import os
import pyodbc
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine,text
from langchain.chains import create_sql_query_chain
import streamlit as st

llm = GoogleGenerativeAI(model="gemini-pro",google_api_key="AIzaSyAP3lP8CBJ8bsuLSzF5Ll9SMJR2Olggyqc")

def connect_to_DB():
    try:
        server = "DESKTOP-746R9QA\SQLEXPRESS"  # Replace with your SQL Server name or IP address
        database = "customer_Support_db"  # Replace with your database name

        connection_string = (
            f"mssql+pyodbc://{server}/{database}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
            "&trusted_connection=yes"
        )

        db_engine=create_engine(connection_string)

        db=SQLDatabase(db_engine)
        # print(db.table_info)
        return db,db_engine

    except Exception as e:
        print(f"Error:{e}")
        
def generate_sql_query(llm,db,query):
    chain = create_sql_query_chain(llm, db)
    response = chain.invoke({"question":query})
    cleaned_query = response.strip('```sql\n').strip('\n```')
    return cleaned_query


def execute_query(db_engine, query):
    conn = db_engine.connect()
    try:
        if 'SELECT' in query:
            with conn.begin():
                result = conn.execute(text(query))
                rows = result.fetchall()
                columns = result.keys()
                records = [dict(zip(columns, row)) for row in rows]
            return records
        else: 
            with conn.begin():
                result = conn.execute(text(query))
                # Get the number of rows affected
                affected_rows = result.rowcount
            return affected_rows  # Return the number of affected rows if needed
    except Exception as e:
        print(f"Error during SELECT operation: {e}")
        conn.rollback()  # Rollback the transaction in case of error
    finally:
        conn.close()
        
def generate_response(question,llm,data):
    string = f"question:{question},data: {data},instructions :based on the data given answer with the perfect answer to the question asked as if a polite customer support agent answers if the data given is not sufficient to answer the question reply that data is not sufficient"
    response = llm.invoke(string)
    return response
  

st.title("AI Powered Customer Assistant")

query = st.text_input("Enter your query")
if st.button('ask'):
    # query = "how many orders did user with id 1 place?" 
    db,db_engine= connect_to_DB()
    sqlquery = generate_sql_query(llm,db,query)
    print(sqlquery)
    result = execute_query(db_engine, sqlquery)
    response = generate_response(query,llm,result)
    st.write(response)
