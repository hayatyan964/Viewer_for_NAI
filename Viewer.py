import flet as ft
from PIL import Image, PngImagePlugin
import os
import json
from io import BytesIO
import base64
import re
import hashlib
import tempfile

TAG_FILE = "tags.json"
IMG_DIR = "./images"

THUMBNAIL_SIZE = (64, 64)

#ファイル名変更
def sanitize_filename(prompt, ext=".png"):
    safe_prompt = re.sub(r"[^a-zA-Z0-9_\- ]+", "", prompt)
    safe_prompt = safe_prompt.strip().replace(" ", "_")
    if len(safe_prompt) > 30:
        safe_prompt = safe_prompt[:30]
    hash_part = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8]
    return f"{safe_prompt}_{hash_part}{ext}"

def extract_prompt_metadata(image_path):
    try:
        img = Image.open(image_path)
        if "Comment" in img.info:
            comment_data = json.loads(img.info["Comment"])
            return comment_data.get("prompt", "(no prompt)")
        else:
            return "(no metadata)"
    except Exception as e:
        return f"Error: {e}"


def generate_thumbnail_file(image_path):
    try:
        img = Image.open(image_path)
        img.thumbnail(THUMBNAIL_SIZE)
        temp_dir = tempfile.gettempdir()
        thumb_path = os.path.join(temp_dir, f"thumb_{os.path.basename(image_path)}")
        img.save(thumb_path, format="PNG")
        return thumb_path
    except Exception as e:
        print(f"サムネ生成エラー: {e}")
        return ""


def rename_images():
        renamed_count = 0
        for file in os.listdir(IMG_DIR):
            if file.lower().endswith(".png"):
                old_path = os.path.join(IMG_DIR, file)
                try:
                    prompt = extract_prompt_metadata(old_path)
                    new_name = sanitize_filename(prompt)
                    new_path = os.path.join(IMG_DIR, new_name)
                    if not os.path.exists(new_path):
                        os.rename(old_path, new_path)
                        renamed_count += 1
                    else:
                        print(f"重複スキップ: {new_name}")
                except Exception as e:
                    print(f"リネーム失敗: {file} -> {e}")
        return renamed_count

def main(page: ft.Page):
    rename_images()
    page.title = "画像ビューワ"
    page.scroll = True

    if not os.path.isdir(IMG_DIR):
        os.makedirs(IMG_DIR)

    selected_image = ft.Image(expand=True)
    metadata_text = ft.Text(value="メタデータ表示", selectable=True)
    prompt_filter_input = ft.TextField(label="プロンプトフィルタ", on_change=lambda e: refresh_image_list())
    image_grid = ft.GridView(expand=True, max_extent=100, child_aspect_ratio=1.0, spacing=5, run_spacing=10)

    

    def show_image(path):
        selected_image.src = path
        metadata_text.value = extract_prompt_metadata(path)
        page.update()

    

    def on_rename_click(e):
        count = rename_images()
        prompt_filter_input.value = ""
        refresh_image_list()
        metadata_text.value = f"{count} 件リネーム"
        page.update()
    
    def make_thumb_button(img_path):
        thumb_path = generate_thumbnail_file(img_path)
        thumb_image = ft.Image(
            src=thumb_path,
            width=THUMBNAIL_SIZE[0],
            height=THUMBNAIL_SIZE[1],
            fit=ft.ImageFit.COVER,
        )
        return ft.Container(
            content=thumb_image,
            on_click=lambda e: show_image(img_path),
            border_radius=ft.border_radius.all(8),
            ink=True,
            padding=5
        )


    def refresh_image_list():
        image_grid.controls.clear()
        keyword = prompt_filter_input.value.lower()
        for file in os.listdir(IMG_DIR):
            if file.lower().endswith(".png"):
                path = os.path.join(IMG_DIR, file)
                prompt = extract_prompt_metadata(path).lower()
                if keyword in prompt:
                    btn = make_thumb_button(path)
                    image_grid.controls.append(btn)
        page.update()

    refresh_image_list()

    page.add(
    ft.Column([
        ft.Row([
            prompt_filter_input,
            ft.ElevatedButton("ファイル名を修正", on_click=on_rename_click),
        ]),
        ft.Row([
            # folder_grid
        ])
        ft.Row([
            ft.Container(image_grid, expand=True, height=300)
        ]),
        ft.Row([
            selected_image,
            ft.Column([metadata_text], scroll=ft.ScrollMode.ALWAYS, expand=True)
        ])
    ])
)


ft.app(target=main)
