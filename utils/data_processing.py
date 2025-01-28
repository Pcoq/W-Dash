import pandas as pd
import numpy as np
from utils.excel_utils import to_excel
from io import BytesIO

def calculate_order_metrics(orders_df):
    """Calculate key metrics from orders data"""
    metrics = {
        'total_orders': len(orders_df),
        'completed_orders': len(orders_df[orders_df['status'] == 'completed']),
        'avg_labour_cost': orders_df['labour_cost_adjusted'].mean(),
        'warranty_orders': len(orders_df[orders_df['warranty_number'].notna()]),
        'total_parts_cost': orders_df['total_parts_cost'],
        'total_labour_cost': orders_df['total_labour_cost']
    }
    
    return metrics

def process_worker_productivity(worker_labours_df):
    """Calculate worker productivity metrics"""
    productivity = worker_labours_df.groupby('worker_name').agg({
        'order_id': 'count',
        'price_per_hour': 'mean'
    }).reset_index()
    productivity.columns = ['worker_name', 'total_tasks', 'avg_rate']
    return productivity

def get_machine_maintenance_stats(orders_df, machines_df):
    """Calculate machine maintenance statistics"""
    maintenance_stats = orders_df[orders_df['category'] == 'maintenance'].groupby('machine_id').agg({
        'id': 'count',
        'labour_cost_adjusted': 'sum'
    }).reset_index()
    return maintenance_stats.merge(machines_df[['id', 'model', 'brand']], 
                                 left_on='machine_id', right_on='id')

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    return output.getvalue()

def calculate_sold_parts_data(df):
    """Perform calculations on sold parts data"""
    df['base_price'] = df['amount'] * df['unit_price']
    df['manual_discount_amount'] = df['base_price'] * (df['discount_manual_percentage'] / 100)
    df['extra_discount_amount'] = df['base_price'] * (1 - df['discount_manual_percentage'] / 100) * (df['discount_extra_percentage'] / 100)
    df['client_discount_amount'] = df['base_price'] * (1 - df['discount_manual_percentage'] / 100) * (1 - df['discount_extra_percentage'] / 100) * (df['client_part_discount_percentage'] / 100)
    df['final_price'] = df['base_price'] * (1 - df['discount_manual_percentage'] / 100) * (1 - df['discount_extra_percentage'] / 100) * (1 - df['client_part_discount_percentage'] / 100)
    
    # Group by delivery note and client
    grouped = df.groupby(['delivery_note_id', 'order_date', 'client_name', 'part_number', 'part_description']).agg(
        total_amount=('amount', 'sum'),
        total_unit_price=('unit_price', 'sum'),
        total_base_price=('base_price', 'sum'),
        total_manual_discount=('manual_discount_amount', 'sum'),
        total_extra_discount=('extra_discount_amount', 'sum'),
        total_client_discount=('client_discount_amount', 'sum'),
        total_price_with_discount=('final_price', 'sum')
    ).reset_index()
    
    return grouped
