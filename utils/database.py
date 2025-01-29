import os
import pandas as pd
import streamlit as st
from pathlib import Path
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from utils.env_loader import load_env_var

# Globale connection pool
_pool = None

def get_connection_pool(min_conn=1, max_conn=10):
    """Maak een connection pool aan voor de database"""
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(
            min_conn,
            max_conn,
            host=load_env_var('DB_HOST'),
            port=load_env_var('DB_PORT'),
            database=load_env_var('DB_NAME'),
            user=load_env_var('DB_USER'),
            password=load_env_var('DB_PASSWORD')
        )
    return _pool

@contextmanager
def get_db_connection():
    """Context manager voor database connecties"""
    pool = get_connection_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

def execute_query(query, params=None):
    """Voer een query uit en return de resultaten als DataFrame"""
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

@st.cache_data(ttl=3600)
def load_data(query, params=None):
    """Laad data met caching"""
    return execute_query(query, params)

@st.cache_data(ttl=3600)
def load_orders_data():
    """Laad orders data"""
    query = """
    SELECT 
    o.*,
    c.name as client_name,
    m.model as machine_model,
    m.brand as machine_brand,
    m.vin as machine_vin,
    SUM(oc.unit_price * oc.amount) as total_parts_cost,
    SUM(st.hours * wl.price_per_hour + st.minutes / 60.0 * wl.price_per_hour) as total_labour_cost
    FROM orders o
    LEFT JOIN clients c ON o.client_id = c.id
    LEFT JOIN machines m ON o.machine_id = m.id
    LEFT JOIN invoices i ON o.invoice_id = i.id
    LEFT JOIN order_costs oc ON o.id = oc.order_id
    LEFT JOIN worker_labours wl ON o.id = wl.order_id
    LEFT JOIN time_v2s st ON wl.specified_time_id = st.id
    GROUP BY o.id, c.name, m.model, m.brand, m.vin, i.number
    """
    return load_data(query)

@st.cache_data(ttl=3600)
def load_worker_labours_data():
    """Laad worker labour data"""
    query = """
    SELECT DISTINCT
        wl.id,
        wl.order_id,
        wl.worker_id,
        wl.price_per_hour,
        wl.specified_time_id,
        w.name as worker_name,
        o.number as order_number,
        o.category,
        o.created_at,
        st.hours,
        st.minutes,
        (COALESCE(st.hours, 0) + COALESCE(st.minutes, 0) / 60.0) as total_hours
    FROM worker_labours wl
    JOIN workers w ON wl.worker_id = w.id
    JOIN orders o ON wl.order_id = o.id
    LEFT JOIN time_v2s st ON wl.specified_time_id = st.id
    """
    return load_data(query)

@st.cache_data(ttl=3600)
def load_parts_data():
    """Laad parts data"""
    query = """
    SELECT 
        o.id,
        o.defect_date,
        o.number,
        o.client_id,
        o.category,
        o.warranty_number,
        o.causal_part_id,
        o.machine_id,
        o.machine_hours,
        o.appointment,
        o.replacement_vehicle,
        o.on_location,
        REPLACE(o.description, E'\n', '; ') AS description,
        o.diagnosis,
        o.parts_discount,
        o.labour_cost_adjusted,
        o.comment_worker,
        o.comment_office,
        o.comment_invoice,
        o.status,
        o.printed,
        COALESCE(i.number, '') as invoice_number,
        o.created_at,
        o.invoice_id,
        o.washed,
        o.client_active,
        o.assigned_to_worker_id,
        o.major_maintenance,
        o.minor_maintenance,
        o.repeated_repair,
        o.original_order_id,
        o.registered_at_garage,
        c.name as client_name,
        m.model as machine_model,
        m.brand as machine_brand,
        m.vin as machine_vin,
        SUM(oc.unit_price * oc.amount) as total_parts_cost,
        SUM(st.hours * wl.price_per_hour + st.minutes / 60.0 * wl.price_per_hour) as total_labour_cost,
        p.number as part_number,
        p.description as part_description,
        p.price as part_price,
        p.brand as part_brand,
        op.amount as part_quantity
    FROM orders o
    LEFT JOIN clients c ON o.client_id = c.id
    LEFT JOIN machines m ON o.machine_id = m.id
    LEFT JOIN invoices i ON o.invoice_id = i.id
    LEFT JOIN order_costs oc ON o.id = oc.order_id
    LEFT JOIN worker_labours wl ON o.id = wl.order_id
    LEFT JOIN time_v2s st ON wl.specified_time_id = st.id
    LEFT JOIN order_parts op ON o.id = op.order_id
    LEFT JOIN parts p ON op.part_id = p.id
    GROUP BY 
        o.id, o.defect_date, o.number, o.client_id, o.category, o.warranty_number, 
        o.causal_part_id, o.machine_id, o.machine_hours, o.appointment, 
        o.replacement_vehicle, o.on_location, o.description, o.diagnosis, 
        o.parts_discount, o.labour_cost_adjusted, o.comment_worker, 
        o.comment_office, o.comment_invoice, o.status, o.printed, 
        i.number, o.created_at, o.invoice_id, o.washed, 
        o.client_active, o.assigned_to_worker_id, o.major_maintenance, 
        o.minor_maintenance, o.repeated_repair, o.original_order_id, 
        o.registered_at_garage, c.name, m.model, m.brand, m.vin, 
        p.number, p.description, p.price, p.brand, op.amount
    """
    return load_data(query)

@st.cache_data(ttl=3600)
def load_used_parts_data():
    """Laad used parts data"""
    query = """
    SELECT 
        p.number AS part_number,
        p.description AS part_description,
        SUM(op.amount) AS used_quantity,
        o.defect_date,
        c.name AS client_name
    FROM order_parts op
    JOIN parts p ON op.part_id = p.id
    JOIN orders o ON op.order_id = o.id
    JOIN clients c ON o.client_id = c.id
    GROUP BY p.number, p.description, o.defect_date, c.name
    ORDER BY o.defect_date DESC
    """
    return load_data(query)

@st.cache_data(ttl=3600)
def load_all_data():
    """Laad alle data sequentieel"""
    orders_df = load_orders_data()
    worker_labours_df = load_worker_labours_data()
    parts_df = load_parts_data()
    used_parts_df = load_used_parts_data()
    
    return orders_df, worker_labours_df, parts_df, used_parts_df



# @st.cache_data(ttl=3600)
# def load_sold_parts_data():
#     """Load sold parts data from parts database"""
#     parts_engine = get_parts_connection()
#     return pd.read_sql("""
#         SELECT 
#             dn.id as delivery_note_id,
#             dn.created_at as order_date,
#             c.name as client_name,
#             dnp.amount,
#             p.number as part_number,
#             p.name as part_description,
#             COALESCE(dnp.custom_price, pp.value) as unit_price,
#             COALESCE(dnp.discount_manual, 0) as discount_manual_percentage,
#             COALESCE(dnp.discount_extra, 0) as discount_extra_percentage,
#             COALESCE(cpd.discount, 0) as client_part_discount_percentage
#         FROM delivery_note_parts dnp
#         JOIN part_prices pp ON pp.id = dnp.part_price_id
#         JOIN parts p ON p.id = pp.part_id
#         LEFT JOIN client_part_discounts cpd ON cpd.id = dnp.client_part_discount_id
#         JOIN delivery_notes dn ON dn.id = dnp.delivery_note_id
#         JOIN clients c ON c.id = dn.client_id
#         WHERE dnp.deleted = false and dn.deleted = false and dnp.created_at > '2024-01-01'
#     """, parts_engine)

# def calculate_sold_parts_data(df):
#     """Perform calculations on sold parts data"""
#     df['base_price'] = df['amount'] * df['unit_price']
#     df['manual_discount_amount'] = df['base_price'] * (df['discount_manual_percentage'] / 100)
#     df['extra_discount_amount'] = df['base_price'] * (1 - df['discount_manual_percentage'] / 100) * (df['discount_extra_percentage'] / 100)
#     df['client_discount_amount'] = df['base_price'] * (1 - df['discount_manual_percentage'] / 100) * (1 - df['discount_extra_percentage'] / 100) * (df['client_part_discount_percentage'] / 100)
#     
#     # Group by delivery note and client
#     grouped = df.groupby(['delivery_note_id', 'order_date', 'client_name', 'part_number', 'part_description']).agg(
#         total_amount=('amount', 'sum'),
#         total_unit_price=('unit_price', 'sum'),
#         total_base_price=('base_price', 'sum'),
#         total_manual_discount=('manual_discount_amount', 'sum'),
#         total_extra_discount=('extra_discount_amount', 'sum'),
#         total_client_discount=('client_discount_amount', 'sum'),
#         total_price_with_discount=('final_price', 'sum')
#     ).reset_index()
#     
#     return grouped

# ... Rest van de query functies op dezelfde manier ...
