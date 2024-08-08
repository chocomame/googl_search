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
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(search_goo_gl_urls, url.strip()): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url, goo_gl_urls, error = future.result()
            results.append({"URL": url, "goo.gl URLs": goo_gl_urls, "エラー": error})
    return results

st.title('複数サイト対応 goo.gl URL検索ツール')

urls = st.text_area('調査するウェブサイトのURLを1行に1つずつ入力してください:')

if st.button('検索'):
    if urls:
        urls_list = urls.split('\n')
        with st.spinner('検索中...'):
            results = process_urls(urls_list)
        
        df = pd.DataFrame(results)
        st.dataframe(df)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="結果をCSVでダウンロード",
            data=csv,
            file_name="goo_gl_search_results.csv",
            mime="text/csv",
        )
    else:
        st.warning('URLを少なくとも1つ入力してください。')