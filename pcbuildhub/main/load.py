import csv
from pathlib import Path
from main.models import CPU, GPU

base_dir = Path(__file__).resolve().parent
CPU_CSV_PATH = base_dir / 'data' / 'passmark_CPU.csv'
GPU_CSV_PATH = base_dir / 'data' / 'passmark_GPU.csv'

def safe_int(value):
    if value == "NA" or value == "" or value is None:
        return None  
    try:
        return int(value)
    except ValueError:
        return None

def import_cpu_data():
    with open(CPU_CSV_PATH, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            print(f"Processing CPU: {row['cpu_name']} with: {row['tdp']}")

            CPU.objects.create(
                cpu_name=row['cpu_name'],
                cores=safe_int(row['cores']),
                cpu_mark=safe_int(row['cpu_mark']),
                thread_mark=safe_int(row['thread_mark']),
                tdp=safe_int(row['tdp']),
                socket=row['socket'],
                category=row['category']
            )

def import_gpu_data():
    with open(GPU_CSV_PATH, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            print(f"Processing GPU: {row['gpu_name']} with: {row['tdp']}")

            GPU.objects.create(
                gpu_name=row['gpu_name'],
                g3d_mark=safe_int(row['g3d_mark']),
                g2d_mark=safe_int(row['g2d_mark']),
                tdp=safe_int(row['tdp']),  
                vram=safe_int(row['vram']),
                category=row['category']
            )

def run():
    import_cpu_data()
    import_gpu_data()
    print("Data loaded successfully!")

if __name__ == "__main__":
    run()
