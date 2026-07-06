import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import glob
from PIL import Image
import logging

def select_folder():
    """フォルダ選択ダイアログを表示し、選択されたフォルダパスを返す"""
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを表示しない
    folder_path = filedialog.askdirectory(title="処理するフォルダを選択してください")
    return folder_path

def find_image_files(folder_path):
    """指定されたフォルダ内の画像ファイルを検索して一覧を返す"""
    if not folder_path:
        return []
    
    # Pillowでサポートされている主な画像形式
    image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif", "*.tiff", "*.webp"]
    
    # すべての画像ファイルを検索
    image_files = []
    for ext in image_extensions:
        pattern = os.path.join(folder_path, ext)
        image_files.extend(glob.glob(pattern))
    
    return image_files

def ensure_convert_directory(folder_path):
    """convertディレクトリを作成する（存在しない場合）"""
    convert_dir = os.path.join(folder_path, "convert")
    if not os.path.exists(convert_dir):
        try:
            os.makedirs(convert_dir)
            log_message(f"convertディレクトリを作成しました: {convert_dir}")
        except Exception as e:
            error_msg = f"エラー: convertディレクトリの作成中に問題が発生しました: {e}"
            log_message(error_msg)
            return None
    return convert_dir

def process_image_to_semitransparent(input_path, alpha_value=128, bg_color=(255, 255, 255)):
    """画像を半透明処理する
    
    Args:
        input_path: 入力画像のパス
        alpha_value: アルファ値（0=透明, 255=不透明）
        bg_color: 背景色（RGB値のタプル）
        
    Returns:
        処理された画像（PIL.Image）、またはエラー時にNone
    """
    try:
        # 画像を開いてRGBAモードに変換
        img = Image.open(input_path).convert("RGBA")
        
        # アルファチャンネルを設定
        img.putalpha(alpha_value)
        
        # 背景色を設定
        bg = Image.new("RGBA", img.size, (*bg_color, 255))
        
        # 合成
        combined = Image.alpha_composite(bg, img)
        
        return combined
    except Exception as e:
        log_message(f"画像処理中にエラーが発生しました: {e}")
        return None

def save_image_as_webp(image, original_path, output_dir):
    """処理した画像をWebP形式で保存する
    
    Args:
        image: 保存する画像（PIL.Image）
        original_path: 元の画像パス（ファイル名取得用）
        output_dir: 出力先ディレクトリ
        
    Returns:
        成功時はTrue、失敗時はFalse
    """
    try:
        # 元のファイル名を取得し、拡張子をwebpに変更
        filename = os.path.basename(original_path)
        basename = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{basename}.webp")
        
        # WebP形式で保存
        image.save(output_path, "WEBP")
        
        log_message(f"画像を保存しました: {output_path}")
        return True
    except Exception as e:
        log_message(f"画像保存中にエラーが発生しました: {e}")
        return False


def setup_logging():
    """ログ設定を初期化する"""
    # ログファイルの設定
    logging.basicConfig(
        filename='alpha-setter.log',
        filemode='w',  # 上書きモード
        level=logging.INFO,
        format='%(message)s',  # タイムスタンプなし
        encoding='utf-8'  # UTF-8エンコーディング
    )

def log_message(message):
    """コンソールとログファイルの両方にメッセージを出力する"""
    print(message)
    logging.info(message)

def main():
    # ログ設定を初期化
    setup_logging()
    
    # フォルダ選択ダイアログを表示
    folder_path = select_folder()
    
    if not folder_path:
        # フォルダが選択されていない場合は処理を終了
        log_message("フォルダが選択されていません。")
        return
        
    # 画像ファイルを検索
    image_files = find_image_files(folder_path)
    
    if not image_files:
        messagebox.showinfo("情報", "画像ファイルが見つかりませんでした。")
        return
    
    log_message(f"{len(image_files)}個の画像ファイルが見つかりました。")
            
    # 背景色を選択
    bg_color = (255, 255, 255)  # デフォルトは白
    
    bg_choice = messagebox.askyesno(
        "背景色選択", 
        "背景色は白でよろしいですか？\n\nはい = 白, いいえ = 黒"
    )
        
    # 透明度を調整するか確認ダイアログを表示
    alpha_input = simpledialog.askstring(
        "透明度設定", 
        "透明度を設定してください。\n\n0 = 透明, 255 = 不透明", 
        initialvalue="128"
    )
    
    if bg_choice:
        bg_color = (255, 255, 255)  # 白
    else:
        bg_color = (0, 0, 0)  # 黒
    
    # 入力値をチェック
    alpha_value = 128  # デフォルト値
    if alpha_input:
        try:
            alpha_value = int(alpha_input)
            if alpha_value < 0 or alpha_value > 255:
                messagebox.showwarning("警告", "透明度は0～255の範囲で指定してください。\n128を使用します。")
                alpha_value = 128
        except ValueError:
            messagebox.showwarning("警告", "有効な数値ではありません。128を使用します。")
            alpha_value = 128
    
    # convertフォルダを作成
    convert_dir = ensure_convert_directory(folder_path)
    if not convert_dir:
        messagebox.showerror("エラー", "convertフォルダの作成に失敗しました。")
        return
    
    # 画像を処理して保存
    success_count = 0
    error_count = 0
    
    for file_path in image_files:
        # 画像を半透明処理（背景色を指定）
        processed_img = process_image_to_semitransparent(file_path, alpha_value, bg_color)
        if processed_img:
            # WebP形式で保存
            if save_image_as_webp(processed_img, file_path, convert_dir):
                success_count += 1
            else:
                error_count += 1
        else:
            error_count += 1
    
    # 処理結果を表示
    result_message = f"処理が完了しました。\n\n成功: {success_count}件\n失敗: {error_count}件"
    log_message(result_message)
    messagebox.showinfo("情報", result_message)

if __name__ == "__main__":
    main()
