#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
スペースマーケット お気に入り収集ツール - Webアプリ版
"""

from flask import Flask, render_template, request, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
import json
from datetime import datetime
import threading

app = Flask(__name__)

# グローバル変数でステータスを管理
scraping_status = {
    'is_running': False,
    'progress': 0,
    'message': '待機中...',
    'total': 0,
    'current': 0,
    'error': None
}

class SpaceMarketScraper:
    """スペースマーケットのスクレイピングクラス"""
    
    def __init__(self, email, password, headless=False):
        self.email = email
        self.password = password
        self.headless = headless
        self.driver = None
        self.favorites = []
        
    def setup_driver(self):
        """Chromeドライバーのセットアップ"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        # 安定性向上のためのオプション
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280,900')
        
        # Mac ARM64用の修正
        try:
            # ChromeDriverを自動インストール
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.os_manager import ChromeType
            
            driver_path = ChromeDriverManager().install()
            
            # パスに 'chromedriver' という実行ファイルが含まれているか確認
            if 'THIRD_PARTY_NOTICES' in driver_path or not driver_path.endswith('chromedriver'):
                # 正しいchromedriverを探す
                import os
                driver_dir = os.path.dirname(driver_path)
                for file in os.listdir(driver_dir):
                    if file == 'chromedriver' and os.access(os.path.join(driver_dir, file), os.X_OK):
                        driver_path = os.path.join(driver_dir, file)
                        break
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
        except Exception as e:
            print(f"ChromeDriverの自動インストールに失敗: {e}")
            print("システムのChromeDriverを使用します...")
            # フォールバック: システムのchromedriver
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.implicitly_wait(10)
        
    def login(self):
        """スペースマーケットにログイン"""
        global scraping_status
        
        try:
            scraping_status['message'] = 'ログインページにアクセス中...'
            self.driver.get('https://www.spacemarket.com/login')
            time.sleep(2)
            
            scraping_status['message'] = 'ログイン情報を入力中...'
            
            # メールアドレス入力
            email_input = self.driver.find_element(By.NAME, 'email')
            email_input.clear()
            email_input.send_keys(self.email)
            
            # パスワード入力
            password_input = self.driver.find_element(By.NAME, 'password')
            password_input.clear()
            password_input.send_keys(self.password)
            
            scraping_status['message'] = 'ログインボタンをクリック中...'
            
            # ログインボタンをクリック
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
            login_button.click()
            
            # ログイン完了を待つ
            time.sleep(3)
            
            # ログイン成功を確認
            if 'login' in self.driver.current_url:
                raise Exception('ログインに失敗しました。メールアドレスとパスワードを確認してください。')
            
            scraping_status['message'] = 'ログイン成功！'
            return True
            
        except Exception as e:
            scraping_status['error'] = f'ログインエラー: {str(e)}'
            raise
    
    def navigate_to_favorites(self):
        """お気に入りページに移動"""
        global scraping_status
        
        try:
            scraping_status['message'] = 'お気に入りページに移動中...'
            
            # お気に入りページのURLを直接開く
            # 注: 実際のURLは要確認
            self.driver.get('https://www.spacemarket.com/dashboard/favorite_lists/')
            time.sleep(3)
            
            scraping_status['message'] = 'お気に入りページを読み込み中...'
            return True
            
        except Exception as e:
            scraping_status['error'] = f'ページ移動エラー: {str(e)}'
            raise
    
    def find_element_by_class_prefix(self, prefix):
        """クラス名のプレフィックスで要素を探す"""
        elements = self.driver.find_elements(By.XPATH, f'//*[starts-with(@class, "{prefix}")]')
        return elements[0] if elements else None
    
    def scrape_favorites(self):
        """お気に入りデータを収集"""
        global scraping_status
        
        try:
            scraping_status['message'] = 'データを収集中...'
            
            # MainContents を探す
            main_contents = self.find_element_by_class_prefix('MainContents_')
            
            if not main_contents:
                # フォールバック: 直接スペースリンクを探す
                scraping_status['message'] = 'お気に入りスペースを検出中...'
                return self.scrape_current_page()
            
            # お気に入りリストのリンクを取得
            favorite_links = main_contents.find_elements(By.CSS_SELECTOR, 'a[href*="/favorite_lists/"]')
            
            if not favorite_links:
                # 現在のページを直接スクレイプ
                return self.scrape_current_page()
            
            # 各お気に入りリストを処理
            for i, link in enumerate(favorite_links):
                scraping_status['current'] = i + 1
                scraping_status['total'] = len(favorite_links)
                scraping_status['message'] = f'お気に入りリスト {i+1}/{len(favorite_links)} を処理中...'
                
                list_url = link.get_attribute('href')
                self.driver.get(list_url)
                time.sleep(2)
                
                self.scrape_favorite_list_page()
            
            # 現在のページもスクレイプ
            if not self.favorites:
                self.scrape_current_page()
            
            return self.favorites
            
        except Exception as e:
            scraping_status['error'] = f'データ収集エラー: {str(e)}'
            raise
    
    def scrape_favorite_list_page(self):
        """お気に入り詳細ページをスクレイプ"""
        try:
            # FavoriteCardListItem 要素を全て取得
            cards = self.driver.find_elements(By.XPATH, '//*[contains(@class, "FavoriteCardListItem")]')
            
            scraping_status['message'] = f'{len(cards)}件のスペースを検出...'
            
            for card in cards:
                try:
                    # タイトル
                    title_elem = card.find_elements(By.XPATH, './/*[starts-with(@class, "FavoriteCardListItem__Title")]')
                    title = title_elem[0].text.strip() if title_elem else ''
                    
                    # レビュー点数
                    score_elem = card.find_elements(By.XPATH, './/*[starts-with(@class, "FavoriteCardListItem__ReputationScoreWrap")]')
                    score = score_elem[0].text.strip() if score_elem else ''
                    
                    # 金額
                    price_elem = card.find_elements(By.XPATH, './/*[starts-with(@class, "FavoriteCardListItem__Time")]')
                    price = price_elem[0].text.strip() if price_elem else ''
                    
                    # URL
                    link_elem = card.find_elements(By.CSS_SELECTOR, 'a[href*="/spaces/"]')
                    url = link_elem[0].get_attribute('href') if link_elem else ''
                    
                    # 画像URL
                    img_elem = card.find_elements(By.TAG_NAME, 'img')
                    image_url = img_elem[0].get_attribute('src') if img_elem else ''
                    
                    if title or url:
                        self.favorites.append({
                            'スペース名': title or 'タイトルなし',
                            '価格': price,
                            'レビュー点数': score,
                            '所在地': '',
                            'カテゴリ': '',
                            'URL': url,
                            '画像URL': image_url
                        })
                        
                except Exception as e:
                    print(f'カード処理エラー: {e}')
                    continue
                    
        except Exception as e:
            print(f'ページスクレイプエラー: {e}')
    
    def scrape_current_page(self):
        """現在のページを汎用的にスクレイプ（フォールバック）"""
        try:
            scraping_status['message'] = '汎用スクレイピングモードで収集中...'
            
            # スペースへのリンクを全て取得
            space_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/spaces/"]')
            
            scraping_status['total'] = len(space_links)
            processed_urls = set()
            
            for i, link in enumerate(space_links):
                scraping_status['current'] = i + 1
                scraping_status['progress'] = int((i + 1) / len(space_links) * 100)
                
                try:
                    url = link.get_attribute('href')
                    
                    if url in processed_urls:
                        continue
                    processed_urls.add(url)
                    
                    # 親要素を取得
                    parent = link
                    for _ in range(5):
                        parent = parent.find_element(By.XPATH, '..')
                    
                    # タイトルを取得
                    title = ''
                    for tag in ['h2', 'h3', 'h4']:
                        headings = parent.find_elements(By.TAG_NAME, tag)
                        for h in headings:
                            text = h.text.strip()
                            if text and len(text) > 3:
                                title = text
                                break
                        if title:
                            break
                    
                    # 価格を取得
                    price = ''
                    text_content = parent.text
                    import re
                    price_match = re.search(r'¥[\d,]+', text_content)
                    if price_match:
                        price = price_match.group(0)
                    
                    # 画像URL
                    image_url = ''
                    imgs = parent.find_elements(By.TAG_NAME, 'img')
                    if imgs:
                        image_url = imgs[0].get_attribute('src') or ''
                    
                    if title or url:
                        self.favorites.append({
                            'スペース名': title or 'タイトルなし',
                            '価格': price,
                            'レビュー点数': '',
                            '所在地': '',
                            'カテゴリ': '',
                            'URL': url,
                            '画像URL': image_url
                        })
                        
                except Exception as e:
                    continue
            
            return self.favorites
            
        except Exception as e:
            scraping_status['error'] = f'汎用スクレイピングエラー: {str(e)}'
            raise
    
    def save_to_excel(self, filename='spacemarket_favorites.xlsx'):
        """Excelファイルに保存"""
        global scraping_status
        
        try:
            scraping_status['message'] = 'Excelファイルを生成中...'
            
            if not self.favorites:
                raise Exception('収集されたデータがありません')
            
            df = pd.DataFrame(self.favorites)
            df.to_excel(filename, index=False, engine='openpyxl')
            
            scraping_status['message'] = f'{len(self.favorites)}件のデータを保存しました！'
            return filename
            
        except Exception as e:
            scraping_status['error'] = f'Excel保存エラー: {str(e)}'
            raise
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()

# Flaskルート
@app.route('/')
def index():
    """トップページ"""
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    """スクレイピング開始"""
    global scraping_status
    
    if scraping_status['is_running']:
        return jsonify({'error': '既に実行中です'}), 400
    
    data = request.json
    email = data.get('email')
    password = data.get('password')
    headless = data.get('headless', False)
    
    if not email or not password:
        return jsonify({'error': 'メールアドレスとパスワードを入力してください'}), 400
    
    # ステータスをリセット
    scraping_status = {
        'is_running': True,
        'progress': 0,
        'message': '準備中...',
        'total': 0,
        'current': 0,
        'error': None
    }
    
    # バックグラウンドでスクレイピングを実行
    thread = threading.Thread(target=run_scraping, args=(email, password, headless))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

def run_scraping(email, password, headless):
    """スクレイピング実行"""
    global scraping_status
    
    scraper = None
    try:
        scraper = SpaceMarketScraper(email, password, headless)
        
        # ドライバーセットアップ
        scraping_status['message'] = 'ブラウザを起動中...'
        scraper.setup_driver()
        
        # ログイン
        scraper.login()
        
        # お気に入りページに移動
        scraper.navigate_to_favorites()
        
        # データ収集
        scraper.scrape_favorites()
        
        # Excel保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'spacemarket_favorites_{timestamp}.xlsx'
        filepath = os.path.join('static', filename)
        scraper.save_to_excel(filepath)
        
        scraping_status['progress'] = 100
        scraping_status['message'] = '完了！ダウンロードボタンをクリックしてください。'
        scraping_status['download_url'] = f'/download/{filename}'
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['message'] = 'エラーが発生しました'
        
    finally:
        if scraper:
            scraper.close()
        scraping_status['is_running'] = False

@app.route('/api/status')
def get_status():
    """ステータス取得"""
    # ステータスが初期化されていない場合はデフォルト値を返す
    if not scraping_status:
        return jsonify({
            'is_running': False,
            'progress': 0,
            'message': '待機中...',
            'total': 0,
            'current': 0,
            'error': None
        })
    return jsonify(scraping_status)

@app.route('/download/<filename>')
def download_file(filename):
    """ファイルダウンロード"""
    filepath = os.path.join('static', filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return 'ファイルが見つかりません', 404

if __name__ == '__main__':
    # staticフォルダを作成
    os.makedirs('static', exist_ok=True)
    
    print('=' * 50)
    print('スペースマーケット お気に入り収集ツール')
    print('=' * 50)
    print('\nブラウザで以下のURLを開いてください:')
    print('http://localhost:8080')
    print('\n終了するには Ctrl+C を押してください')
    print('=' * 50)
    
    # Webサーバー起動
    app.run(debug=True, host='0.0.0.0', port=8080)