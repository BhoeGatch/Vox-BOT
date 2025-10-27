import pandas as pd
import os
from datetime import datetime

def log_interaction(query, response, log_file='logs/interactions.csv'):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    df = pd.DataFrame({
        'timestamp': [datetime.now()],
        'query': [query],
        'response': [response]
    })
    if os.path.exists(log_file):
        df.to_csv(log_file, mode='a', header=False, index=False)
    else:
        df.to_csv(log_file, index=False)