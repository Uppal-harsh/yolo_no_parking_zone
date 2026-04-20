import os
import xml.etree.ElementTree as ET
import shutil
import random
from tqdm import tqdm

def convert_voc_to_yolo(xml_path, output_txt_path, class_id=0):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)
    
    if w == 0 or h == 0:
        return False
    
    with open(output_txt_path, 'w') as f:
        for obj in root.findall('object'):
            # We treat all objects as the license plate class
            xmlbox = obj.find('bndbox')
            b = (float(xmlbox.find('xmin').text), float(xmlbox.find('xmax').text), 
                 float(xmlbox.find('ymin').text), float(xmlbox.find('ymax').text))
            
            # Normalize
            x_center = (b[0] + b[1]) / 2.0 / w
            y_center = (b[2] + b[3]) / 2.0 / h
            width = (b[1] - b[0]) / w
            height = (b[3] - b[2]) / h
            
            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
    return True

def prepare_dataset(source_dir, target_dir, split_ratio=0.8):
    os.makedirs(os.path.join(target_dir, 'train/images'), exist_ok=True)
    os.makedirs(os.path.join(target_dir, 'train/labels'), exist_ok=True)
    os.makedirs(os.path.join(target_dir, 'valid/images'), exist_ok=True)
    os.makedirs(os.path.join(target_dir, 'valid/labels'), exist_ok=True)
    
    files = [f for f in os.listdir(source_dir) if f.endswith('.xml')]
    random.shuffle(files)
    
    split_idx = int(len(files) * split_ratio)
    train_files = files[:split_idx]
    valid_files = files[split_idx:]
    
    def process_files(file_list, subset):
        for xml_file in tqdm(file_list, desc=f"Processing {subset}"):
            xml_path = os.path.join(source_dir, xml_file)
            
            # Find corresponding image
            image_file = None
            for ext in ['.jpg', '.png', '.jpeg']:
                temp_img = xml_file.replace('.xml', ext)
                if os.path.exists(os.path.join(source_dir, temp_img)):
                    image_file = temp_img
                    break
            
            if image_file:
                txt_file = xml_file.replace('.xml', '.txt')
                txt_path = os.path.join(target_dir, subset, 'labels', txt_file)
                
                if convert_voc_to_yolo(xml_path, txt_path):
                    shutil.copy(os.path.join(source_dir, image_file), 
                                os.path.join(target_dir, subset, 'images', image_file))

    process_files(train_files, 'train')
    process_files(valid_files, 'valid')

if __name__ == "__main__":
    source = "video_images"
    target = "dataset"
    if os.path.exists(target):
        shutil.rmtree(target)
    prepare_dataset(source, target)
    print("Dataset prepared successfully.")

    # Create data.yaml
    yaml_content = f"""path: {os.path.abspath(target)}
train: train/images
val: valid/images

names:
  0: license_plate
"""
    with open('data.yaml', 'w') as f:
        f.write(yaml_content)
    print("data.yaml created.")
