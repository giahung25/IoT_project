import os
import sys
import urllib.request
import json

def download_file(url, filepath):
    print(f"Downloading {url} -> {filepath}")
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    urllib.request.install_opener(opener)
    
    # Simple chunked downloader to show progress
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
        meta = response.info()
        file_size = int(meta.get("Content-Length", 0))
        print(f"Size: {file_size / (1024*1024):.2f} MB")
        
        chunk_size = 1024 * 1024
        downloaded = 0
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            print(f"\rProgress: {downloaded / (1024*1024):.2f} MB / {file_size / (1024*1024):.2f} MB ({downloaded/file_size*100:.1f}%)", end="", flush=True)
    print("\nDownload complete.")

def main():
    base_dir = "ollama_model"
    blobs_dir = os.path.join(base_dir, "blobs")
    manifest_dir = os.path.join(base_dir, "manifests", "registry.ollama.ai", "library", "moondream")
    
    os.makedirs(blobs_dir, exist_ok=True)
    os.makedirs(manifest_dir, exist_ok=True)
    
    # Manifest JSON data we retrieved
    manifest_data = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "digest": "sha256:ba5fbb481ada654c85475473fa862b81eb5539cecc56da57f90ef5af56798be2",
            "size": 562
        },
        "layers": [
            {"mediaType": "application/vnd.ollama.image.model", "digest": "sha256:e554c6b9de016673fd2c732e0342967727e9659ca5f853a4947cc96263fa602b", "size": 828661152},
            {"mediaType": "application/vnd.ollama.image.projector", "digest": "sha256:4cc1cb3660d87ff56432ebeb7884ad35d67c48c7b9f6b2856f305e39c38eed8f", "size": 909777984},
            {"mediaType": "application/vnd.ollama.image.license", "digest": "sha256:c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4", "size": 11357},
            {"mediaType": "application/vnd.ollama.image.template", "digest": "sha256:4b021a3b4b4a58b06921bdf163d1b61e78b74d7df434a7f735edfdc807e68377", "size": 77},
            {"mediaType": "application/vnd.ollama.image.params", "digest": "sha256:9468773bdc1f9908492a3cdaab70bf5ac0a45d2d52717e8208c0deece2765262", "size": 65}
        ]
    }
    
    # Save manifest
    manifest_path = os.path.join(manifest_dir, "latest")
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)
    print(f"Saved manifest to {manifest_path}")
    
    # Blobs to download
    blobs = [
        "sha256:ba5fbb481ada654c85475473fa862b81eb5539cecc56da57f90ef5af56798be2",
        "sha256:e554c6b9de016673fd2c732e0342967727e9659ca5f853a4947cc96263fa602b",
        "sha256:4cc1cb3660d87ff56432ebeb7884ad35d67c48c7b9f6b2856f305e39c38eed8f",
        "sha256:c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
        "sha256:4b021a3b4b4a58b06921bdf163d1b61e78b74d7df434a7f735edfdc807e68377",
        "sha256:9468773bdc1f9908492a3cdaab70bf5ac0a45d2d52717e8208c0deece2765262"
    ]
    
    for blob in blobs:
        digest_part = blob.split(":")[1]
        filename = f"sha256-{digest_part}"
        filepath = os.path.join(blobs_dir, filename)
        
        # Check if already exists and size matches
        expected_size = 562
        if blob == manifest_data["config"]["digest"]:
            expected_size = manifest_data["config"]["size"]
        else:
            for layer in manifest_data["layers"]:
                if layer["digest"] == blob:
                    expected_size = layer["size"]
                    break
        
        if os.path.exists(filepath) and os.path.getsize(filepath) == expected_size:
            print(f"Blob {filename} already downloaded and verified.")
            continue
            
        url = f"https://registry.ollama.ai/v2/library/moondream/blobs/{blob}"
        try:
            download_file(url, filepath)
        except Exception as e:
            print(f"Error downloading {blob}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
