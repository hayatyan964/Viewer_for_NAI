import flet as ft
from PIL import Image, PngImagePlugin
import os
import json
import re
import hashlib
import tempfile
import json

# 後で基本はdefaultconfig userconfigがあればそっちを開くようにする
'''
if os.path.exists("./userconfig"):
    f_in = open ('./userconfig.json')
else:
    f_in = open('./defaultconfig.json')
data = json.load(f_in)
'''

image_paths = [] # 前後ボタン用画像パス
current_index = -1 # 前後ボタン用現在位置

if os.path.exists("./defaultconfig.json"):
    f_in = open('./defaultconfig.json')
    data = json.load(f_in)

IMG_DIR = data["IMG_DIR"]
THUMBNAIL_SIZE = (data["THUMBNAIL_WIDTH"], data["THUMBNAIL_HEIGHT"])

# 初期画像ディレクトリ作成
if not os.path.exists(IMG_DIR) and IMG_DIR == "./images":
    os.makedirs(IMG_DIR)

# メタデータ全取得
def extract_metadata(image_path):
    try:
        img = Image.open(image_path)
        if "Comment" in img.info:
            return json.loads(img.info["Comment"])
        else:
            return {}
    except Exception as e:
        print(f"メタデータ読み込み失敗: {e}")
        return {}

# メタデータ整形
def format_metadata(metadata):
    if not metadata:
        return "(no metadata)"

    lines = []

    # 基本パラメータ
    lines.append(f" Size: {metadata.get('width')} x {metadata.get('height')}")
    lines.append(f" Steps: {metadata.get('steps')}, Scale: {metadata.get('scale')}, Sampler: {metadata.get('sampler')}")

    # プロンプト
    prompt = metadata.get("prompt", "(no prompt)")
    lines.append(f"\n Prompt:\n{prompt}")
    # ネガティブプロンプト
    negative_prompt = metadata.get("v4_negative_prompt", {}).get("caption", {}).get("base_caption", [])
    lines.append(f"\n NegativePrompt:\n{negative_prompt}")

    # キャラクタープロンプト
    char_info = metadata.get("v4_prompt", {}).get("caption", {}).get("char_captions", [])
    for i, char in enumerate(char_info):
        caption = char.get("char_caption", "")
        lines.append(f"\n Character {i+1}:\n{caption.strip()}")

    return "\n".join(lines)

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


def main(page: ft.Page):

    page.title = "画像ビューワ"
    page.scroll = True

    selected_image = ft.Image(
    expand=True,
    fit=ft.ImageFit.CONTAIN  # 縦横比を保って収める
    )
    
    # 表示エリアに制限をつけて中央寄せ
    image_display_area = ft.Container(
        content=selected_image,
        #alignment=ft.alignment.center,
        expand=True,
        height=500,  # 高さはお好みで調整してね～
    )

    # 前後ボタン
    def on_prev_click(e):
        global current_index
        if current_index > 0:
            current_index -= 1
            show_image(image_paths[current_index])

    def on_next_click(e):
        global current_index
        if current_index < len(image_paths) - 1:
            current_index += 1
            show_image(image_paths[current_index])
    
    navigation_prev = ft.ElevatedButton("← 前へ", on_click=on_prev_click)
    navigation_next = ft.ElevatedButton("次へ →", on_click=on_next_click)

    metadata_text = ft.Text(value="メタデータ表示", selectable=True)
    prompt_filter_input = ft.TextField(label="プロンプトフィルタ", on_change=lambda e: refresh_image_list())
    image_grid = ft.GridView(expand=True, max_extent=100, child_aspect_ratio=1.0, spacing=5, run_spacing=10)

    search_mode_dropdown = ft.Dropdown(
        label="検索モード",
        options=[
            ft.dropdown.Option("prompt", "プロンプト"),
            ft.dropdown.Option("negative", "ネガティブプロンプト"),
        ],
        value="prompt",  # デフォルト
        on_change=lambda e: refresh_image_list()
    )





    # 画像フォルダ変更
    def file_picker_result(e: ft.FilePickerResultEvent):
        global IMG_DIR
        if e.path:
            IMG_DIR = e.path
            print(f"画像フォルダ変更: {IMG_DIR}")
            # rename_images()
            refresh_image_list()
        page.update()


    file_picker = ft.FilePicker(on_result=file_picker_result)
    page.overlay.append(file_picker)

    # 画像表示
    def show_image(path):
        selected_image.src = path
        metadata = extract_metadata(path)
        metadata_text.value = format_metadata(metadata)
        page.update()
    
    # クリック可能サムネ表示
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

    # 画像リスト再読み込み
    def refresh_image_list():
        image_grid.controls.clear()
        keyword = prompt_filter_input.value.lower()
        mode = search_mode_dropdown.value
        global image_paths, current_index

        image_paths = []

        for root, dirs, files in os.walk(IMG_DIR):
            for file in sorted(files):  # 並び順安定させる
                if file.lower().endswith(".png"):
                    path = os.path.join(root, file)
                    metadata = extract_metadata(path)
                    # プロンプトフィルタ
                    if mode == "prompt":
                        base_caption = metadata.get("v4_prompt", {}).get("caption", {}).get("base_caption", [])
                        target_text = " ".join(base_caption).lower() if isinstance(base_caption, list) else str(base_caption).lower()
                    elif mode == "negative":
                        neg_caption = metadata.get("v4_negative_prompt", {}).get("caption", {}).get("base_caption", [])
                        target_text = " ".join(neg_caption).lower() if isinstance(neg_caption, list) else str(neg_caption).lower()
                    else:
                        target_text = ""
                    # 前後ボタン
                    if keyword in target_text: 
                        image_paths.append(path)
                        btn = make_thumb_button(path)
                        image_grid.controls.append(btn)

        if image_paths:
            show_image(image_paths[0])  # 最初の画像を表示
            current_index = 0
        else:
            selected_image.src = ""
            metadata_text.value = "(画像なし)"
            current_index = -1

    page.update()


    def on_prompt_filter_change(e):
        refresh_image_list()
        page.update()

    
    refresh_image_list()
    prompt_filter_input = ft.TextField(label="プロンプトフィルタ", on_change=on_prompt_filter_change)
    
    page.update()



    page.add(
    ft.Column([
        ft.Row([
            prompt_filter_input,
            search_mode_dropdown,
            ft.ElevatedButton(
                    "画像フォルダ変更",
                    icon=ft.icons.FILE_OPEN,
                    on_click=lambda _: file_picker.get_directory_path(),
                ),
        ]),
        ft.Row([
            ft.Container(image_grid, expand = True, height = 300)
        ]),
        ft.Row([
            navigation_prev,
            image_display_area,
            navigation_next,
            ft.Column([metadata_text], scroll = ft.ScrollMode.ALWAYS, expand = True)
        ]),
        ]),
    )

ft.app(target=main)
