import csv
from pathlib import Path
from main.models import CPU, GPU

base_dir = Path(__file__).resolve().parent
CPU_CSV_PATH = base_dir / 'data' / 'newpassmark_CPU.csv'
GPU_CSV_PATH = base_dir / 'data' / 'newpassmark_GPU.csv'

def safe_int(value):
    if value == "NA" or value == "" or value is None:
        return None  
    try:
        return int(value)
    except ValueError:
        return None
    
def clean_vram(value):
    """Removes ' MB' and converts to int"""
    if value and "MB" in value:
        return safe_int(value.replace(" MB", "").strip())
    return safe_int(value)

def import_cpu_data():
    with open(CPU_CSV_PATH, 'r') as file:
        reader = csv.DictReader(file)
        cpu_objects = []

        for row in reader:
            cpu_objects.append(CPU(
                cpu_name=row['cpu_name'],
                cores=safe_int(row['cores']),
                cpu_mark=safe_int(row['cpu_mark']),
                thread_mark=safe_int(row['thread_mark']),
                tdp=safe_int(row['tdp']),
                socket=row['socket'],
                category=row['category']
            ))
        CPU.objects.bulk_create(cpu_objects)
    print("CPU data loaded successfully!")

def import_gpu_data():
    with open(GPU_CSV_PATH, 'r') as file:
        reader = csv.DictReader(file)
        gpu_objects = []

        for row in reader:
            gpu_objects.append(GPU(
                gpu_name=row['gpu_name'],
                g3d_mark=safe_int(row['g3d_mark']),
                g2d_mark=safe_int(row['g2d_mark']),
                tdp=safe_int(row['tdp']),
                vram=clean_vram(row['vram']),
                category=row['category']
            ))
        GPU.objects.bulk_create(gpu_objects)
    print("GPU data loaded successfully!")


def run():
    print("Clearing existing data...")
    CPU.objects.all().delete()
    GPU.objects.all().delete()
    

    print("Importing new data...")
    import_cpu_data()
    import_gpu_data()
    

    print("All data loaded successfully!")

if __name__ == "__main__":
    run()
