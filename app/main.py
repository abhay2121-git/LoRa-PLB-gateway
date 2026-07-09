# Entry Point of FastAPI
from fastapi import FastAPI
import json

app = FastAPI()

def load_data():
    with open(r"C:\Users\Abhay\OneDrive\Desktop\lora-plb-gateway\app\nodes.json") as f:
        data = json.load(f)
        return data

@app.get('/')
def user_interface():
    return {'message' : 'LoRa PLB Gateway UI'}

@app.get('/view_node_ids')
def nodeid():
    data = load_data()
    return data

# @app.get('/node_info{node}')