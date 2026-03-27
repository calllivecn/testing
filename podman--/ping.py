
import podman

with podman.PodmanClient() as client:
    if client.ping():
        images = client.images.list()
        for image in images:
            print(f"{image=}")
