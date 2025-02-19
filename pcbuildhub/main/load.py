import csv
from pathlib import Path
from main.models import CPU, GPU, HDD

base_dir = Path(__file__).resolve().parent
CPU_CSV_PATH = base_dir / 'data' / 'passmark_CPU.csv'
GPU_CSV_PATH = base_dir / 'data' / 'passmark_GPU.csv'
HDD_CSV_PATH = base_dir / 'data' / 'passmark_HDD.csv'

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
        cpu_objects = []  # Store objects in a list

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
                vram=safe_int(row['vram']),
                category=row['category']
            ))
        GPU.objects.bulk_create(gpu_objects)
    print("GPU data loaded successfully!")

def import_hdd_data():
    with open(HDD_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        hdd_objects = []

        for row in reader:
            print(f"Processing HDD: {row['drive_name']} with size {row['size']}")

            hdd_objects.append(HDD(
                drive_name=row['drive_name'],
                size=row['size'],
                disk_mark=safe_int(row['disk_mark']),
                type=row['type']
            ))

        
        HDD.objects.bulk_create(hdd_objects)
    print("HDD data loaded successfully!")

def run():
    print("Clearing existing data...")
    CPU.objects.all().delete()
    GPU.objects.all().delete()
    HDD.objects.all().delete()

    print("Importing new data...")
    import_cpu_data()
    import_gpu_data()
    import_hdd_data()

    print("All data loaded successfully!")

if __name__ == "__main__":
    run()
