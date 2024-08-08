import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import pandas as pd
import concurrent.futures

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def search_goo_gl_urls(url):
    if not is_valid_url(url):
        return url, [], "無効なURL"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return url, [], f"エラー: {str(e)}"
    soup = BeautifulSoup(response.text, 'html.parser')
    
    goo_gl_pattern = re.compile(r'https://goo\.gl/\S+')
    goo_gl_urls = goo_gl_pattern.findall(str(soup))
    
    return url, list(set(goo_gl_urls)), None

def process_urls(urls):
    results = []
    for url in urls:
        url = url.strip()
        try:
            result_url, goo_gl_urls, error = search_goo_gl_urls(url)
            results.append({"URL": result_url, "goo.gl URLs": ', '.join(goo_gl_urls) if goo_gl_urls else '', "エラー": error or ''})
        except Exception as e:
            results.append({"URL": url, "goo.gl URLs": '', "エラー": f"予期せぬエラー: {str(e)}"})
    return results

st.title('複数サイト対応 goo.gl 検索ツール')
st.markdown('ver1.02：ユーザーが入力した並び順通りに出力されるように修正')
urls = st.text_area('調査するウェブサイトのURLを1行に1つずつ入力してください:')

if st.button('検索'):
    if urls:
        urls_list = [url.strip() for url in urls.split('\n') if url.strip()]
        with st.spinner('検索中...'):
            results = process_urls(urls_list)
        
        df = pd.DataFrame(results)
        
        # データフレームの表示をカスタマイズ
        st.dataframe(
            df.style.apply(lambda x: ['background-color: #ffcccc' if x['エラー'] else '' for i in x], axis=1)
        )
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="結果をCSVでダウンロード",
            data=csv,
            file_name="goo_gl_search_results.csv",
            mime="text/csv",
        )
    else:
        st.warning('URLを少なくとも1つ入力してください。')