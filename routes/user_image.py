from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/user", tags=["User Image"])
image_directory = Path('images/')

def image_exists(name: str):
    extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']

    for ext in extensions:
        if (image_directory / f'{name}.{ext}').is_file():
            return ext
        
    return False


def remove_image(name: str):
    (image_directory / f'{name}').unlink()
    return

@router.get("/{user_id}/has_image")
async def user_has_image(user_id: int):
    return bool(image_exists(f"{user_id}"))
        

@router.get("/{user_id}/image")
async def get_user_image(user_id: int):
    ext = image_exists(f'{user_id}')
    
    if ext:
        return FileResponse(f"{image_directory}/{user_id}.{ext}", media_type=f'image/{ext}', filename=f'user_image.{ext}')
    
    raise HTTPException(status_code=404, detail="Imagem não encontrada")


@router.post("/image")
async def upload_user_image(user_id: int = Form(...), image: UploadFile = File(...)):

    # Image data
    file_type = f'{image.content_type.split('/')[-1]}'
    filename = f'{user_id}'
    size = len(await image.read())

    if(size > 25e5):
        raise HTTPException(status_code=400, detail="Imagem maior do que o limite de 2.5MB")

    ext = image_exists(filename)

    if ext:
        remove_image(f'{filename}.{ext}')

    # Save image
    file_path = f"{image_directory}/{filename}.{file_type}"
    with open(file_path, "wb") as f:
        await image.seek(0)
        f.write(await image.read())

    return {"filename": filename, "content_type": file_type, "size": size, "message": "Imagem alterada com sucesso"}


@router.delete("/image")
async def delete_user_image(user_id: int):

    ext = image_exists(f'{user_id}')

    if ext:
        remove_image(f'{user_id}.{ext}')

    return {"message": "Imagem removida com sucesso"}