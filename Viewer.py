import flet as ft
from PIL import Image
import os
import json

TAG_FILE = "tags.json"
# 画像ディレクトリ
IMG_DIR = "./images"

def main(page: ft.Page):
    page.title = "ビューワ"
    page.scroll = True

    # ディレクトリ無かったら生成
    if os.path.isdir(IMG_DIR):
        pass
    else:
        os.makedirs(IMG_DIR)
    
    # 画像選択とリスト
    selected_image = ft.Image()
    image_list = ft.Column(scroll = ft.ScrollMode.ALWAYS)

    # 画像表示
    def show_image(path):
        selected_image.src = path
        page.update()

    for file in os.listdir(IMG_DIR):
        if file.lower().endswith((".png")):
            path = os.path.join(IMG_DIR, file)
            btn = ft.TextButton(text = file, on_click = lambda e, p=path:show_image(p))
            image_list.controls.append(btn)

    page.add(
        ft.Column([
            image_list,
            ft.Row([
                selected_image,
                # metadata_tag,
            ])

        ])
    )

ft.app(target=main)
