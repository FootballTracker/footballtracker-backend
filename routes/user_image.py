from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/user", tags=["User Image"])

image_directory = Path("images/")
image_directory.mkdir(parents=True, exist_ok=True)


def image_exists(name: str):
    extensions = ["png", "jpg", "jpeg", "gif", "bmp", "webp"]

    for ext in extensions:
        if (image_directory / f"{name}.{ext}").is_file():
            return ext

    return None


def remove_image(name_with_ext: str):
    try:
        (image_directory / name_with_ext).unlink()
    except OSError as e:
        print(f"Erro ao remover imagem {name_with_ext}: {e}")
    return


@router.get("/{user_id}/has_image")
async def user_has_image(user_id: int):
    return bool(image_exists(str(user_id)))


@router.get("/{user_id}/image")
async def get_user_image(user_id: int):
    ext = image_exists(str(user_id))

    if ext:
        file_path = image_directory / f"{user_id}.{ext}"
        return FileResponse(
            path=file_path, media_type=f"image/{ext}", filename=f"user_image.{ext}"
        )

    raise HTTPException(status_code=404, detail="Imagem não encontrada")


@router.post("/image")
async def upload_user_image(user_id: int = Form(...), image: UploadFile = File(...)):
    contents = await image.read()
    size = len(contents)

    if size > 2.5 * 10**6:
        raise HTTPException(
            status_code=413, detail="Imagem maior do que o limite de 2.5MB"
        )

    filename_without_ext = str(user_id)
    file_ext = image.content_type.split("/")[-1]

    existing_ext = image_exists(filename_without_ext)
    if existing_ext:
        remove_image(f"{filename_without_ext}.{existing_ext}")

    new_file_path = image_directory / f"{filename_without_ext}.{file_ext}"
    with open(new_file_path, "wb") as f:
        f.write(contents)

    return {
        "filename": new_file_path.name,
        "content_type": image.content_type,
        "size": size,
        "message": "Imagem alterada com sucesso",
    }


@router.delete("/image")
async def delete_user_image(user_id: int):
    ext = image_exists(str(user_id))

    if ext:
        remove_image(f"{user_id}.{ext}")
        return {"message": "Imagem removida com sucesso"}

    raise HTTPException(
        status_code=404, detail="Nenhuma imagem para remover foi encontrada"
    )
