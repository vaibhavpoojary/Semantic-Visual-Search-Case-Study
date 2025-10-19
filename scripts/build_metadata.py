import os, json

def build_metadata(image_dir="data/images", output_path="data/metadata.json"):
    files = sorted([
        f for f in os.listdir(image_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])
    metadata = []
    for i, f in enumerate(files):
        metadata.append({
            "id": i + 1,
            "filename": f,
            "path": os.path.join(image_dir, f)
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata created for {len(metadata)} images at {output_path}")

if __name__ == "__main__":
    build_metadata()
