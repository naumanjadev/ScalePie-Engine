import sys
import getpass
sys_user = getpass.getuser()
sys.path.append(f"/home/{sys_user}/gtp/backend/")

from datetime import datetime, timedelta
from src.new_setup.adapter import NodeAdapter
from src.new_setup.utils import MaxWaitTimeExceededException, get_chain_config
from src.db_connector import DbConnector
from airflow.decorators import dag, task
from src.misc.airflow_utils import alert_via_webhook

@dag(
    default_args={
        'owner': 'nader',
        'retries': 2,
        'email_on_failure': False,
        'retry_delay': timedelta(minutes=1),
        'on_failure_callback': alert_via_webhook
    },
    dag_id='raw_mantle',
    description='Load raw tx data from Mantle',
    tags=['raw', 'near-real-time', 'rpc', 'new-setup'],
    start_date=datetime(2023, 9, 1),
    schedule_interval='*/15 * * * *'
)

def adapter_rpc():
    @task()
    def run_mantle():

        # Initialize DbConnector
        db_connector = DbConnector()
        
        chain_name = 'mantle'

        active_rpc_configs = get_chain_config(db_connector, chain_name)
        print(f"MANTLE_CONFIG={active_rpc_configs}")

        adapter_params = {
            'rpc': 'local_node',
            'chain': chain_name,
            'rpc_configs': active_rpc_configs,
        }

        # Initialize NodeAdapter
        adapter = NodeAdapter(adapter_params, db_connector)

        # Initial load parameters
        load_params = {
            'block_start': 'auto',
            'batch_size': 10,
        }

        try:
            adapter.extract_raw(load_params)
        except MaxWaitTimeExceededException as e:
            print(f"Extraction stopped due to maximum wait time being exceeded: {e}")
            raise e

    run_mantle()
adapter_rpc()