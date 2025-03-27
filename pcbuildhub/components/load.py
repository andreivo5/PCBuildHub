import csv
from pathlib import Path
from .models import CPU, GPU, Case, Cooler, RAM, Motherboard, PSU, Storage

base_dir = Path(__file__).resolve().parent

CPU_CSV_PATH = base_dir / 'data' / 'CPU.csv'
GPU_CSV_PATH = base_dir / 'data' / 'GPU.csv'
CASE_CSV_PATH = base_dir / 'data' / 'Case.csv'
COOLER_CSV_PATH = base_dir / 'data' / 'Cooler.csv'
RAM_CSV_PATH = base_dir / 'data' / 'Memory.csv'
MOTHERBOARD_CSV_PATH = base_dir / 'data' / 'Motherboard.csv'
PSU_CSV_PATH = base_dir / 'data' / 'PSU.csv'
STORAGE_CSV_PATH = base_dir / 'data' / 'Storage.csv'


def import_cpu_data():
    with open(CPU_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        cpu_objects = []

        for row in reader:
            cpu_objects.append(CPU(
                name=row['name'],
                image=row['image'],
                url=row['url'],
                brand=row['brand'],
                socket=row['socket'],
                speed=float(row['speed']) if row['speed'] else None,
                core_count=int(row['coreCount']),
                thread_count=int(row['threadCount']),
                series=row['series'],
                model=row['model'],
                cpu_mark=int(row['cpu_mark']) if row['cpu_mark'] else None,
                thread_mark=int(row['thread_mark']) if row['thread_mark'] else None,
                tdp=int(row['tdp']) if row['tdp'] else None
            ))
        CPU.objects.bulk_create(cpu_objects)
    print("CPU data loaded successfully!")


def import_gpu_data():
    with open(GPU_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        gpu_objects = []

        for row in reader:
            gpu_objects.append(GPU(
                name=row['name'],
                image=row['image'],
                url=row['url'],
                brand=row['brand'],
                vram=int(row['VRAM']),
                resolution=row['resolution'],
                model=row['model'],
                vram_gb=int(row['vram_gb']),
                g3d_mark=float(row['g3d_mark']) if row['g3d_mark'] else None,
                g2d_mark=float(row['g2d_mark']) if row['g2d_mark'] else None,
                tdp=int(row['tdp']) if row['tdp'] else None
            ))
        GPU.objects.bulk_create(gpu_objects)
    print("GPU data loaded successfully!")


def import_case_data():
    with open(CASE_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        case_objects = [Case(name=row['name'], image=row['image'], url=row['url'], size=row['size']) for row in reader]
        Case.objects.bulk_create(case_objects)
    print("Case data loaded successfully!")


def import_cooler_data():
    with open(COOLER_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        cooler_objects = [Cooler(name=row['name'], image=row['image'], url=row['url'], type=row['type']) for row in reader]
        Cooler.objects.bulk_create(cooler_objects)
    print("Cooler data loaded successfully!")


def import_ram_data():
    with open(RAM_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        ram_objects = [RAM(name=row['name'], image=row['image'], url=row['url'], type=row['type'], size=int(row['size'])) for row in reader]
        RAM.objects.bulk_create(ram_objects)
    print("RAM data loaded successfully!")


def import_motherboard_data():
    with open(MOTHERBOARD_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        motherboard_objects = [
            Motherboard(name=row['name'], image=row['image'], url=row['url'], brand=row['brand'], socket=row['socket'], size=row['size'])
            for row in reader
        ]
        Motherboard.objects.bulk_create(motherboard_objects)
    print("Motherboard data loaded successfully!")


def import_psu_data():
    with open(PSU_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        psu_objects = [PSU(name=row['name'], image=row['image'], url=row['url'], power=int(row['power']), size=row['size']) for row in reader]
        PSU.objects.bulk_create(psu_objects)
    print("PSU data loaded successfully!")


def import_storage_data():
    with open(STORAGE_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        storage_objects = [Storage(name=row['name'], image=row['image'], url=row['url'], type=row['type'], space=int(row['space'])) for row in reader]
        Storage.objects.bulk_create(storage_objects)
    print("Storage data loaded successfully!")


def run():
    print("Clearing existing data...")
    CPU.objects.all().delete()
    GPU.objects.all().delete()
    Case.objects.all().delete()
    Cooler.objects.all().delete()
    RAM.objects.all().delete()
    Motherboard.objects.all().delete()
    PSU.objects.all().delete()
    Storage.objects.all().delete()

    print("Importing new data...")
    import_cpu_data()
    import_gpu_data()
    import_case_data()
    import_cooler_data()
    import_ram_data()
    import_motherboard_data()
    import_psu_data()
    import_storage_data()

    print("All data loaded successfully!")


if __name__ == "__main__":
    run()